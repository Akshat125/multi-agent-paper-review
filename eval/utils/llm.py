"""OpenRouter LLM access and JSON parsing shared across eval metrics.

Wraps CrewAI for live judge/alignment calls; ``extract_json`` pulls structured
payloads out of fenced or bare JSON in model responses.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Protocol

from crewai import LLM

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "review_agent") not in sys.path:
    sys.path.insert(0, str(ROOT / "review_agent"))

from src.utils.openrouter import build_openrouter_llm_kwargs  # noqa: E402

JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


class LLMClient(Protocol):
    """Minimal interface metrics use so tests can inject fake LLM backends."""

    def call(self, prompt: str) -> str: ...


def openrouter_model(model_name: str) -> str:
    """Normalize a model slug to the ``openrouter/…`` form CrewAI expects."""
    return model_name if model_name.startswith("openrouter/") else f"openrouter/{model_name}"


class OpenRouterLLM:
    """Live OpenRouter client used by metric CLIs when no fake backend is injected.

    Temperature defaults to ``0.0`` so judge/alignment calls are as reproducible as
    the provider allows (comment_recall's variation comes from its shuffle passes,
    not sampling).
    """

    def __init__(self, model: str, api_key: str | None = None, *, temperature: float = 0.0) -> None:
        self.model = model
        self.temperature = temperature
        self._llm = LLM(
            **build_openrouter_llm_kwargs(
                model,
                api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
                temperature=temperature,
            )
        )

    def call(self, prompt: str) -> str:
        """Send a single-turn prompt and return the model's text response."""
        response = self._llm.call(prompt)
        return response if isinstance(response, str) else str(response)


def extract_json(text: str) -> dict[str, Any]:
    """Parse the last valid JSON object from an LLM response.

    Tries fenced ```json blocks first, then falls back to parsing the whole body.
    """
    blocks = JSON_BLOCK_RE.findall(text)
    for block in reversed(blocks):
        try:
            payload = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    try:
        payload = json.loads(text.strip())
    except json.JSONDecodeError as exc:
        raise ValueError("could not parse JSON from LLM response") from exc
    if not isinstance(payload, dict):
        raise ValueError("LLM JSON must be an object")
    return payload
