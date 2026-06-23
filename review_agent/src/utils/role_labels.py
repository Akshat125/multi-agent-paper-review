"""Canonical agent role labels for trace.jsonl and CrewAI agents."""

from __future__ import annotations

ROLE_LABELS: dict[str, str] = {
    "leader": "Review Leader",
    "clarity": "Clarity and Reproducibility Reviewer",
    "experiments": "Experiments and Methodology Reviewer",
    "impact": "Impact and Contribution Reviewer",
}

AGENT_ROLE_TO_KEY: dict[str, str] = {label: key for key, label in ROLE_LABELS.items()}
