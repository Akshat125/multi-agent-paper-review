"""OpenRouter helpers shared by the reviewer and eval metric clients."""

from __future__ import annotations

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
QWEN_NO_THINK_SUFFIX = " /no_think"


def normalize_openrouter_model(model_name: str) -> str:
    """Return the ``openrouter/<slug>`` form CrewAI expects."""
    return model_name if model_name.startswith("openrouter/") else f"openrouter/{model_name}"


def append_qwen_no_think(text: str, model_name: str) -> str:
    """Append Qwen3's per-turn thinking disable token when needed.

    OpenRouter's ``qwen/qwen3-32b`` is a hybrid thinking model. Qwen's
    documented ``/no_think`` suffix disables thinking for that turn.
    """
    if "qwen" not in model_name.lower() or "/no_think" in text:
        return text
    return text.rstrip() + QWEN_NO_THINK_SUFFIX


def build_openrouter_llm_kwargs(
    model_name: str,
    *,
    api_key: str | None = None,
    temperature: float = 0.0,
) -> dict:
    """Keyword arguments for ``crewai.LLM`` pointed at OpenRouter."""
    kwargs: dict = {
        "model": normalize_openrouter_model(model_name),
        "base_url": OPENROUTER_BASE_URL,
        "temperature": temperature,
    }
    if api_key is not None:
        kwargs["api_key"] = api_key
    return kwargs
