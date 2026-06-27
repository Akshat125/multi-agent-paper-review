"""OpenRouter LLM access and JSON parsing shared across eval metrics.

Wraps CrewAI for live judge/alignment calls; ``extract_json`` pulls structured
payloads out of fenced or bare JSON in model responses.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Protocol

from crewai import LLM

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "review_agent") not in sys.path:
    sys.path.insert(0, str(ROOT / "review_agent"))

from src.utils.openrouter import build_openrouter_llm_kwargs  # noqa: E402

JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)

DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_BACKOFF_CAP = 30.0


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

    ``call`` retries transient failures (transport errors, 429s, 5xx) with capped
    exponential backoff so a single blip several hours into a long sequential run
    doesn't abort it. Any exception from the underlying client is treated as
    retryable; non-transient errors (e.g. auth) simply burn the bounded attempts
    and then surface. The retry is internal so the ``LLMClient`` protocol signature
    (``call(self, prompt: str) -> str``) is unchanged and fake backends still work.
    """

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        *,
        temperature: float = 0.0,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        backoff_cap: float = DEFAULT_BACKOFF_CAP,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_attempts = max(1, max_attempts)
        self.backoff_cap = backoff_cap
        self._sleep = sleep
        self._llm = LLM(
            **build_openrouter_llm_kwargs(
                model,
                api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
                temperature=temperature,
            )
        )

    def call(self, prompt: str) -> str:
        """Send a single-turn prompt and return the model's text response.

        Retries up to ``max_attempts`` times with ``min(2 ** attempt, backoff_cap)``
        seconds of backoff between attempts before re-raising the last error.
        """
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = self._llm.call(prompt)
                return response if isinstance(response, str) else str(response)
            except Exception as exc:  # noqa: BLE001 - retry transport/5xx/429 alike
                last_error = exc
                if attempt < self.max_attempts:
                    self._sleep(min(2 ** attempt, self.backoff_cap))
        raise RuntimeError(
            f"LLM call failed after {self.max_attempts} attempts "
            f"(model={self.model}): {last_error!r}"
        ) from last_error


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
