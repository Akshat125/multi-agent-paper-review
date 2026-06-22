"""CrewAI event-bus listener for multi-agent review traces.

One record per expert round-trip (``delegation_finished``) and one for the leader's
final synthesis (``leader_completion``). ``llm_call`` records stay separate
for token/cost accounting.

Why a custom listener instead of ``BaseEventListener``: the event bus is a
global singleton whose handlers persist across runs. This class keeps explicit
handler references and supports :meth:`detach` / context-manager use.
"""

from __future__ import annotations

from typing import Any

from crewai.events.event_bus import crewai_event_bus
from crewai.events.types.agent_events import AgentExecutionCompletedEvent
from crewai.events.types.llm_events import LLMCallCompletedEvent
from crewai.events.types.tool_usage_events import (
    ToolUsageErrorEvent,
    ToolUsageFinishedEvent,
)
from crewai.utilities.string_utils import sanitize_tool_name

from .trace_logger import TraceLogger, preview

_DELEGATION_TOOLS = {
    sanitize_tool_name("Delegate work to coworker"),
    sanitize_tool_name("Ask question to coworker"),
}


def _duration_ms(event: Any) -> float | None:
    start = getattr(event, "started_at", None)
    end = getattr(event, "finished_at", None)
    if start is None or end is None:
        return None
    return round((end - start).total_seconds() * 1000, 1)


def _coworker_and_task(tool_args: Any) -> tuple[str | None, str | None]:
    if not isinstance(tool_args, dict):
        return None, None
    coworker = tool_args.get("coworker")
    task = tool_args.get("task") or tool_args.get("question")
    return coworker, task


class ReviewTraceListener:
    """Subscribe to review-relevant CrewAI events and log them as JSONL."""

    def __init__(
        self,
        logger: TraceLogger,
        bus: Any = None,
        leader_role: str = "Review Leader",
    ) -> None:
        self.logger = logger
        self.bus = bus or crewai_event_bus
        self.leader_role = leader_role
        self.counts = {"delegations": 0, "delegation_errors": 0}
        self._handlers = [
            (ToolUsageFinishedEvent, self._on_tool_finished),
            (ToolUsageErrorEvent, self._on_tool_error),
            (AgentExecutionCompletedEvent, self._on_agent_completed),
            (LLMCallCompletedEvent, self._on_llm_completed),
        ]

    def attach(self) -> ReviewTraceListener:
        for event_type, handler in self._handlers:
            self.bus.register_handler(event_type, handler)
        return self

    def detach(self) -> None:
        for event_type, handler in self._handlers:
            self.bus.off(event_type, handler)

    def flush(self, timeout: float | None = 30.0) -> bool:
        return self.bus.flush(timeout=timeout)

    def __enter__(self) -> ReviewTraceListener:
        return self.attach()

    def __exit__(self, *exc: object) -> None:
        self.detach()

    def _on_tool_finished(self, _source: Any, event: ToolUsageFinishedEvent) -> None:
        if event.tool_name not in _DELEGATION_TOOLS:
            return
        expert_role, task = _coworker_and_task(event.tool_args)
        output = str(event.output)
        self.counts["delegations"] += 1
        self.logger.log(
            "delegation_finished",
            emit_seq=getattr(event, "emission_sequence", None),
            expert_role=expert_role,
            task=preview(task) if task else None,
            output=output,
            output_chars=len(output),
            duration_ms=_duration_ms(event),
            status="ok",
        )

    def _on_tool_error(self, _source: Any, event: ToolUsageErrorEvent) -> None:
        if event.tool_name not in _DELEGATION_TOOLS:
            return
        expert_role, task = _coworker_and_task(event.tool_args)
        self.counts["delegation_errors"] += 1
        self.logger.log(
            "delegation_error",
            emit_seq=getattr(event, "emission_sequence", None),
            expert_role=expert_role,
            task=preview(task) if task else None,
            error=preview(event.error),
            status="error",
        )

    def _on_agent_completed(
        self, _source: Any, event: AgentExecutionCompletedEvent
    ) -> None:
        role = getattr(event.agent, "role", None)
        if role != self.leader_role:
            return  # expert output is captured in delegation
        output = str(event.output)
        self.logger.log(
            "leader_completion",
            emit_seq=getattr(event, "emission_sequence", None),
            output=preview(output),
            output_chars=len(output),
        )

    def _on_llm_completed(self, _source: Any, event: LLMCallCompletedEvent) -> None:
        usage = event.usage or {}
        self.logger.log(
            "llm_call",
            emit_seq=getattr(event, "emission_sequence", None),
            agent_role=getattr(event, "agent_role", None),
            model=event.model,
            tokens_in=usage.get("prompt_tokens"),
            tokens_out=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
        )
