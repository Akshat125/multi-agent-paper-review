"""Structured JSONL logging for review runs.

Writes one JSON object per line to ``<output_dir>/<run>/trace.jsonl``. Records
are flat dicts with a monotonic ``seq``, a timestamp, an event ``type``, and
event-specific fields. The actual capture of multi-agent events (delegations,
expert completions, LLM calls) is done by :class:`ReviewTraceListener`, which
subscribes to the CrewAI event bus and calls :meth:`log` here.

This separation keeps the sink (this class) dumb and thread-safe -- CrewAI runs
sync event handlers in a thread pool, so writes are guarded by a lock.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def preview(text: Any, limit: int = 500) -> str:
    """Single-line, length-capped preview of a value for compact logging."""
    s = text if isinstance(text, str) else str(text)
    s = " ".join(s.split())
    return s if len(s) <= limit else s[:limit] + "..."


class TraceLogger:
    """Append-only JSONL sink for a single review run."""

    def __init__(
        self, output_dir: str | Path = "outputs", run_name: str | None = None
    ) -> None:
        ts = run_name or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.run_dir = Path(output_dir) / ts
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.trace_path = self.run_dir / "trace.jsonl"
        self.review_path = self.run_dir / "final_review.md"
        self._seq = 0
        self._lock = threading.Lock()

    def log(self, event_type: str, **fields: Any) -> None:
        """Append one record. Thread-safe (handlers fire from a thread pool)."""
        with self._lock:
            record = {
                "seq": self._seq,
                "ts": datetime.now(timezone.utc).isoformat(),
                "type": event_type,
                **fields,
            }
            self._seq += 1
            with self.trace_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    def save_review(self, text: str) -> Path:
        """Write the full review text; trace record is ``leader_completion``."""
        self.review_path.write_text(text, encoding="utf-8")
        return self.review_path
