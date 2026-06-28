"""Load a run-set of completed reviews by scanning ``eval/reviews/<name>/``.

Generation writes artifacts under ``eval/reviews/<run-set>/<config__paper>/``.
Metric scripts discover those runs here; results go to ``eval/results/<run-set>/``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from utils.spec import (
    REQUIRED_ARTIFACTS,
    ROLES,
    Config,
    derive_homogeneous,
    is_run_complete,
    parse_run_dir_name,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = PROJECT_ROOT / "dataset" / "eval_sample_30.json"


@dataclass(frozen=True)
class RunRecord:
    """One completed (config, paper) run and its on-disk artifact directory."""

    config_id: str
    paper_id: str
    run_dir: Path


class RunArtifacts:
    """Resolved paths and dataset fields for one completed (config, paper) run."""

    def __init__(self, run: RunRecord, paper: dict[str, Any]) -> None:
        self.run = run
        self.paper = paper

    def final_review(self) -> str:
        """Read the leader's full markdown review from the run directory."""
        return (self.run.run_dir / "final_review.md").read_text(encoding="utf-8")

    def review_rating(self) -> float:
        """Read the parsed 1–10 overall score from ``review.json`` (P2)."""
        path = self.run.run_dir / "review.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        rating = data.get("rating")
        if rating is None:
            raise ValueError(f"missing rating in {path}")
        return float(rating)

    def _parse_trace_roles(self) -> tuple[dict[str, str], dict[str, str]]:
        """Parse ``trace.jsonl`` once into role-label and delegation-output maps.

        Returns ``(role_labels, outputs_by_label)`` where ``role_labels`` maps
        each role key from ``run_header.roles`` to its display label, and
        ``outputs_by_label`` maps an expert label to the ``output`` of its
        ``delegation_finished`` record. A single-agent run (leader emits a
        review without delegating) yields an empty ``outputs_by_label``.
        """
        trace_path = self.run.run_dir / "trace.jsonl"
        role_labels: dict[str, str] = {}
        outputs_by_label: dict[str, str] = {}

        for line in trace_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            rtype = record.get("type")
            if rtype == "run_header":
                role_labels = record.get("roles", {})
            elif rtype == "delegation_finished":
                label = record.get("expert_role", "")
                if label:
                    outputs_by_label[label] = record.get("output", "")

        return role_labels, outputs_by_label

    def role_output(self, role: str) -> str:
        """Read the full text output of a reviewer role from this run (P1).

        For ``leader`` returns ``final_review.md`` (always persisted untruncated).
        For expert roles (``clarity``, ``experiments``, ``impact``) parses
        ``trace.jsonl``: uses ``run_header.roles`` to map the role key to its
        label, then returns the ``output`` field of the matching
        ``delegation_finished`` record.
        """
        if role == "leader":
            return self.final_review()

        role_labels, outputs_by_label = self._parse_trace_roles()
        label = role_labels.get(role)
        if label is None:
            raise KeyError(
                f"role {role!r} not found in run_header.roles for run {self.run.run_dir}"
            )
        if label not in outputs_by_label:
            raise KeyError(
                f"no delegation_finished record for role {role!r} "
                f"(label={label!r}) in {self.run.run_dir / 'trace.jsonl'}"
            )
        return outputs_by_label[label]

    def has_role_output(self, role: str) -> bool:
        """Whether this run produced an output for ``role`` without raising (P1).

        ``leader`` is always available (``final_review.md`` is a required
        artifact). Expert roles are available only when the leader actually
        delegated to them; single-agent runs that skipped delegation (e.g. a
        llama leader that never calls a tool) return ``False``.
        """
        if role == "leader":
            return True
        role_labels, outputs_by_label = self._parse_trace_roles()
        label = role_labels.get(role)
        return label is not None and label in outputs_by_label


