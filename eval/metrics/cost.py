"""Metric 5 — cost and inference time.

Sums ``llm_call`` tokens and prices each call via ``eval/prices.json`` (P3).
Wall-clock comes from ``run_footer.duration_ms``. Aggregates mean ± SEM per config.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from metrics.base import Metric
from utils.batch import ROLES, Batch
from utils.cli import add_common_args, load_batch
from utils.prices import DEFAULT_PRICES_PATH, PriceTable, cost_usd, load_prices
from utils.stats import mean_sem

AGENT_ROLE_TO_KEY = {
    "Review Leader": "leader",
    "Clarity and Reproducibility Reviewer": "clarity",
    "Experiments and Methodology Reviewer": "experiments",
    "Impact and Contribution Reviewer": "impact",
}


@dataclass
class RoleTotals:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    llm_calls: int = 0

    def add_call(self, tokens_in: int, tokens_out: int, call_cost: float | None) -> None:
        self.input_tokens += tokens_in
        self.output_tokens += tokens_out
        self.llm_calls += 1
        if call_cost is not None:
            self.cost_usd += call_cost


@dataclass
class RunCost:
    config_id: str
    paper_id: str
    input_tokens: int
    output_tokens: int
    cost_usd: float | None
    time_s: float
    by_role: dict[str, dict[str, float | int | None]]
    missing_price_models: list[str] = field(default_factory=list)


def role_key(agent_role: str | None) -> str | None:
    """Map trace ``agent_role`` labels to config role keys."""
    if agent_role is None:
        return None
    return AGENT_ROLE_TO_KEY.get(agent_role)


def parse_trace(run_dir: Path, prices: PriceTable) -> RunCost:
    """Parse one run's ``trace.jsonl`` into token, cost, and timing totals."""
    path = run_dir / "trace.jsonl"
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    role_totals = {role: RoleTotals() for role in ROLES}
    missing_price_models: set[str] = set()

    input_tokens = 0
    output_tokens = 0
    total_cost = 0.0
    has_all_prices = True
    time_s: float | None = None

    for record in records:
        record_type = record.get("type")
        if record_type == "llm_call":
            tokens_in = int(record["tokens_in"])
            tokens_out = int(record["tokens_out"])
            model = str(record["model"])
            call_cost = cost_usd(model, tokens_in, tokens_out, prices)
            if call_cost is None:
                has_all_prices = False
                missing_price_models.add(model)

            input_tokens += tokens_in
            output_tokens += tokens_out
            if call_cost is not None:
                total_cost += call_cost

            mapped_role = role_key(record.get("agent_role"))
            if mapped_role is not None:
                role_totals[mapped_role].add_call(tokens_in, tokens_out, call_cost)
        elif record_type == "run_footer":
            time_s = float(record["duration_ms"]) / 1000.0

    if time_s is None:
        raise ValueError(f"missing run_footer in trace: {path}")

    by_role: dict[str, dict[str, float | int | None]] = {}
    for role in ROLES:
        totals = role_totals[role]
        role_missing = any(
            record.get("type") == "llm_call"
            and role_key(record.get("agent_role")) == role
            and cost_usd(
                str(record["model"]),
                int(record["tokens_in"]),
                int(record["tokens_out"]),
                prices,
            )
            is None
            for record in records
        )
        by_role[role] = {
            "input_tokens": totals.input_tokens,
            "output_tokens": totals.output_tokens,
            "cost_usd": totals.cost_usd if not role_missing else None,
            "llm_calls": totals.llm_calls,
        }

    return RunCost(
        config_id="",
        paper_id="",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=total_cost if has_all_prices else None,
        time_s=time_s,
        by_role=by_role,
        missing_price_models=sorted(missing_price_models),
    )


