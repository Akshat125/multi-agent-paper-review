"""Generation orchestrator: run the multi-agent reviewer over a batch.

Reads a batch from ``eval/batches.json`` by name, runs ``MultiAgentReviewer`` once
per ``(config, paper)``, and writes reviews under ``eval/reviews/<batch>/``.
Metric scripts discover those runs directly — no registry files.

Usage (from the project root, poetry venv active)::

    python eval/experiments.py --batch pilot --dry-run
    python eval/experiments.py --batch pilot
    python eval/experiments.py --batch pilot --stratum controversial --n 2
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = Path(__file__).resolve().parent

if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

from utils.batch import DEFAULT_DATASET, load_papers  # noqa: E402
from utils.spec import (  # noqa: E402
    BatchSpec,
    RunItem,
    build_matrix,
    collect_warnings,
    is_run_complete,
    load_spec,
    select_papers,
)

Runner = Callable[[dict, str, str, Path, str], Path]


@dataclass(frozen=True)
class BatchPaths:
    """Resolved on-disk locations for one batch."""

    root: Path
    name: str

    @property
    def results_dir(self) -> Path:
        return self.root / "eval" / "results" / self.name

    @property
    def reviews_dir(self) -> Path:
        return self.root / "eval" / "reviews" / self.name


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
    """Load review_agent on sys.path, .env, and isolated CrewAI storage (tracing off)."""
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


@dataclass
class Summary:
    """End-of-batch tally."""

    done: int = 0
    skipped: int = 0
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
    """Skip completed combos on disk and run the rest."""
    paths.reviews_dir.mkdir(parents=True, exist_ok=True)
    summary = Summary()
    total = len(items)

    for idx, item in enumerate(items, start=1):
        run_dir = paths.reviews_dir / item.run_name
        prefix = f"[{idx}/{total}] {item.run_name}"

        if is_run_complete(run_dir):
            summary.skipped += 1
            log(f"{prefix} skip (complete on disk)")
            continue

        log(f"{prefix} running...")
        try:
            run_dir = runner(
                spec.configs[item.config_id].models,
                papers[item.paper_id]["paper_text"],
                item.paper_id,
                paths.reviews_dir,
                item.run_name,
            )
        except Exception as exc:  # noqa: BLE001 - one failure must not kill the batch
            summary.failed += 1
            log(f"{prefix} FAILED: {exc!r}")
            continue

        if not is_run_complete(run_dir):
            summary.failed += 1
            log(f"{prefix} FAILED: incomplete artifacts at {run_dir}")
            continue

        summary.done += 1
        log(f"{prefix} done")

    return summary


def dry_run_report(
    spec: BatchSpec,
    paths: BatchPaths,
    items: list[RunItem],
    paper_ids: list[str],
    warnings: list[str],
) -> str:
    """Human-readable preflight: matrix, per-combo status, totals. No side effects."""
    lines: list[str] = []
    lines.append(f"batch     : {spec.name}")
    lines.append(f"configs   : {len(spec.configs)}  ({_homo_count(spec)} homogeneous)")
    lines.append(f"papers    : {len(paper_ids)}")
    lines.append(f"runs      : {len(items)}")
    lines.append("")

    pending = 0
    done = 0
    for item in items:
        if is_run_complete(paths.reviews_dir / item.run_name):
            done += 1
            status = "done"
        else:
            pending += 1
            status = "pending"
        lines.append(f"  [{status:8}] {item.run_name}")

    lines.append("")
    lines.append(f"status    : {pending} pending, {done} done")
    if warnings:
        lines.append("")
        lines.append("warnings  :")
        lines.extend(f"  - {w}" for w in warnings)
    return "\n".join(lines)


def _homo_count(spec: BatchSpec) -> int:
    return sum(1 for c in spec.configs.values() if c.homogeneous)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generation orchestrator (one run per combo)")
    parser.add_argument("--batch", required=True, help="Batch name (key in eval/batches.json)")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET, help="Paper dataset JSON")
    parser.add_argument("--dry-run", action="store_true", help="Print the run matrix and exit; no spend")
    parser.add_argument("--papers", help="Comma-separated paper ids (overrides spec 'papers')")
    parser.add_argument("--stratum", help="Run only papers in this stratum (overrides spec 'papers')")
    parser.add_argument("--n", type=int, help="Cap the number of selected papers")
    parser.add_argument("--limit", type=int, help="Cap the number of runs (after planning)")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = build_parser().parse_args(argv)

    spec = load_spec(args.batch)
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
        f"\nbatch {spec.name}: {summary.done} done, "
        f"{summary.skipped} skipped, {summary.failed} failed"
    )
    print(f"reviews: {paths.reviews_dir}")
    return 1 if summary.failed else 0


def _try_load_prices() -> Optional[dict[str, dict[str, float]]]:
    try:
        from utils.prices import load_prices

        return load_prices()
    except Exception:  # noqa: BLE001 - prices are advisory only
        return None


if __name__ == "__main__":
    raise SystemExit(main())