class RunSet:
    """Named set of completed review runs under ``eval/reviews/<name>/``.

    Holds config assignments derived from trace headers, completed runs, and the
    paper dataset metrics join against.
    """

    def __init__(
        self,
        name: str,
        results_dir: Path,
        configs: dict[str, Config],
        runs: list[RunRecord],
        papers: dict[str, dict[str, Any]],
    ) -> None:
        self.name = name
        self.results_dir = results_dir
        self.configs = configs
        self.runs = runs
        self.papers = papers

    @classmethod
    def load(
        cls,
        name: str,
        *,
        root: Path | None = None,
        dataset_path: Path | None = None,
        validate_artifacts: bool = True,
    ) -> RunSet:
        """Scan ``eval/reviews/<name>/`` for complete runs and load the dataset."""
        project_root = root or PROJECT_ROOT
        reviews_dir = project_root / "eval" / "reviews" / name
        results_dir = project_root / "eval" / "results" / name
        papers = load_papers(dataset_path or DEFAULT_DATASET)

        if not reviews_dir.is_dir():
            raise FileNotFoundError(f"missing reviews directory: {reviews_dir}")

        configs: dict[str, Config] = {}
        runs: list[RunRecord] = []

        for entry in sorted(reviews_dir.iterdir()):
            if not entry.is_dir():
                continue
            if not is_run_complete(entry):
                continue

            config_id, paper_id = parse_run_dir_name(entry.name)
            models = _models_from_trace(entry)

            if config_id in configs:
                if configs[config_id].models != models:
                    raise ValueError(
                        f"inconsistent models for config {config_id!r} across runs in {reviews_dir}"
                    )
            else:
                configs[config_id] = Config(
                    config_id=config_id,
                    models=models,
                    homogeneous=derive_homogeneous(models),
                )

            runs.append(
                RunRecord(
                    config_id=config_id,
                    paper_id=paper_id,
                    run_dir=entry.resolve(),
                )
            )

        if not runs:
            raise ValueError(f"no complete runs found in {reviews_dir}")

        run_set = cls(name, results_dir, configs, runs, papers)
        if validate_artifacts:
            _validate_artifacts(run_set)
        return run_set

    def runs_by_config_paper(self) -> dict[tuple[str, str], RunRecord]:
        """Index runs by ``(config_id, paper_id)``."""
        index: dict[tuple[str, str], RunRecord] = {}
        for run in self.runs:
            key = (run.config_id, run.paper_id)
            if key in index:
                raise ValueError(
                    f"duplicate run for config={run.config_id!r} paper={run.paper_id!r}"
                )
            index[key] = run
        return index

    def open_run(self, run: RunRecord) -> RunArtifacts:
        """Attach dataset paper metadata to a run record."""
        if run.config_id not in self.configs:
            raise KeyError(f"unknown config_id {run.config_id!r}")
        if run.paper_id not in self.papers:
            raise KeyError(f"unknown paper_id {run.paper_id!r}")
        return RunArtifacts(run, self.papers[run.paper_id])

    def config_ids(self) -> list[str]:
        """Sorted config ids for stable iteration across metrics."""
        return sorted(self.configs)

    def paper_ids(self) -> list[str]:
        """Sorted paper ids present in the run index."""
        run_index = self.runs_by_config_paper()
        return sorted({paper_id for _, paper_id in run_index})


def unordered_pairs(items: list[str]) -> list[tuple[str, str]]:
    """Lexicographic unordered pairs — used for all-vs-all config comparisons."""
    ordered = sorted(items)
    return [(a, b) for i, a in enumerate(ordered) for b in ordered[i + 1 :]]


def _models_from_trace(run_dir: Path) -> dict[str, str]:
    """Read resolved role models from the first ``run_header`` in a trace."""
    trace_path = run_dir / "trace.jsonl"
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("type") == "run_header":
            models = record.get("models")
            if not isinstance(models, dict):
                break
            for role in ROLES:
                if role not in models:
                    raise ValueError(f"missing role {role!r} in run_header.models for {run_dir}")
            return dict(models)
    raise ValueError(f"missing run_header with models in {trace_path}")


def load_papers(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"missing dataset: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return {paper["id"]: paper for paper in data["papers"]}


def _validate_artifacts(run_set: RunSet) -> None:
    for run in run_set.runs:
        for name in REQUIRED_ARTIFACTS:
            path = run.run_dir / name
            if not path.is_file():
                raise FileNotFoundError(
                    f"missing {name} for config={run.config_id!r} "
                    f"paper={run.paper_id!r} at {path}"
                )
