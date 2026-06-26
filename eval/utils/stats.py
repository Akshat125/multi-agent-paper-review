"""Lightweight numeric helpers shared across eval metrics."""

from __future__ import annotations

import hashlib
import statistics


def mean(values: list[float]) -> float:
    """Arithmetic mean; returns 0.0 for an empty list."""
    return sum(values) / len(values) if values else 0.0


def sem(values: list[float]) -> float:
    """Standard error of the mean; 0.0 for fewer than two values."""
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values) / len(values) ** 0.5


def mean_sem(values: list[float]) -> dict[str, float]:
    """Return macro-averaged mean and SEM for a list of per-paper values."""
    return {"mean": mean(values), "sem": sem(values), "n": float(len(values))}


def derive_seed(base: int, *parts: object) -> int:
    """Deterministically derive a child seed from a base seed and extra identifiers.

    Stable across processes and machines, unlike the builtin ``hash`` (which is
    salted per-process unless PYTHONHASHSEED is pinned). Stays within numpy's
    uint32 range.
    """
    key = "|".join(str(part) for part in (base, *parts))
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")
