"""Base class for eval metrics."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from utils.results import write_metric
from utils.run_set import RunSet


class Metric(ABC):
    """Common contract for eval metrics: compute a payload and write JSON output.

    Subclasses own all metric-specific logic; this base only wires ``run`` to
    ``eval/results/<run-set>/<name>.json`` via ``write_metric``.
    """

    metric_name: str

    def __init__(self, run_set: RunSet) -> None:
        self.run_set = run_set

    @abstractmethod
    def run(self) -> dict[str, Any]:
        """Compute the metric payload (excluding the write envelope)."""

    def write(self, payload: dict[str, Any] | None = None) -> Path:
        """Run if needed and persist this metric's JSON under the run-set."""
        data = payload if payload is not None else self.run()
        return write_metric(self.run_set, self.metric_name, data)
