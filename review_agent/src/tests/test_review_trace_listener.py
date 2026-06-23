"""Unit tests for ReviewTraceListener (event objects faked, no CrewAI run)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from src.utils import ReviewTraceListener, TraceLogger


class FakeBus:
    """Minimal stand-in for the CrewAI event bus."""

    def __init__(self) -> None:
        self.handlers: dict = {}
        self.flushed = False

    def register_handler(self, event_type, handler):
        self.handlers.setdefault(event_type, []).append(handler)

    def off(self, event_type, handler):
        self.handlers.get(event_type, []).remove(handler)

    def flush(self, timeout=None):
        self.flushed = True
        return True

    def emit(self, event):
        for handler in self.handlers.get(type(event), []):
            handler(None, event)


def _records(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _tool_finished(**kw):
    from crewai.events.types.tool_usage_events import ToolUsageFinishedEvent

    now = datetime.now(timezone.utc)
    defaults = dict(
        tool_name="delegate_work_to_coworker",
        tool_args={"coworker": "Clarity and Reproducibility Reviewer", "task": "Assess clarity"},
        agent_role="Review Leader",
        started_at=now,
        finished_at=now + timedelta(seconds=2),
        output="clarity feedback here",
    )
    defaults.update(kw)
    return ToolUsageFinishedEvent(**defaults)


def test_delegation_event_logged(tmp_path):
    logger = TraceLogger(output_dir=tmp_path, run_name="r")
    bus = FakeBus()
    listener = ReviewTraceListener(logger, bus=bus).attach()

    bus.emit(_tool_finished())

    rec = _records(logger.trace_path)[0]
    assert rec["type"] == "delegation_finished"
    assert rec["expert_role"] == "Clarity and Reproducibility Reviewer"
    assert rec["task"] == "Assess clarity"
    assert rec["output"] == "clarity feedback here"
    assert rec["status"] == "ok"
    assert rec["duration_ms"] == 2000.0
    assert listener.counts["delegations"] == 1


def test_display_name_delegation_tool_not_matched(tmp_path):
    """Events carry sanitized names; display names must not be matched."""
    logger = TraceLogger(output_dir=tmp_path, run_name="r")
    bus = FakeBus()
    ReviewTraceListener(logger, bus=bus).attach()

    bus.emit(_tool_finished(tool_name="Delegate work to coworker"))

    assert not logger.trace_path.exists() or _records(logger.trace_path) == []


def test_expert_completion_not_logged_separately(tmp_path):
    logger = TraceLogger(output_dir=tmp_path, run_name="r")
    listener = ReviewTraceListener(logger, bus=FakeBus())

    event = SimpleNamespace(
        agent=SimpleNamespace(role="Impact and Contribution Reviewer"),
        output="impact feedback",
        emission_sequence=7,
    )
    listener._on_agent_completed(None, event)

    assert not logger.trace_path.exists()


def test_leader_completion_logged(tmp_path):
    logger = TraceLogger(output_dir=tmp_path, run_name="r")
    listener = ReviewTraceListener(logger, bus=FakeBus(), leader_role="Review Leader")

    event = SimpleNamespace(
        agent=SimpleNamespace(role="Review Leader"),
        output="final peer review text",
        emission_sequence=34,
    )
    listener._on_agent_completed(None, event)

    rec = _records(logger.trace_path)[0]
    assert rec["type"] == "leader_completion"
    assert rec["output_chars"] == len("final peer review text")
    assert rec["emit_seq"] == 34


def test_context_manager_attaches_and_detaches(tmp_path):
    logger = TraceLogger(output_dir=tmp_path, run_name="r")
    bus = FakeBus()

    with ReviewTraceListener(logger, bus=bus):
        bus.emit(_tool_finished())
    bus.emit(_tool_finished())  # after exit: ignored

    assert len(_records(logger.trace_path)) == 1
