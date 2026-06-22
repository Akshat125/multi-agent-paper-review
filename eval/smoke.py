"""Smoke-test: run the multi-agent reviewer on one paper from the eval set.

Usage (from the project root with the poetry venv active):
    python eval/smoke.py
"""

from __future__ import annotations

import json
import os
import statistics
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = EVAL_DIR / "outputs"

sys.path.insert(0, str(ROOT / "review_agent"))

from dotenv import load_dotenv

load_dotenv(ROOT / "review_agent" / ".env")

_tmp_dir = tempfile.mkdtemp(prefix="crewai_")
os.environ.setdefault("CREWAI_STORAGE_DIR", _tmp_dir)
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")

from src.agents.reviewer import MultiAgentReviewer
from src.utils import TraceLogger

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MODEL = "qwen/qwen3-8b"
MAX_CHARS: int | None = None  # None = full paper
PAPER_INDEX = 0

_SECTION_KEYS = ("summary", "strengths", "weaknesses", "questions")


class VerboseTraceLogger(TraceLogger):
    """TraceLogger that also prints each event to stdout as it's logged."""

    def log(self, event_type: str, **fields: Any) -> None:
        super().log(event_type, **fields)
        if event_type == "delegation_finished":
            print(f"  -> {fields.get('expert_role')} responded", flush=True)
        elif event_type == "delegation_error":
            print(f"  !! delegation error: {fields.get('expert_role')}", flush=True)
        elif event_type == "leader_completion":
            print(f"[leader done] {fields.get('output_chars')} chars", flush=True)
        elif event_type == "review_parsed":
            print(
                f"[review_parsed] rating={fields.get('rating')} "
                f"summary={fields.get('summary_chars')} chars",
                flush=True,
            )
        else:
            print(f"[{event_type}]", flush=True)


def _human_mean_rating(paper: dict) -> float:
    return statistics.mean(paper["ratings"])


def _print_inspection(run_dir: Path, paper: dict) -> None:
    """Print artifact paths and a quick validation checklist."""
    review_md = run_dir / "final_review.md"
    review_json = run_dir / "review.json"
    trace_jsonl = run_dir / "trace.jsonl"

    print("\n" + "=" * 60)
    print("ARTIFACTS")
    print("=" * 60)
    for path in (review_md, review_json, trace_jsonl):
        status = "ok" if path.is_file() else "MISSING"
        print(f"  [{status}] {path}")

    if not review_json.is_file():
        print("\nCannot inspect parsed review — review.json not found.")
        return

    parsed = json.loads(review_json.read_text())
    human_mean = _human_mean_rating(paper)
    model_rating = parsed.get("rating")

    print("\n" + "=" * 60)
    print("PARSED REVIEW (review.json)")
    print("=" * 60)
    print(f"  rating          : {model_rating}")
    print(f"  human mean      : {human_mean:.2f}  (from {paper['ratings']})")
    if model_rating is not None:
        print(f"  delta vs human  : {model_rating - human_mean:+.2f}")
    for key in _SECTION_KEYS:
        text = parsed.get(key, "")
        preview = text.replace("\n", " ")[:80]
        suffix = "..." if len(text) > 80 else ""
        print(f"  {key:14}: {len(text):4} chars  {preview!r}{suffix}")

    print("\n" + "=" * 60)
    print("CHECKLIST")
    print("=" * 60)
    checks = [
        ("final_review.md exists", review_md.is_file()),
        ("review.json exists", review_json.is_file()),
        ("trace.jsonl exists", trace_jsonl.is_file()),
        ("RATING parsed (1-10)", isinstance(model_rating, int) and 1 <= model_rating <= 10),
        *(
            (f"{key} non-empty", bool(parsed.get(key, "").strip()))
            for key in _SECTION_KEYS
        ),
        (
            "RATING line in final_review.md",
            review_md.is_file() and "RATING:" in review_md.read_text().upper(),
        ),
    ]
    for label, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")

    if trace_jsonl.is_file():
        records = [
            json.loads(line)
            for line in trace_jsonl.read_text().splitlines()
            if line.strip()
        ]
        types = [r["type"] for r in records]
        print(f"\n  trace events    : {', '.join(types)}")
        footer = next((r for r in records if r["type"] == "run_footer"), None)
        if footer:
            print(
                f"  duration        : {footer.get('duration_ms')} ms"
                f"  delegations={footer.get('delegations')}"
                f"  errors={footer.get('delegation_errors')}"
            )


def main() -> None:
    dataset_path = ROOT / "dataset" / "eval_sample_30.json"
    papers = json.loads(dataset_path.read_text())["papers"]
    paper = papers[PAPER_INDEX]
    full_text = paper["paper_text"]
    paper_text = full_text if MAX_CHARS is None else full_text[:MAX_CHARS]

    print(f"Paper ID   : {paper['id']}")
    print(f"Decision   : {paper['decision']}")
    print(f"Ratings    : {paper['ratings']}  (mean={_human_mean_rating(paper):.2f})")
    print(f"Text chars : {len(paper_text)} (of {len(full_text)} total)")
    print(f"Model      : {MODEL}")
    print("-" * 60)

    trace = VerboseTraceLogger(output_dir=OUTPUT_DIR)
    print(f"Output dir : {trace.run_dir}")
    print("Running review (this takes a few minutes)...", flush=True)

    reviewer = MultiAgentReviewer(
        leader_model=MODEL,
        clarity_model=MODEL,
        experiments_model=MODEL,
        impact_model=MODEL,
    )

    review = reviewer.review(paper_text, trace_logger=trace, paper_id=paper["id"])

    print("\n" + "=" * 60)
    print("FINAL REVIEW")
    print("=" * 60)
    print(review)

    _print_inspection(trace.run_dir, paper)


if __name__ == "__main__":
    main()
