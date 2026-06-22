"""Unit tests for TraceLogger."""

from __future__ import annotations

import json

from src.utils import TraceLogger
from src.utils.trace_logger import preview


def _read_records(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_log_writes_flat_records_with_seq(tmp_path):
    logger = TraceLogger(output_dir=tmp_path, run_name="run1")

    logger.log("delegation_finished", expert_role="Clarity", status="ok")
    logger.log("leader_completion", output_chars=42)

    records = _read_records(logger.trace_path)
    assert [r["seq"] for r in records] == [0, 1]
    assert [r["type"] for r in records] == ["delegation_finished", "leader_completion"]
    assert records[0]["expert_role"] == "Clarity"
    assert records[1]["output_chars"] == 42
    assert all("ts" in r for r in records)


def test_save_review_writes_file_only(tmp_path):
    logger = TraceLogger(output_dir=tmp_path, run_name="run2")

    review_path = logger.save_review("THE FINAL REVIEW")

    assert review_path.read_text() == "THE FINAL REVIEW"
    assert not logger.trace_path.exists()
    assert logger.run_dir.name == "run2"


def test_save_review_json_writes_structured_file(tmp_path):
    logger = TraceLogger(output_dir=tmp_path, run_name="run4")
    data = {
        "summary": "s",
        "strengths": "st",
        "weaknesses": "w",
        "questions": "q",
        "rating": 7,
    }

    path = logger.save_review_json(data)

    assert path == logger.review_json_path
    loaded = json.loads(path.read_text())
    assert loaded == data


def test_preview_truncates_and_single_lines():
    assert preview("a\nb  c", limit=100) == "a b c"
    long = "x" * 600
    out = preview(long, limit=500)
    assert len(out) == 503 and out.endswith("...")


def test_log_serializes_non_json_values(tmp_path):
    logger = TraceLogger(output_dir=tmp_path, run_name="run3")

    class Weird:
        def __str__(self) -> str:
            return "weird-object"

    logger.log("misc", value=Weird())
    records = _read_records(logger.trace_path)
    assert records[0]["value"] == "weird-object"
