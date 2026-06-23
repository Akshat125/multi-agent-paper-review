"""Tests for Metric 5 cost and inference time."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from metrics.cost import CostMetric, aggregate_config, parse_trace, role_key
from utils.batch import Batch
from utils.prices import cost_usd, load_prices, normalize_model_id


@pytest.fixture
def tiny_prices(tmp_path: Path) -> Path:
    payload = {
        "model-a": {"in": 1.0, "out": 2.0},
        "model-b": {"in": 10.0, "out": 20.0},
    }
    path = tmp_path / "prices.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def write_cost_trace(run_dir: Path, *, model: str, duration_ms: float = 2000.0) -> None:
    records = [
        {
            "type": "llm_call",
            "agent_role": "Review Leader",
            "model": model,
            "tokens_in": 1000,
            "tokens_out": 100,
            "total_tokens": 1100,
        },
        {
            "type": "llm_call",
            "agent_role": "Clarity and Reproducibility Reviewer",
            "model": model,
            "tokens_in": 200,
            "tokens_out": 50,
            "total_tokens": 250,
        },
        {
            "type": "llm_call",
            "agent_role": "Experiments and Methodology Reviewer",
            "model": model,
            "tokens_in": 200,
            "tokens_out": 50,
            "total_tokens": 250,
        },
        {
            "type": "llm_call",
            "agent_role": "Impact and Contribution Reviewer",
            "model": model,
            "tokens_in": 200,
            "tokens_out": 50,
            "total_tokens": 250,
        },
        {"type": "run_footer", "duration_ms": duration_ms},
    ]
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "trace.jsonl").write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )


def test_role_key_maps_known_labels():
    assert role_key("Review Leader") == "leader"
    assert role_key("Unknown Agent") is None


def test_normalize_model_id_strips_openrouter_prefix():
    assert normalize_model_id("openrouter/qwen/qwen3-8b") == "qwen/qwen3-8b"


def test_cost_usd_uses_per_million_rates(tiny_prices: Path):
    prices = load_prices(tiny_prices)
    assert cost_usd("model-a", 1_000_000, 500_000, prices) == pytest.approx(2.0)


def test_parse_trace_sums_tokens_and_cost(tmp_path: Path, tiny_prices: Path):
    run_dir = tmp_path / "run"
    write_cost_trace(run_dir, model="model-a")
    prices = load_prices(tiny_prices)

    result = parse_trace(run_dir, prices)

    assert result.input_tokens == 1600
    assert result.output_tokens == 250
    assert result.time_s == 2.0
    assert result.cost_usd == pytest.approx(0.0021)
    assert result.by_role["leader"]["input_tokens"] == 1000
    assert result.by_role["clarity"]["output_tokens"] == 50


def test_cost_metric_end_to_end(tiny_batch: Batch, tiny_prices: Path, tmp_path: Path):
    for config_id in ("All-A", "All-B"):
        for paper_id in ("paper_a", "paper_b"):
            run_dir = tmp_path / "eval" / "outputs" / f"{config_id}_{paper_id}"
            model = "model-a" if config_id == "All-A" else "model-b"
            write_cost_trace(run_dir, model=model, duration_ms=1000.0 if paper_id == "paper_a" else 3000.0)

    metric = CostMetric(tiny_batch, prices_path=tiny_prices)
    payload = metric.run()

    all_a = payload["per_config"]["All-A"]
    all_b = payload["per_config"]["All-B"]

    assert all_a["input_tokens"]["mean"] == 1600.0
    assert all_a["output_tokens"]["mean"] == 250.0
    assert all_a["time_s"]["mean"] == 2.0
    assert all_a["cost_usd"]["mean"] == pytest.approx(0.0021)
    assert all_b["cost_usd"]["mean"] == pytest.approx(0.021)
    assert payload["missing_price_models"] == []


def test_aggregate_config_handles_partial_cost():
    from metrics.cost import RunCost

    runs = [
        RunCost(
            config_id="cfg",
            paper_id="p1",
            input_tokens=100,
            output_tokens=10,
            cost_usd=1.0,
            time_s=1.0,
            by_role={
                "leader": {"input_tokens": 100, "output_tokens": 10, "cost_usd": 1.0, "llm_calls": 1},
                "clarity": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "llm_calls": 0},
                "experiments": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "llm_calls": 0},
                "impact": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "llm_calls": 0},
            },
        ),
        RunCost(
            config_id="cfg",
            paper_id="p2",
            input_tokens=200,
            output_tokens=20,
            cost_usd=None,
            time_s=2.0,
            by_role={
                "leader": {"input_tokens": 200, "output_tokens": 20, "cost_usd": None, "llm_calls": 1},
                "clarity": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "llm_calls": 0},
                "experiments": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "llm_calls": 0},
                "impact": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "llm_calls": 0},
            },
            missing_price_models=["unknown/model"],
        ),
    ]

    aggregated = aggregate_config(runs)
    assert aggregated["cost_usd"] is None
    assert aggregated["time_s"]["mean"] == 1.5
