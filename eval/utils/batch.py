"""Load an evaluation batch and resolve per-run artifacts.

Generation writes ``eval/runs/<batch>/{configs.json, runs.jsonl}``; metric scripts
read them here. See ``eval/README.md`` → ``seminar-paper/paper-context/eval-metrics.md`` (Interface).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROLES = ("leader", "clarity", "experiments", "impact")
REQUIRED_ARTIFACTS = ("final_review.md", "review.json", "trace.jsonl")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = PROJECT_ROOT / "dataset" / "eval_sample_30.json"


@dataclass(frozen=True)
class ConfigRecord:
    """One experimental configuration: which model fills each reviewer role."""

    config_id: str
    models: dict[str, str]
    homogeneous: bool


@dataclass(frozen=True)
class RunRecord:
    """Registry row linking a config and paper to on-disk run artifacts."""

    config_id: str
    paper_id: str
    run_dir: Path
    replicate: int


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

        trace_path = self.run.run_dir / "trace.jsonl"
        role_labels: dict[str, str] = {}
        outputs: dict[str, str] = {}

        for line in trace_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            rtype = record.get("type")
            if rtype == "run_header":
                role_labels = record.get("roles", {})
            elif rtype == "delegation_finished":
                label = record.get("expert_role", "")
                output = record.get("output", "")
                if label:
                    outputs[label] = output

        label = role_labels.get(role)
        if label is None:
            raise KeyError(
                f"role {role!r} not found in run_header.roles for run {self.run.run_dir}"
            )
        if label not in outputs:
            raise KeyError(
                f"no delegation_finished record for role {role!r} "
                f"(label={label!r}) in {trace_path}"
            )
        return outputs[label]


class Batch:
    """Named evaluation run-set loaded from ``eval/runs/<batch>/``.

    Holds config assignments, completed runs, and the paper dataset metrics join against.
    """

    def __init__(
        self,
        name: str,
        batch_dir: Path,
        configs: dict[str, ConfigRecord],
        runs: list[RunRecord],
        papers: dict[str, dict[str, Any]],
    ) -> None:
        self.name = name
        self.batch_dir = batch_dir
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
    ) -> Batch:
        """Load ``configs.json``, ``runs.jsonl``, and the paper dataset for a batch name."""
        project_root = root or PROJECT_ROOT
        batch_dir = project_root / "eval" / "runs" / name
        configs = _load_configs(batch_dir / "configs.json")
        runs = _load_runs(batch_dir / "runs.jsonl", project_root, replicate=0)
        papers = load_papers(dataset_path or DEFAULT_DATASET)

        batch = cls(name, batch_dir, configs, runs, papers)
        _validate_registry(batch)
        if validate_artifacts:
            _validate_artifacts(batch)
        return batch

    def metrics_dir(self) -> Path:
        """Ensure and return ``eval/runs/<batch>/metrics/``."""
        path = self.batch_dir / "metrics"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def runs_by_config_paper(self, replicate: int = 0) -> dict[tuple[str, str], RunRecord]:
        """Index runs by ``(config_id, paper_id)`` for the given replicate."""
        index: dict[tuple[str, str], RunRecord] = {}
        for run in self.runs:
            if run.replicate != replicate:
                continue
            key = (run.config_id, run.paper_id)
            if key in index:
                raise ValueError(
                    f"duplicate run for config={run.config_id!r} paper={run.paper_id!r} "
                    f"replicate={replicate}"
                )
            index[key] = run
        return index

    def open_run(self, run: RunRecord) -> RunArtifacts:
        """Attach dataset paper metadata to a registry run record."""
        if run.config_id not in self.configs:
            raise KeyError(f"unknown config_id {run.config_id!r}")
        if run.paper_id not in self.papers:
            raise KeyError(f"unknown paper_id {run.paper_id!r}")
        return RunArtifacts(run, self.papers[run.paper_id])

    def config_ids(self) -> list[str]:
        """Sorted config ids for stable iteration across metrics."""
        return sorted(self.configs)

    def paper_ids(self) -> list[str]:
        """Sorted paper ids present in the run index for replicate 0."""
        run_index = self.runs_by_config_paper()
        return sorted({paper_id for _, paper_id in run_index})


def unordered_pairs(items: list[str]) -> list[tuple[str, str]]:
    """Lexicographic unordered pairs — used for all-vs-all config comparisons."""
    ordered = sorted(items)
    return [(a, b) for i, a in enumerate(ordered) for b in ordered[i + 1 :]]


def write_metric(batch: Batch, name: str, payload: dict[str, Any]) -> Path:
    """Persist one metric result JSON with batch metadata and a timestamp envelope."""
    envelope = {
        "metric": name,
        "batch": batch.name,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    path = batch.metrics_dir() / f"{name}.json"
    path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _load_configs(path: Path) -> dict[str, ConfigRecord]:
    if not path.is_file():
        raise FileNotFoundError(f"missing configs.json: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    configs: dict[str, ConfigRecord] = {}
    for config_id, entry in raw.items():
        models = entry["models"]
        for role in ROLES:
            if role not in models:
                raise ValueError(f"config {config_id!r} missing role {role!r}")
        configs[config_id] = ConfigRecord(
            config_id=config_id,
            models=dict(models),
            homogeneous=bool(entry.get("homogeneous", False)),
        )
    return configs


def _load_runs(path: Path, root: Path, replicate: int) -> list[RunRecord]:
    if not path.is_file():
        raise FileNotFoundError(f"missing runs.jsonl: {path}")
    runs: list[RunRecord] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        run_replicate = int(row.get("replicate", 0))
        if run_replicate != replicate:
            continue
        rel = row["run_dir"]
        run_dir = (root / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
        runs.append(
            RunRecord(
                config_id=row["config_id"],
                paper_id=row["paper_id"],
                run_dir=run_dir,
                replicate=run_replicate,
            )
        )
    if not runs:
        raise ValueError(f"no runs with replicate={replicate} in {path}")
    return runs


def load_papers(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"missing dataset: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return {paper["id"]: paper for paper in data["papers"]}


def _validate_registry(batch: Batch) -> None:
    seen: set[tuple[str, str, int]] = set()
    for run in batch.runs:
        if run.config_id not in batch.configs:
            raise ValueError(f"run references unknown config_id {run.config_id!r}")
        key = (run.config_id, run.paper_id, run.replicate)
        if key in seen:
            raise ValueError(
                f"duplicate registry entry for config={run.config_id!r} "
                f"paper={run.paper_id!r} replicate={run.replicate}"
            )
        seen.add(key)


def _validate_artifacts(batch: Batch) -> None:
    for run in batch.runs:
        for name in REQUIRED_ARTIFACTS:
            path = run.run_dir / name
            if not path.is_file():
                raise FileNotFoundError(
                    f"missing {name} for config={run.config_id!r} "
                    f"paper={run.paper_id!r} at {path}"
                )
