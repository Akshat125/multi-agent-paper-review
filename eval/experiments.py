"""Generation orchestrator: run the multi-agent reviewer over a batch.

Reads a batch from ``eval/batches.json`` by name, runs ``MultiAgentReviewer`` once
per ``(config, paper)``, and writes reviews under ``eval/reviews/<batch>/``.
Metric scripts discover those runs directly — no registry files.

Usage (from the project root, poetry venv active)::

    python eval/experiments.py --run-set pilot --dry-run
    python eval/experiments.py --run-set pilot
    python eval/experiments.py --run-set pilot --limit 2
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = Path(__file__).resolve().parent

if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

from utils.run_set import DEFAULT_DATASET, load_papers  # noqa: E402
from utils.spec import (  # noqa: E402
    EvalPlan,
    RunItem,
    build_matrix,
    collect_warnings,
    is_run_complete,
    load_spec,
    resolve_paper_ids,
)

Runner = Callable[[dict, str, str, Path, str], Path]


@dataclass(frozen=True)
class EvalPaths:
    """Resolved on-disk locations for one eval plan / run-set."""

    root: Path
    name: str

    @property
    def results_dir(self) -> Path:
        return self.root / "eval" / "results" / self.name

    @property
    def reviews_dir(self) -> Path:
        return self.root / "eval" / "reviews" / self.name


def _attempt_rating_ok(run_dir: Path) -> bool:
    """True iff the attempt produced a substantive review (rating + all sections).

    Shares :func:`utils.spec.review_is_substantive` with ``is_run_complete`` so
    the retry loop and the completeness gate agree on what counts as a usable
    review.
    """
    from utils.spec import review_is_substantive

    return review_is_substantive(run_dir / "review.json")


def default_runner(
    models: dict[str, str],
    paper_text: str,
    paper_id: str,
    output_dir: Path,
    run_name_: str,
) -> Path:
    """Run the real reviewer for one combo and return its run directory.

    Retries up to ``REVIEW_MAX_ATTEMPTS`` (default 3) when an attempt fails to
    yield a parseable review (``rating is None``) or raises (e.g. a transient
    upstream ``429``). Each attempt runs in an isolated ``_attempts/`` directory
    so traces never interleave; the first attempt that produces a valid rating
    (else the last attempt) is committed to ``output_dir/run_name_``. This makes
    a single batch invocation self-healing against the deterministic
    Mistral-leader formatting failures and sporadic rate limits seen on the full
    run, without changing prompts, temperature, or topology.
    """
    _bootstrap_review_env()
    import shutil
    import time as _time

    from src.agents.reviewer import MultiAgentReviewer  # type: ignore[import]
    from src.utils import TraceLogger  # type: ignore[import]

    max_attempts = max(1, int(os.getenv("REVIEW_MAX_ATTEMPTS", "3")))
    attempts_root = Path(output_dir) / "_attempts"
    final_dir = Path(output_dir) / run_name_

    last_dir: Path | None = None
    for attempt in range(1, max_attempts + 1):
        attempt_dir = attempts_root / f"{run_name_}__a{attempt}"
        if attempt_dir.exists():
            shutil.rmtree(attempt_dir)
        trace = TraceLogger(output_dir=attempts_root, run_name=f"{run_name_}__a{attempt}")
        # Fresh reviewer per attempt so no leader/agent state carries over.
        reviewer = MultiAgentReviewer(
            leader_model=models["leader"],
            clarity_model=models["clarity"],
            experiments_model=models["experiments"],
            impact_model=models["impact"],
        )
        try:
            reviewer.review(paper_text, trace_logger=trace, paper_id=paper_id)
        except Exception:  # noqa: BLE001 - retry transient failures (e.g. 429)
            last_dir = trace.run_dir
            if attempt < max_attempts:
                _time.sleep(min(30, 5 * attempt))
                continue
            break
        last_dir = trace.run_dir
        if _attempt_rating_ok(trace.run_dir):
            break
        if attempt < max_attempts:
            _time.sleep(min(30, 5 * attempt))

    # Commit the winning (or last) attempt to the canonical run directory.
    if last_dir is not None:
        if final_dir.exists():
            shutil.rmtree(final_dir)
        shutil.move(str(last_dir), str(final_dir))
    for stale in attempts_root.glob(f"{run_name_}__a*"):
        shutil.rmtree(stale, ignore_errors=True)
    return final_dir


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
    spec: EvalPlan,
    papers: dict[str, dict[str, Any]],
    *,
    limit: int | None = None,
) -> tuple[list[RunItem], list[str]]:
    """Resolve papers from the batch spec, build the matrix, and apply ``--limit``."""
    paper_ids = resolve_paper_ids(spec, papers)
    if not paper_ids:
        raise ValueError("no papers selected")
    items = build_matrix(spec, paper_ids)
    if limit is not None:
        items = items[:limit]
    return items, paper_ids


def execute(
    spec: EvalPlan,
    papers: dict[str, dict[str, Any]],
    paths: EvalPaths,
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


@dataclass
class _RunTask:
    """Self-contained unit of work shipped to a worker process (must be picklable)."""

    run_name: str
    paper_id: str
    paper_text: str
    models: dict = field(default_factory=dict)
    reviews_dir: Path = Path(".")


@dataclass
class _RunResult:
    run_name: str
    status: str  # "done" | "incomplete" | "failed"
    error: Optional[str] = None


def _run_one_item(task: _RunTask) -> _RunResult:
    """Worker entry point: run one review in this process and report status.

    Runs in a *separate process* (see :func:`execute_parallel`) so each review gets
    its own CrewAI ``crewai_event_bus`` singleton — in-process threads would let
    concurrent runs cross-contaminate each other's trace/token records.
    """
    try:
        run_dir = default_runner(
            task.models, task.paper_text, task.paper_id, task.reviews_dir, task.run_name
        )
        return _RunResult(task.run_name, "done" if is_run_complete(run_dir) else "incomplete")
    except Exception as exc:  # noqa: BLE001 - one failure must not kill the batch
        return _RunResult(task.run_name, "failed", repr(exc))


def execute_parallel(
    spec: EvalPlan,
    papers: dict[str, dict[str, Any]],
    paths: EvalPaths,
    items: list[RunItem],
    *,
    concurrency: int,
    log: Callable[[str], None] = print,
) -> Summary:
    """Like :func:`execute`, but runs pending combos across ``concurrency`` processes.

    Completed combos are skipped up front (resumable, never re-billed). Each in-flight
    review issues at most one OpenRouter call at a time, so peak concurrent API calls
    is bounded by ``concurrency`` — kept modest on purpose to avoid upstream 429s
    (which can still incur prompt-processing cost).
    """
    paths.reviews_dir.mkdir(parents=True, exist_ok=True)
    summary = Summary()

    pending: list[RunItem] = []
    for item in items:
        if is_run_complete(paths.reviews_dir / item.run_name):
            summary.skipped += 1
            log(f"skip (complete on disk): {item.run_name}")
        else:
            pending.append(item)

    total = len(pending)
    if total == 0:
        return summary

    tasks = [
        _RunTask(
            run_name=item.run_name,
            paper_id=item.paper_id,
            paper_text=papers[item.paper_id]["paper_text"],
            models=spec.configs[item.config_id].models,
            reviews_dir=paths.reviews_dir,
        )
        for item in pending
    ]

    log(f"running {total} pending runs at concurrency {concurrency}...")
    done = 0
    with ProcessPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(_run_one_item, task): task.run_name for task in tasks}
        for future in as_completed(futures):
            name = futures[future]
            done += 1
            prefix = f"[{done}/{total}] {name}"
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001 - worker died (e.g. crash)
                summary.failed += 1
                log(f"{prefix} FAILED: {exc!r}")
                continue
            if result.status == "done":
                summary.done += 1
                log(f"{prefix} done")
            else:
                summary.failed += 1
                log(f"{prefix} FAILED: {result.error or result.status}")

    return summary


def dry_run_report(
    spec: EvalPlan,
    paths: EvalPaths,
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


def _homo_count(spec: EvalPlan) -> int:
    return sum(1 for c in spec.configs.values() if c.homogeneous)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generation orchestrator (one run per combo)")
    parser.add_argument("--run-set", required=True, help="RunSet name (key in eval/batches.json)")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET, help="Paper dataset JSON")
    parser.add_argument("--dry-run", action="store_true", help="Print the run matrix and exit; no spend")
    parser.add_argument("--limit", type=int, help="Cap the number of runs (after planning)")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        help="Parallel reviews, each in its own process (default 4; use 1 for sequential). "
        "Peak concurrent OpenRouter calls = this value; raise cautiously to avoid upstream 429s.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = build_parser().parse_args(argv)

    spec = load_spec(args.run_set)
    papers = load_papers(args.dataset)
    paths = EvalPaths(root=ROOT, name=spec.name)

    items, paper_ids = plan_runs(spec, papers, limit=args.limit)

    prices = _try_load_prices()
    warnings = collect_warnings(spec, prices=prices)

    if args.dry_run:
        print(dry_run_report(spec, paths, items, paper_ids, warnings))
        return 0

    for w in warnings:
        print(f"warning: {w}")

    concurrency = max(1, args.concurrency)
    if concurrency == 1:
        summary = execute(spec, papers, paths, items)
    else:
        summary = execute_parallel(spec, papers, paths, items, concurrency=concurrency)
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
