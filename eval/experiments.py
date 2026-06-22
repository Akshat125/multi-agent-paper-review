"""Generation orchestrator: run the multi-agent reviewer over a batch spec.

Reads a committed batch spec (``eval/batches/<name>.json``), runs
``MultiAgentReviewer`` once per ``(config, paper, replicate)``, and writes the
``eval/runs/<batch>/`` registry (``configs.json`` + ``runs.jsonl``) that the metric
scripts consume. See ``eval/README.md`` → ``seminar-paper/paper-context/eval-metrics.md`` (Interface) for the registry contract and
``eval/utils/spec.py`` for the batch spec format.

Pure generation: it never computes metrics and never prunes configs. Stage 1 ->
Stage 2 promotion (Successive Halving) is a manual step performed between two specs.

Usage (from the project root, poetry venv active)::

    python eval/experiments.py --spec eval/batches/pilot.json --dry-run
    python eval/experiments.py --spec eval/batches/pilot.json
    python eval/experiments.py --spec eval/batches/pilot.json --stratum controversial --n 2
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = Path(__file__).resolve().parent

# Make ``utils`` importable when run as a script (pytest sets this via pythonpath).
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

from utils.spec import (  # noqa: E402
    BatchSpec,
    RunItem,
    build_matrix,
    collect_warnings,
    is_run_complete,
    load_spec,
    select_papers,
)

DEFAULT_DATASET = ROOT / "dataset" / "eval_sample_30.json"

# A runner produces the three artifacts under ``output_dir/run_name`` and returns
# the run directory. Injectable so tests can avoid a live model backend.
Runner = Callable[[dict, str, str, Path, str], Path]


# --------------------------------------------------------------------------- #
# Batch paths + registry IO
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class BatchPaths:
    """Resolved on-disk locations for one batch."""

    root: Path
    name: str

    @property
    def batch_dir(self) -> Path:
        return self.root / "eval" / "runs" / self.name

    @property
    def outputs_dir(self) -> Path:
        return self.root / "eval" / "outputs" / self.name

    @property
    def configs_path(self) -> Path:
        return self.batch_dir / "configs.json"

    @property
    def runs_path(self) -> Path:
        return self.batch_dir / "runs.jsonl"

    @property
    def errors_path(self) -> Path:
        return self.batch_dir / "errors.jsonl"


def write_configs(spec: BatchSpec, paths: BatchPaths) -> Path:
    """Write ``configs.json`` (once) per eval-metrics.md Interface. Idempotent content."""
    paths.batch_dir.mkdir(parents=True, exist_ok=True)
    payload = {cid: cfg.to_registry() for cid, cfg in spec.configs.items()}
    paths.configs_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return paths.configs_path


def load_done_keys(paths: BatchPaths) -> set[tuple[str, str, int]]:
    """Read ``runs.jsonl`` into a set of ``(config_id, paper_id, replicate)`` keys."""
    done: set[tuple[str, str, int]] = set()
    if not paths.runs_path.is_file():
        return done
    for line in paths.runs_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        done.add((row["config_id"], row["paper_id"], int(row.get("replicate", 0))))
    return done


def append_run(paths: BatchPaths, item: RunItem, rel_run_dir: str) -> None:
    """Append one completed-run line to ``runs.jsonl`` (append-only)."""
    paths.batch_dir.mkdir(parents=True, exist_ok=True)
    row = {
        "config_id": item.config_id,
        "paper_id": item.paper_id,
        "run_dir": rel_run_dir,
        "replicate": item.replicate,
        "ts": _now(),
    }
    with paths.runs_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def append_error(paths: BatchPaths, item: RunItem, error: str) -> None:
    """Append one failed-run line to ``errors.jsonl`` (never to ``runs.jsonl``)."""
    paths.batch_dir.mkdir(parents=True, exist_ok=True)
    row = {
        "config_id": item.config_id,
        "paper_id": item.paper_id,
        "replicate": item.replicate,
        "error": error,
        "ts": _now(),
    }
    with paths.errors_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _rel_run_dir(paths: BatchPaths, item: RunItem) -> str:
    return str((paths.outputs_dir / item.run_name).relative_to(paths.root))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
# Run status (resume / repair)
# --------------------------------------------------------------------------- #

PENDING, DONE, REPAIRED = "pending", "done", "repaired"


def status_of(
    item: RunItem,
    paths: BatchPaths,
    done_keys: set[tuple[str, str, int]],
) -> str:
    """Classify a combo: already in registry (``done``), complete on disk but
    missing its registry line (``repaired``), or not yet run (``pending``)."""
    if (item.config_id, item.paper_id, item.replicate) in done_keys:
        return DONE
    if is_run_complete(paths.outputs_dir / item.run_name):
        return REPAIRED
    return PENDING


# --------------------------------------------------------------------------- #
# Default runner (lazy CrewAI import)
# --------------------------------------------------------------------------- #


def default_runner(
    models: dict[str, str],
    paper_text: str,
    paper_id: str,
    output_dir: Path,
    run_name_: str,
) -> Path:
    """Run the real reviewer for one combo and return its run directory."""
    _bootstrap_review_env()
    from src.agents.reviewer import MultiAgentReviewer  # type: ignore[import]
    from src.utils import TraceLogger  # type: ignore[import]

    trace = TraceLogger(output_dir=output_dir, run_name=run_name_)
    reviewer = MultiAgentReviewer(
        leader_model=models["leader"],
        clarity_model=models["clarity"],
        experiments_model=models["experiments"],
        impact_model=models["impact"],
    )
    reviewer.review(paper_text, trace_logger=trace, paper_id=paper_id)
    return trace.run_dir


_REVIEW_ENV_READY = False


def _bootstrap_review_env() -> None:
    """Mirror eval/smoke.py: path, dotenv, isolated CrewAI storage, tracing off."""
    global _REVIEW_ENV_READY
    if _REVIEW_ENV_READY:
        return
    review_src = str(ROOT / "review_agent")
    if review_src not in sys.path:
        sys.path.insert(0, review_src)
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / "review_agent" / ".env")
    except Exception:  # noqa: BLE001 - dotenv is best-effort
        pass
    os.environ.setdefault("CREWAI_STORAGE_DIR", tempfile.mkdtemp(prefix="crewai_"))
    os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
    _REVIEW_ENV_READY = True


# --------------------------------------------------------------------------- #
# Planning + execution
# --------------------------------------------------------------------------- #


@dataclass
class Summary:
    """End-of-batch tally."""

    done: int = 0
    skipped: int = 0
    repaired: int = 0
    failed: int = 0


def plan_runs(
    spec: BatchSpec,
    papers: dict[str, dict[str, Any]],
    *,
    cli_ids: list[str] | None = None,
    cli_stratum: str | None = None,
    cli_n: int | None = None,
    limit: int | None = None,
) -> tuple[list[RunItem], list[str]]:
    """Resolve papers, build the matrix, and apply ``--limit``."""
    paper_ids = select_papers(
        spec, papers, cli_ids=cli_ids, cli_stratum=cli_stratum, cli_n=cli_n
    )
    if not paper_ids:
        raise ValueError("no papers selected")
    items = build_matrix(spec, paper_ids)
    if limit is not None:
        items = items[:limit]
    return items, paper_ids


def execute(
    spec: BatchSpec,
    papers: dict[str, dict[str, Any]],
    paths: BatchPaths,
    items: list[RunItem],
    *,
    runner: Runner = default_runner,
    log: Callable[[str], None] = print,
) -> Summary:
    """Write ``configs.json``, repair/skip completed combos, and run the rest."""
    write_configs(spec, paths)
    done_keys = load_done_keys(paths)
    summary = Summary()
    total = len(items)

    for idx, item in enumerate(items, start=1):
        status = status_of(item, paths, done_keys)
        prefix = f"[{idx}/{total}] {item.run_name}"

        if status == DONE:
            summary.skipped += 1
            log(f"{prefix} skip (already in registry)")
            continue
        if status == REPAIRED:
            append_run(paths, item, _rel_run_dir(paths, item))
            done_keys.add((item.config_id, item.paper_id, item.replicate))
            summary.repaired += 1
            log(f"{prefix} repaired (artifacts on disk, registry line added)")
            continue

        log(f"{prefix} running...")
        try:
            run_dir = runner(
                spec.configs[item.config_id].models,
                papers[item.paper_id]["paper_text"],
                item.paper_id,
                paths.outputs_dir,
                item.run_name,
            )
        except Exception as exc:  # noqa: BLE001 - one failure must not kill the batch
            append_error(paths, item, repr(exc))
            summary.failed += 1
            log(f"{prefix} FAILED: {exc!r}")
            continue

        if not is_run_complete(run_dir):
            append_error(paths, item, "run produced incomplete artifacts")
            summary.failed += 1
            log(f"{prefix} FAILED: incomplete artifacts at {run_dir}")
            continue

        append_run(paths, item, _rel_run_dir(paths, item))
        done_keys.add((item.config_id, item.paper_id, item.replicate))
        summary.done += 1
        log(f"{prefix} done")

    return summary


# --------------------------------------------------------------------------- #
# Dry-run reporting
# --------------------------------------------------------------------------- #


def dry_run_report(
    spec: BatchSpec,
    paths: BatchPaths,
    items: list[RunItem],
    paper_ids: list[str],
    warnings: list[str],
) -> str:
    """Human-readable preflight: matrix, per-combo status, totals. No side effects."""
    done_keys = load_done_keys(paths)
    lines: list[str] = []
    lines.append(f"batch     : {spec.name}")
    lines.append(f"configs   : {len(spec.configs)}  ({_homo_count(spec)} homogeneous)")
    lines.append(f"papers    : {len(paper_ids)}")
    lines.append(f"replicates: {spec.replicates}")
    lines.append(f"runs      : {len(items)}")
    lines.append("")

    counts = {PENDING: 0, DONE: 0, REPAIRED: 0}
    for item in items:
        status = status_of(item, paths, done_keys)
        counts[status] += 1
        lines.append(f"  [{status:8}] {item.run_name}")

    lines.append("")
    lines.append(
        f"status    : {counts[PENDING]} pending, "
        f"{counts[DONE]} done, {counts[REPAIRED]} repairable"
    )
    if warnings:
        lines.append("")
        lines.append("warnings  :")
        lines.extend(f"  - {w}" for w in warnings)
    return "\n".join(lines)


def _homo_count(spec: BatchSpec) -> int:
    return sum(1 for c in spec.configs.values() if c.homogeneous)


# --------------------------------------------------------------------------- #
# Dataset loading
# --------------------------------------------------------------------------- #


def load_papers(path: Path) -> dict[str, dict[str, Any]]:
    """Load the paper dataset keyed by id (same shape as ``utils.batch``)."""
    if not path.is_file():
        raise FileNotFoundError(f"missing dataset: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return {paper["id"]: paper for paper in data["papers"]}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generation orchestrator (one run per combo)")
    parser.add_argument("--spec", type=Path, required=True, help="Batch spec JSON (eval/batches/<name>.json)")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET, help="Paper dataset JSON")
    parser.add_argument("--dry-run", action="store_true", help="Print the run matrix and exit; no spend")
    parser.add_argument("--papers", help="Comma-separated paper ids (overrides spec 'papers')")
    parser.add_argument("--stratum", help="Run only papers in this stratum (overrides spec 'papers')")
    parser.add_argument("--n", type=int, help="Cap the number of selected papers")
    parser.add_argument("--replicates", type=int, help="Override the spec replicate count")
    parser.add_argument("--limit", type=int, help="Cap the number of runs (after planning)")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = build_parser().parse_args(argv)

    spec = load_spec(args.spec, replicates_override=args.replicates)
    papers = load_papers(args.dataset)
    paths = BatchPaths(root=ROOT, name=spec.name)

    cli_ids = [pid.strip() for pid in args.papers.split(",") if pid.strip()] if args.papers else None
    items, paper_ids = plan_runs(
        spec,
        papers,
        cli_ids=cli_ids,
        cli_stratum=args.stratum,
        cli_n=args.n,
        limit=args.limit,
    )

    prices = _try_load_prices()
    warnings = collect_warnings(spec, prices=prices)

    if args.dry_run:
        print(dry_run_report(spec, paths, items, paper_ids, warnings))
        return 0

    for w in warnings:
        print(f"warning: {w}")

    summary = execute(spec, papers, paths, items)
    print(
        f"\nbatch {spec.name}: {summary.done} done, {summary.repaired} repaired, "
        f"{summary.skipped} skipped, {summary.failed} failed"
    )
    print(f"registry: {paths.batch_dir}")
    return 1 if summary.failed else 0


def _try_load_prices() -> Optional[dict[str, dict[str, float]]]:
    try:
        from utils.prices import load_prices

        return load_prices()
    except Exception:  # noqa: BLE001 - prices are advisory only
        return None


if __name__ == "__main__":
    raise SystemExit(main())
