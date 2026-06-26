"""Shared CLI helpers for eval metric entry points.

Every metric CLI calls ``add_common_args`` to register the shared flags, then
``load_run_set`` to resolve the run-set from parsed args. Metric-specific flags are
added in the metric's own ``build_parser``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from utils.run_set import DEFAULT_DATASET, RunSet

_EVAL_DIR = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _EVAL_DIR.parent


def _ensure_sys_path() -> None:
    if str(_EVAL_DIR) not in sys.path:
        sys.path.insert(0, str(_EVAL_DIR))


def add_common_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Register --run-set, --dataset, and --no-validate on any metric parser."""
    parser.add_argument(
        "--run-set",
        required=True,
        help="Run-set name (subdir under eval/reviews/ and eval/results/)",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
        help="Paper dataset JSON",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip per-run artifact existence checks",
    )
    return parser


def load_run_set(args: argparse.Namespace, *, load_dotenv_file: bool = True) -> RunSet:
    """Bootstrap sys.path, optionally load .env, and return the loaded run-set."""
    _ensure_sys_path()
    if load_dotenv_file:
        load_dotenv(_PROJECT_ROOT / "review_agent" / ".env")
    return RunSet.load(
        args.run_set,
        root=_PROJECT_ROOT,
        dataset_path=args.dataset,
        validate_artifacts=not args.no_validate,
    )
