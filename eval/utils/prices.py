"""OpenRouter price table loading and refresh (P3).

``eval/prices.json`` stores USD per 1M tokens::

    { "<model_id>": {"in": <usd_per_1M_in>, "out": <usd_per_1M_out>} }

Use :func:`fetch_openrouter_prices` to rebuild the table from OpenRouter's public
``GET /api/v1/models`` endpoint (pricing is per token there; we convert to per 1M).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from utils.run_set import PROJECT_ROOT

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
DEFAULT_PRICES_PATH = PROJECT_ROOT / "eval" / "prices.json"
PriceTable = dict[str, dict[str, float]]


def normalize_model_id(model: str) -> str:
    """Strip the ``openrouter/`` prefix so ids match trace ``model`` fields."""
    return model.removeprefix("openrouter/")


def load_prices(path: Path | None = None) -> PriceTable:
    """Load the price table from ``eval/prices.json`` (or ``path``)."""
    price_path = path or DEFAULT_PRICES_PATH
    if not price_path.is_file():
        raise FileNotFoundError(f"missing price table: {price_path}")
    raw = json.loads(price_path.read_text(encoding="utf-8"))
    return _normalize_price_table(raw)


def lookup_prices(model: str, prices: PriceTable) -> dict[str, float] | None:
    """Return ``{in, out}`` USD-per-1M rates for a model, or ``None`` if unknown."""
    model_id = normalize_model_id(model)
    entry = prices.get(model_id)
    if entry is None:
        entry = prices.get(f"openrouter/{model_id}")
    return entry


def cost_usd(
    model: str,
    tokens_in: int,
    tokens_out: int,
    prices: PriceTable,
) -> float | None:
    """Price one LLM call from token counts and the per-1M rate table."""
    entry = lookup_prices(model, prices)
    if entry is None:
        return None
    return (tokens_in / 1_000_000) * entry["in"] + (tokens_out / 1_000_000) * entry["out"]


def fetch_openrouter_prices() -> PriceTable:
    """Download current OpenRouter list prices and convert to USD per 1M tokens."""
    request = urllib.request.Request(
        OPENROUTER_MODELS_URL,
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"failed to fetch OpenRouter models: {exc}") from exc

    table: PriceTable = {}
    for model in payload.get("data", []):
        model_id = model.get("id")
        pricing = model.get("pricing") or {}
        prompt = pricing.get("prompt")
        completion = pricing.get("completion")
        if not model_id or prompt is None or completion is None:
            continue
        table[model_id] = {
            "in": float(prompt) * 1_000_000,
            "out": float(completion) * 1_000_000,
        }
    if not table:
        raise RuntimeError("OpenRouter models response contained no priced models")
    return table


def write_prices(prices: PriceTable, path: Path | None = None) -> Path:
    """Persist a price table sorted by model id."""
    price_path = path or DEFAULT_PRICES_PATH
    price_path.parent.mkdir(parents=True, exist_ok=True)
    ordered = {model_id: prices[model_id] for model_id in sorted(prices)}
    price_path.write_text(
        json.dumps(ordered, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return price_path


def refresh_prices_file(path: Path | None = None) -> Path:
    """Fetch OpenRouter prices and overwrite ``eval/prices.json``."""
    return write_prices(fetch_openrouter_prices(), path)


def _normalize_price_table(raw: Any) -> PriceTable:
    if not isinstance(raw, dict):
        raise ValueError("prices.json must be an object keyed by model id")
    table: PriceTable = {}
    for model_id, entry in raw.items():
        if not isinstance(entry, dict) or "in" not in entry or "out" not in entry:
            raise ValueError(f"invalid price entry for {model_id!r}")
        table[str(model_id)] = {"in": float(entry["in"]), "out": float(entry["out"])}
    return table