def collect_run_costs(batch: Batch, prices: PriceTable) -> dict[str, dict[str, RunCost]]:
    """Compute per-(config, paper) cost rows for replicate 0."""
    run_index = batch.runs_by_config_paper()
    per_run: dict[str, dict[str, RunCost]] = {}

    for config_id in batch.config_ids():
        per_run[config_id] = {}
        for paper_id in batch.paper_ids():
            run = run_index[(config_id, paper_id)]
            parsed = parse_trace(run.run_dir, prices)
            parsed.config_id = config_id
            parsed.paper_id = paper_id
            per_run[config_id][paper_id] = parsed

    return per_run


def _aggregate_role_values(runs: list[RunCost], role: str, field_name: str) -> dict[str, float]:
    values = [
        float(run.by_role[role][field_name])  # type: ignore[arg-type]
        for run in runs
        if run.by_role[role][field_name] is not None
    ]
    return mean_sem(values)


def aggregate_config(runs: list[RunCost]) -> dict[str, Any]:
    """Macro-average per-paper run totals into mean ± SEM for one config."""
    input_tokens = mean_sem([float(run.input_tokens) for run in runs])
    output_tokens = mean_sem([float(run.output_tokens) for run in runs])
    time_s = mean_sem([run.time_s for run in runs])

    cost_values = [run.cost_usd for run in runs if run.cost_usd is not None]
    cost_usd = mean_sem([float(value) for value in cost_values]) if len(cost_values) == len(runs) else None

    by_role: dict[str, Any] = {}
    for role in ROLES:
        by_role[role] = {
            "input_tokens": _aggregate_role_values(runs, role, "input_tokens"),
            "output_tokens": _aggregate_role_values(runs, role, "output_tokens"),
            "cost_usd": _aggregate_role_values(runs, role, "cost_usd")
            if all(run.by_role[role]["cost_usd"] is not None for run in runs)
            else None,
        }

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
        "time_s": time_s,
        "by_role": by_role,
    }


def run_cost_to_dict(run: RunCost) -> dict[str, Any]:
    """Serialize one per-paper run row."""
    return {
        "input_tokens": run.input_tokens,
        "output_tokens": run.output_tokens,
        "cost_usd": run.cost_usd,
        "time_s": run.time_s,
        "by_role": run.by_role,
        "missing_price_models": run.missing_price_models,
    }


class CostMetric(Metric):
    """Token, USD cost, and wall-clock time per run and per config."""

    metric_name = "cost"

    def __init__(self, batch: Batch, *, prices_path: Path | None = None) -> None:
        super().__init__(batch)
        self.prices_path = prices_path or DEFAULT_PRICES_PATH
        self.prices = load_prices(self.prices_path)

    def run(self) -> dict[str, Any]:
        per_run_raw = collect_run_costs(self.batch, self.prices)

        per_run: dict[str, dict[str, Any]] = {}
        per_config: dict[str, Any] = {}
        missing_models: set[str] = set()
        for config_id, runs_by_paper in per_run_raw.items():
            per_run[config_id] = {
                paper_id: run_cost_to_dict(run) for paper_id, run in sorted(runs_by_paper.items())
            }
            per_config[config_id] = aggregate_config(list(runs_by_paper.values()))
            for run in runs_by_paper.values():
                missing_models.update(run.missing_price_models)

        return {
            "prices_path": str(self.prices_path),
            "missing_price_models": sorted(missing_models),
            "per_run": per_run,
            "per_config": per_config,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Metric 5: cost and inference time")
    add_common_args(parser)
    parser.add_argument(
        "--prices",
        type=Path,
        default=DEFAULT_PRICES_PATH,
        help="OpenRouter price table JSON (USD per 1M tokens)",
    )
    parser.add_argument(
        "--refresh-prices",
        action="store_true",
        help="Fetch OpenRouter list prices and overwrite --prices before computing",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for Metric 5."""
    args = build_parser().parse_args(argv)
    if args.refresh_prices:
        from utils.prices import refresh_prices_file

        refreshed = refresh_prices_file(args.prices)
        print(f"refreshed {refreshed}")

    batch = load_batch(args, load_dotenv_file=False)
    metric = CostMetric(batch, prices_path=args.prices)
    output_path = metric.write()
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
