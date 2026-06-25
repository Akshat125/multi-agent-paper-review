"""Base class for eval metrics."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from utils.batch import Batch, write_metric


class Metric(ABC):
    """Common contract for batch metrics: compute a payload and write JSON output.

    Subclasses own all metric-specific logic; this base only wires ``run`` to
    ``eval/results/<batch>/<name>.json`` via ``write_metric``.
    """

    metric_name: str

    def __init__(self, batch: Batch) -> None:
        self.batch = batch

    @abstractmethod
    def run(self) -> dict[str, Any]:
        """Compute the metric payload (excluding the write envelope)."""

    def write(self, payload: dict[str, Any] | None = None) -> Path:
        """Run if needed and persist this metric's JSON under the batch."""
        data = payload if payload is not None else self.run()
        return write_metric(self.batch, self.metric_name, data)
