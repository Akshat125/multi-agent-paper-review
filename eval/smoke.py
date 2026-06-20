"""Smoke-test: run the multi-agent reviewer on one paper from the eval set.

Usage (from the project root with the poetry venv active):
    python eval/smoke.py
"""

from __future__ import annotations

import json
import os
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

from src.agents.reviewer import MultiAgentReviewer
from src.utils import TraceLogger


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
        else:
            print(f"[{event_type}]", flush=True)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MODEL = "qwen/qwen3-8b"
MAX_CHARS = 8_000
PAPER_INDEX = 0

# ---------------------------------------------------------------------------
# Load paper
# ---------------------------------------------------------------------------

dataset_path = ROOT / "dataset" / "eval_sample_30.json"
papers = json.loads(dataset_path.read_text())["papers"]
paper = papers[PAPER_INDEX]
paper_text = paper["paper_text"][:MAX_CHARS]

print(f"Paper ID   : {paper['id']}")
print(f"Decision   : {paper['decision']}")
print(f"Ratings    : {paper['ratings']}")
print(f"Text chars : {len(paper_text)} (of {len(paper['paper_text'])} total)")
print(f"Model      : {MODEL}")
print("-" * 60)

trace = VerboseTraceLogger(output_dir=OUTPUT_DIR)
print(f"Trace log  : {trace.trace_path}")
print("Running review (this takes a few minutes)...", flush=True)

reviewer = MultiAgentReviewer(
    leader_model=MODEL,
    clarity_model=MODEL,
    experiments_model=MODEL,
    impact_model=MODEL,
)

review = reviewer.review(paper_text, trace_logger=trace, paper_id=paper["id"])

print(f"\nFull trace saved to: {trace.run_dir}")
print("\n" + "=" * 60)
print("FINAL REVIEW")
print("=" * 60)
print(review)
