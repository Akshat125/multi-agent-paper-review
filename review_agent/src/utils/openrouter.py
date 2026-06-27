"""OpenRouter helpers shared by the reviewer and eval metric clients."""

from __future__ import annotations

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
QWEN_NO_THINK_SUFFIX = " /no_think"

# Pin each pool model to a controlled, ordered set of OpenRouter providers with
# open-ended fallback disabled. Without this, OpenRouter picks the cheapest
# provider per call, which silently (a) varies quantization (fp8 vs bf16) and
# (b) drops qwen to a 40k-context backend that can truncate a long paper. Every
# provider listed below is fp8 and >=131k context AND advertises ``tools``
# support (required so the leader can delegate via function calls), so quant,
# context, and tool-calling stay fixed across runs while still surviving a
# single provider outage. Keys are bare OpenRouter model slugs; values are
# provider-routing blocks sent as ``provider``.
PROVIDER_ROUTING: dict[str, dict] = {
    "qwen/qwen3-32b": {
        "order": ["SiliconFlow", "Alibaba"],
        "allow_fallbacks": False,
    },
    "mistralai/mistral-small-3.2-24b-instruct": {
        "order": ["Venice", "DeepInfra"],
        "allow_fallbacks": False,
    },
    "meta-llama/llama-3.3-70b-instruct": {
        "order": ["DeepInfra", "Nebius", "AkashML"],
        "allow_fallbacks": False,
    },
}


def normalize_openrouter_model(model_name: str) -> str:
    """Return the ``openrouter/<slug>`` form CrewAI expects."""
    return model_name if model_name.startswith("openrouter/") else f"openrouter/{model_name}"


def provider_routing_for(model_name: str) -> dict | None:
    """Return the pinned OpenRouter provider-routing block for ``model_name``."""
    slug = model_name.split("openrouter/", 1)[-1]
    return PROVIDER_ROUTING.get(slug)


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
    provider = provider_routing_for(model_name)
    if provider is not None:
        kwargs["extra_body"] = {"provider": provider}
    return kwargs
