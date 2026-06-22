"""OpenRouter LLM access and JSON parsing shared across eval metrics.

Wraps CrewAI for live judge/alignment calls; ``extract_json`` pulls structured
payloads out of fenced or bare JSON in model responses.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Protocol

from crewai import LLM

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


class LLMClient(Protocol):
    """Minimal interface metrics use so tests can inject fake LLM backends."""

    def call(self, prompt: str) -> str: ...


def openrouter_model(model_name: str) -> str:
    """Normalize a model slug to the ``openrouter/…`` form CrewAI expects."""
    return model_name if model_name.startswith("openrouter/") else f"openrouter/{model_name}"


class OpenRouterLLM:
    """Live OpenRouter client used by metric CLIs when no fake backend is injected."""

    def __init__(self, model: str, api_key: str | None = None) -> None:
        self.model = model
        self._llm = LLM(
            model=openrouter_model(model),
            base_url=OPENROUTER_BASE_URL,
            api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
        )

    def call(self, prompt: str) -> str:
        """Send a single-turn prompt and return the model's text response."""
        response = self._llm.call(prompt)
        return response if isinstance(response, str) else str(response)

    def judge(self, prompt: str) -> str:
        """Same as ``call`` — win-rate code uses a judge-style name."""
        return self.call(prompt)


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
