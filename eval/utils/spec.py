"""RunSet spec parsing, resolution, and run-matrix planning for the orchestrator.

All batch definitions live in ``eval/batches.json`` — one file, batches keyed by
name. Each entry has a model ``pool``, ``configs`` (role -> pool key or raw slug),
and ``papers`` (``\"all\"`` or a list of ids). ``experiments.py`` reads a batch by name, resolves pool keys to
slugs, and turns it into a flat run matrix.

This module is intentionally free of any CrewAI / reviewer import so the planning and
validation logic stays unit-testable without a model backend.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

ROLES = ("leader", "clarity", "experiments", "impact")
REQUIRED_ARTIFACTS = ("final_review.md", "review.json", "trace.jsonl")

DEFAULT_BATCHES = Path(__file__).resolve().parents[1] / "batches.json"

# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Config:
    """One experimental configuration: role models and whether all four match."""

    config_id: str
    models: dict[str, str]
    homogeneous: bool


@dataclass(frozen=True)
class EvalPlan:
    """Resolved eval plan from ``batches.json``: everything needed to plan a run matrix."""

    name: str
    pool: dict[str, str]
    configs: dict[str, Config]
    papers: list[str] | Literal["all"]


@dataclass(frozen=True)
class RunItem:
    """A single planned ``(config, paper)`` unit of work."""

    config_id: str
    paper_id: str
    run_name: str


# --------------------------------------------------------------------------- #
# Spec loading + resolution
# --------------------------------------------------------------------------- #


def load_spec(name: str, *, batches_path: Path | None = None) -> EvalPlan:
    """Load and resolve one batch from ``eval/batches.json`` by name."""
    path = batches_path or DEFAULT_BATCHES
    if not path.is_file():
        raise FileNotFoundError(f"missing batches file: {path}")
    all_batches = json.loads(path.read_text(encoding="utf-8"))
    if name not in all_batches:
        known = ", ".join(sorted(all_batches))
        raise KeyError(f"unknown batch {name!r}; known batches: {known or '(none)'}")
    raw = all_batches[name]
    if not isinstance(raw, dict):
        raise ValueError(f"batch {name!r} must be an object")
    return resolve_spec(name, raw)


def resolve_spec(name: str, raw: dict[str, Any]) -> EvalPlan:
    """Resolve a raw batch entry (pool keys -> slugs, derive homogeneous flag)."""
    if not name:
        raise ValueError("batch name must be non-empty")

    pool = dict(raw.get("pool", {}))
    raw_configs = raw.get("configs")
    if not isinstance(raw_configs, dict) or not raw_configs:
        raise ValueError("spec must define a non-empty 'configs' object")

    configs: dict[str, Config] = {}
    for config_id, entry in raw_configs.items():
        models = _resolve_models(config_id, entry, pool)
        configs[config_id] = Config(
            config_id=config_id,
            models=models,
            homogeneous=derive_homogeneous(models),
        )

    return EvalPlan(
        name=name,
        pool=pool,
        configs=configs,
        papers=_parse_papers(raw.get("papers", "all")),
    )


def _parse_papers(raw: Any) -> list[str] | Literal["all"]:
    """Accept ``\"all\"`` or a non-empty list of paper id strings from batches.json."""
    if raw is None or raw == "all":
        return "all"
    if isinstance(raw, list):
        if not raw:
            raise ValueError("'papers' list must be non-empty")
        for paper_id in raw:
            if not isinstance(paper_id, str) or not paper_id:
                raise ValueError("'papers' must be a list of non-empty paper id strings")
        return list(raw)
    raise ValueError("'papers' must be 'all' or a list of paper ids")


def _resolve_models(config_id: str, entry: Any, pool: dict[str, str]) -> dict[str, str]:
    """Map each role value to a concrete slug; pool keys resolve, others pass through."""
    models_in = entry.get("models", entry) if isinstance(entry, dict) else None
    if not isinstance(models_in, dict):
        raise ValueError(f"config {config_id!r} must map roles to models")

    resolved: dict[str, str] = {}
    for role in ROLES:
        if role not in models_in:
            raise ValueError(f"config {config_id!r} missing role {role!r}")
        value = models_in[role]
        if not isinstance(value, str) or not value:
            raise ValueError(f"config {config_id!r} role {role!r} must be a non-empty string")
        resolved[role] = pool.get(value, value)
    return resolved


def derive_homogeneous(models: dict[str, str]) -> bool:
    """A config is homogeneous iff the same slug fills all four roles."""
    return len(set(models.values())) == 1


