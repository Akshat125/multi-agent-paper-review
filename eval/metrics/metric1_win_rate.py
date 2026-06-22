"""CLI entry point for Metric 1 — LLM-as-judge win-rate.

Usage (from project root):
    python eval/metrics/metric1_win_rate.py --batch pilot_v1 \\
        --judge google/gemini-2.5-pro --judge anthropic/claude-sonnet-4-5
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

EVAL_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = EVAL_DIR.parent

sys.path.insert(0, str(EVAL_DIR))

from metrics.batch import DEFAULT_DATASET, Batch  # noqa: E402
from metrics.rubric import DEFAULT_DIMENSIONS  # noqa: E402
from metrics.win_rate import WinRateMetric  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Metric 1: LLM-as-judge side-by-side win-rate")
    parser.add_argument("--batch", required=True, help="Batch name under eval/runs/<batch>/")
    parser.add_argument(
        "--judge",
        action="append",
        dest="judges",
        required=True,
        help="Judge model id (repeatable; P4 requires >=2 out-of-suite judges)",
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET, help="Paper dataset JSON")
    parser.add_argument(
        "--dimension",
        action="append",
        dest="dimensions",
        help="Rubric dimension to score (repeatable; default: all core dimensions)",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip per-run artifact existence checks",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv(PROJECT_ROOT / "review_agent" / ".env")
    args = build_parser().parse_args(argv)

    dimensions = tuple(args.dimensions) if args.dimensions else DEFAULT_DIMENSIONS
    if "overall" not in dimensions:
        raise SystemExit("overall dimension is mandatory")
    if len(args.judges) < 2:
        raise SystemExit("P4 requires at least two --judge models")

    batch = Batch.load(
        args.batch,
        root=PROJECT_ROOT,
        dataset_path=args.dataset,
        validate_artifacts=not args.no_validate,
    )

    metric = WinRateMetric(
        batch,
        args.judges,
        dimensions=dimensions,
    )
    output_path = metric.write()
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
