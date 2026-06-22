"""Shared CLI helpers for eval metric entry points.

Every metric CLI calls ``add_common_args`` to register the shared flags, then
``load_batch`` to resolve the batch from parsed args. Metric-specific flags are
added in the metric's own ``build_parser``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from utils.batch import Batch, DEFAULT_DATASET

_EVAL_DIR = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _EVAL_DIR.parent


def _ensure_sys_path() -> None:
    if str(_EVAL_DIR) not in sys.path:
        sys.path.insert(0, str(_EVAL_DIR))


def add_common_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Register --batch, --dataset, and --no-validate on any metric parser."""
    parser.add_argument("--batch", required=True, help="Batch name under eval/runs/<batch>/")
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


def load_batch(args: argparse.Namespace, *, load_dotenv_file: bool = True) -> Batch:
    """Bootstrap sys.path, optionally load .env, and return the parsed batch."""
    _ensure_sys_path()
    if load_dotenv_file:
        load_dotenv(_PROJECT_ROOT / "review_agent" / ".env")
    return Batch.load(
        args.batch,
        root=_PROJECT_ROOT,
        dataset_path=args.dataset,
        validate_artifacts=not args.no_validate,
    )