def resolve_paper_ids(spec: EvalPlan, papers: dict[str, dict[str, Any]]) -> list[str]:
    """Map the batch's ``papers`` field to concrete ids from the loaded dataset."""
    if spec.papers == "all":
        return sorted(papers)
    missing = [paper_id for paper_id in spec.papers if paper_id not in papers]
    if missing:
        raise ValueError(f"paper ids not in dataset: {missing}")
    return list(spec.papers)


# --------------------------------------------------------------------------- #
# Run matrix + run-dir naming + completeness
# --------------------------------------------------------------------------- #


def run_name(config_id: str, paper_id: str) -> str:
    """Deterministic run directory name: ``<config_id>__<paper_id>``."""
    return f"{config_id}__{paper_id}"


def parse_run_dir_name(dirname: str) -> tuple[str, str]:
    """Split a run directory name back into ``(config_id, paper_id)``."""
    parts = dirname.split("__")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"invalid run directory name {dirname!r}; expected config__paper")
    return parts[0], parts[1]


def build_matrix(spec: EvalPlan, paper_ids: list[str]) -> list[RunItem]:
    """Cartesian product of configs x papers as a flat, ordered list."""
    items: list[RunItem] = []
    for config_id in spec.configs:
        for paper_id in paper_ids:
            items.append(
                RunItem(
                    config_id=config_id,
                    paper_id=paper_id,
                    run_name=run_name(config_id, paper_id),
                )
            )
    return items


def is_run_complete(run_dir: Path) -> bool:
    """True iff all artifacts exist, the trace has a ``run_footer``, and the
    review parsed to a non-null rating.

    The rating gate matters because a run whose leader output failed to parse
    (e.g. an upstream rate-limit wiped the experts, or the leader emitted only a
    plan) still writes all three artifacts plus a ``run_footer`` with
    ``rating: null``. Without this check such a run counts as "complete", so the
    generator skips it on resume and the metric loaders silently ingest an empty
    review. Treating null-rating runs as incomplete makes them auto-regenerate
    and keeps them out of the metric set.
    """
    for name in REQUIRED_ARTIFACTS:
        if not (run_dir / name).is_file():
            return False
    if not _has_run_footer(run_dir / "trace.jsonl"):
        return False
    return review_is_substantive(run_dir / "review.json")


def review_is_substantive(review_json_path: Path) -> bool:
    """True iff ``review.json`` parsed a non-null rating *and* every section body
    is non-empty.

    A rating alone is not enough: some Mistral-leader runs emit only a plan or a
    bare ``RATING:`` line, which yields a rating but blank Summary/Strengths/
    Weaknesses/Questions. Such a review carries no content for the judges, so it
    is treated as incomplete (auto-regenerated, excluded from metrics).
    """
    try:
        data = json.loads(review_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if data.get("rating") is None:
        return False
    return all((data.get(name) or "").strip() for name in ("summary", "strengths", "weaknesses", "questions"))


def _has_run_footer(trace_path: Path) -> bool:
    try:
        for line in trace_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                if json.loads(line).get("type") == "run_footer":
                    return True
            except json.JSONDecodeError:
                continue
    except OSError:
        return False
    return False


# --------------------------------------------------------------------------- #
# Validation warnings (non-fatal)
# --------------------------------------------------------------------------- #


def collect_warnings(
    spec: EvalPlan,
    *,
    prices: dict[str, dict[str, float]] | None = None,
) -> list[str]:
    """Non-fatal advisories: too few homogeneous configs, unpriced models."""
    warnings: list[str] = []
    warnings.extend(_homogeneous_warnings(spec))
    if prices is not None:
        warnings.extend(_price_warnings(spec, prices))
    return warnings


def _homogeneous_warnings(spec: EvalPlan) -> list[str]:
    homo = [c for c in spec.configs.values() if c.homogeneous]
    if len(homo) < 2:
        return [
            f"Metric 3 (diversity) needs >=2 homogeneous configs; batch has {len(homo)}. "
            "Per-role cross-model diversity cannot be computed."
        ]
    return []


def _price_warnings(spec: EvalPlan, prices: dict[str, dict[str, float]]) -> list[str]:
    from utils.prices import lookup_prices

    slugs = sorted({slug for c in spec.configs.values() for slug in c.models.values()})
    unpriced = [slug for slug in slugs if lookup_prices(slug, prices) is None]
    if unpriced:
        return [
            "Metric 5 (cost) has no price for: "
            f"{unpriced}. Add them to eval/prices.json or cost will be incomplete."
        ]
    return []
