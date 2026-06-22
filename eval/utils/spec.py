"""Batch spec parsing, resolution, and run-matrix planning for the orchestrator.

A **batch spec** (``eval/batches/<name>.json``) is the authored description of one
generation batch: a model ``pool``, the ``configs`` to run (role -> pool key or raw
slug), the ``papers`` to run them over, and a ``replicates`` count. ``experiments.py``
reads it, resolves pool keys to slugs, validates, and turns it into a flat run matrix.

This module is intentionally free of any CrewAI / reviewer import so the planning and
validation logic stays unit-testable without a model backend.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from utils.batch import REQUIRED_ARTIFACTS, ROLES

# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ResolvedConfig:
    """One configuration with role models already resolved to concrete slugs."""

    config_id: str
    models: dict[str, str]
    homogeneous: bool

    def to_registry(self) -> dict[str, Any]:
        """Shape expected by ``configs.json`` / ``Batch._load_configs``."""
        return {"models": dict(self.models), "homogeneous": self.homogeneous}


@dataclass(frozen=True)
class BatchSpec:
    """Resolved batch spec: everything needed to plan a run matrix."""

    name: str
    pool: dict[str, str]
    configs: dict[str, ResolvedConfig]
    papers: Any
    replicates: int


@dataclass(frozen=True)
class RunItem:
    """A single planned ``(config, paper, replicate)`` unit of work."""

    config_id: str
    paper_id: str
    replicate: int
    run_name: str


# --------------------------------------------------------------------------- #
# Spec loading + resolution
# --------------------------------------------------------------------------- #


def load_spec(path: Path, *, replicates_override: int | None = None) -> BatchSpec:
    """Read and resolve a batch spec JSON file into a :class:`BatchSpec`."""
    if not path.is_file():
        raise FileNotFoundError(f"missing batch spec: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return resolve_spec(raw, replicates_override=replicates_override)


def resolve_spec(raw: dict[str, Any], *, replicates_override: int | None = None) -> BatchSpec:
    """Resolve a raw spec dict (pool keys -> slugs, derive homogeneous flag)."""
    name = raw.get("batch")
    if not name or not isinstance(name, str):
        raise ValueError("spec must have a non-empty string 'batch' name")

    pool = dict(raw.get("pool", {}))
    raw_configs = raw.get("configs")
    if not isinstance(raw_configs, dict) or not raw_configs:
        raise ValueError("spec must define a non-empty 'configs' object")

    configs: dict[str, ResolvedConfig] = {}
    for config_id, entry in raw_configs.items():
        models = _resolve_models(config_id, entry, pool)
        configs[config_id] = ResolvedConfig(
            config_id=config_id,
            models=models,
            homogeneous=derive_homogeneous(models),
        )

    replicates = replicates_override if replicates_override is not None else int(raw.get("replicates", 1))
    if replicates < 1:
        raise ValueError(f"replicates must be >= 1, got {replicates}")

    return BatchSpec(
        name=name,
        pool=pool,
        configs=configs,
        papers=raw.get("papers", "all"),
        replicates=replicates,
    )


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


# --------------------------------------------------------------------------- #
# Paper selection
# --------------------------------------------------------------------------- #


def select_papers(
    spec: BatchSpec,
    papers: dict[str, dict[str, Any]],
    *,
    cli_ids: list[str] | None = None,
    cli_stratum: str | None = None,
    cli_n: int | None = None,
) -> list[str]:
    """Resolve which paper ids to run, with CLI overrides taking precedence over the spec.

    Precedence: explicit ``cli_ids`` > ``cli_stratum`` > the spec ``papers`` selector.
    ``cli_n`` (if given) truncates the resolved list after the above.
    """
    if cli_ids:
        base = _validate_ids(cli_ids, papers)
    elif cli_stratum is not None:
        base = _by_stratum(cli_stratum, papers)
    else:
        base = _resolve_selector(spec.papers, papers)

    if cli_n is not None:
        if cli_n < 0:
            raise ValueError(f"--n must be >= 0, got {cli_n}")
        base = base[:cli_n]
    return base


def _resolve_selector(selector: Any, papers: dict[str, dict[str, Any]]) -> list[str]:
    if selector is None or selector == "all":
        return sorted(papers)
    if isinstance(selector, list):
        return _validate_ids(selector, papers)
    if isinstance(selector, dict) and "stratum" in selector:
        return _by_stratum(selector["stratum"], papers)
    raise ValueError(f"unsupported 'papers' selector: {selector!r}")


def _by_stratum(stratum: str, papers: dict[str, dict[str, Any]]) -> list[str]:
    ids = sorted(pid for pid, p in papers.items() if p.get("stratum") == stratum)
    if not ids:
        raise ValueError(f"no papers found for stratum {stratum!r}")
    return ids


def _validate_ids(ids: list[str], papers: dict[str, dict[str, Any]]) -> list[str]:
    missing = [pid for pid in ids if pid not in papers]
    if missing:
        raise ValueError(f"paper ids not in dataset: {missing}")
    return list(ids)


# --------------------------------------------------------------------------- #
# Run matrix + run-dir naming + completeness
# --------------------------------------------------------------------------- #


def run_name(config_id: str, paper_id: str, replicate: int) -> str:
    """Deterministic, collision-free run directory name for a combo."""
    base = f"{config_id}__{paper_id}"
    return base if replicate == 0 else f"{base}__r{replicate}"


def build_matrix(spec: BatchSpec, paper_ids: list[str]) -> list[RunItem]:
    """Cartesian product of configs x papers x replicates as a flat, ordered list."""
    items: list[RunItem] = []
    for config_id in spec.configs:
        for paper_id in paper_ids:
            for replicate in range(spec.replicates):
                items.append(
                    RunItem(
                        config_id=config_id,
                        paper_id=paper_id,
                        replicate=replicate,
                        run_name=run_name(config_id, paper_id, replicate),
                    )
                )
    return items


def is_run_complete(run_dir: Path) -> bool:
    """True iff all required artifacts exist and the trace has a ``run_footer``."""
    for name in REQUIRED_ARTIFACTS:
        if not (run_dir / name).is_file():
            return False
    return _has_run_footer(run_dir / "trace.jsonl")


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
    spec: BatchSpec,
    *,
    prices: dict[str, dict[str, float]] | None = None,
) -> list[str]:
    """Non-fatal advisories: missing homogeneous baselines, unpriced models."""
    warnings: list[str] = []
    warnings.extend(_homogeneous_warnings(spec))
    if prices is not None:
        warnings.extend(_price_warnings(spec, prices))
    return warnings


def _homogeneous_warnings(spec: BatchSpec) -> list[str]:
    homo = [c for c in spec.configs.values() if c.homogeneous]
    if len(homo) < 2:
        return [
            f"Metric 3 (diversity) needs >=2 homogeneous configs; batch has {len(homo)}. "
            "Per-role cross-model diversity cannot be computed."
        ]
    if spec.pool:
        covered = {c.models["leader"] for c in homo}
        missing = sorted(set(spec.pool.values()) - covered)
        if missing:
            return [
                "Metric 3 (diversity) wants a homogeneous config per pool model; "
                f"missing All-* baselines for: {missing}."
            ]
    return []


def _price_warnings(spec: BatchSpec, prices: dict[str, dict[str, float]]) -> list[str]:
    from utils.prices import lookup_prices

    slugs = sorted({slug for c in spec.configs.values() for slug in c.models.values()})
    unpriced = [slug for slug in slugs if lookup_prices(slug, prices) is None]
    if unpriced:
        return [
            "Metric 5 (cost) has no price for: "
            f"{unpriced}. Add them to eval/prices.json or cost will be incomplete."
        ]
    return []
