"""Metric 1 — LLM-as-judge side-by-side win-rate.

Compares configs head-to-head on each paper using out-of-suite judges.
Position-debiased (both orders) and aggregated into per-config win rates.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from prompts.win_rate import (
    DEFAULT_DIMENSIONS,
    RUBRIC_TEXT,
    RUBRIC_VERSION,
    build_comparison_prompt,
    dimension_labels,
)
from metrics.base import Metric
from utils.batch import Batch, RunArtifacts, unordered_pairs
from utils.cli import add_common_args, load_batch
from utils.llm import OpenRouterLLM, extract_json
from utils.stats import mean

DEFAULT_JUDGES: tuple[str, ...] = (
    "openai/gpt-5-mini",
    "deepseek/deepseek-v3.2",
)

THOUGHT_RE = re.compile(r"THOUGHT:\s*(.*?)\s*REVIEW COMPARISON JSON:", re.DOTALL | re.IGNORECASE)
BETTER_ASSISTANT_RE = re.compile(
    r'"(?P<label>[^"]+) Better Assistant":\s*"(?P<verdict>A|B|Tie)"',
    re.IGNORECASE,
)


class JudgeClient(Protocol):
    """LLM backend that returns a side-by-side judge verdict string."""

    def judge(self, prompt: str) -> str: ...


@dataclass(frozen=True)
class RawComparison:
    """One debiased judge call: one config pair, paper, judge, and presentation order."""
    config_a: str
    config_b: str
    paper_id: str
    judge_model: str
    assistant_a_config: str
    verdicts: dict[str, str]
    reasons: dict[str, str]
    thought: str
    raw_response: str


def parse_judge_response(
    text: str,
    dimensions: tuple[str, ...] = DEFAULT_DIMENSIONS,
) -> tuple[str, dict[str, str], dict[str, str]]:
    """Parse ScholarPeer H.2 THOUGHT + REVIEW COMPARISON JSON into verdicts."""
    thought_match = THOUGHT_RE.search(text)
    thought = thought_match.group(1).strip() if thought_match else ""

    label_map = {label: key for label, key in dimension_labels(dimensions)}
    verdicts: dict[str, str] = {}
    reasons: dict[str, str] = {}

    try:
        payload = extract_json(text)
    except ValueError:
        payload = {}

    for label, key in label_map.items():
        verdict_raw = payload.get(f"{label} Better Assistant")
        reason_raw = payload.get(f"{label} Reason")
        if verdict_raw is not None:
            verdict = _normalize_verdict(str(verdict_raw))
            if verdict is not None:
                verdicts[key] = verdict
        if reason_raw:
            reasons[key] = str(reason_raw).strip()

    if len(verdicts) < len(label_map):
        for match in BETTER_ASSISTANT_RE.finditer(text):
            label = match.group("label")
            if label not in label_map:
                continue
            key = label_map[label]
            if key not in verdicts:
                verdicts[key] = _normalize_verdict(match.group("verdict")) or "Tie"

    missing = [key for label, key in label_map.items() if key not in verdicts]
    if missing:
        raise ValueError(f"missing or invalid verdict for {missing!r} in judge response")

    return thought, verdicts, reasons


def points_for_config(
    verdict: str,
    favored_config: str,
    config_a: str,
    assistant_a_config: str,
) -> float:
    """Convert an A/B/Tie verdict into points for one config, accounting for swap order."""
    normalized = _normalize_verdict(verdict)
    if normalized is None or normalized == "Tie":
        return 0.5
    assistant_a_won = normalized == "A"
    favored_is_assistant_a = favored_config == assistant_a_config
    return 1.0 if assistant_a_won == favored_is_assistant_a else 0.0


class SideBySideJudge:
    """Run one config-pair comparison in both Assistant A/B presentation orders."""

    def __init__(
        self,
        client_factory: Callable[[str], JudgeClient],
        dimensions: tuple[str, ...] = DEFAULT_DIMENSIONS,
    ) -> None:
        self.client_factory = client_factory
        self.dimensions = dimensions

    def compare(
        self,
        *,
        config_a: str,
        config_b: str,
        paper_id: str,
        judge_model: str,
        paper_text: str,
        review_a: str,
        review_b: str,
    ) -> list[RawComparison]:
        """Call the judge twice with swapped review positions."""
        client = self.client_factory(judge_model)
        raw: list[RawComparison] = []

        for assistant_a_config in (config_a, config_b):
            assistant_a_review = review_a if assistant_a_config == config_a else review_b
            assistant_b_review = review_b if assistant_a_config == config_a else review_a
            prompt = build_comparison_prompt(paper_text, assistant_a_review, assistant_b_review)
            response = client.judge(prompt)
            thought, verdicts, reasons = parse_judge_response(response, self.dimensions)
            raw.append(
                RawComparison(
                    config_a=config_a,
                    config_b=config_b,
                    paper_id=paper_id,
                    judge_model=judge_model,
                    assistant_a_config=assistant_a_config,
                    verdicts=verdicts,
                    reasons=reasons,
                    thought=thought,
                    raw_response=response,
                )
            )
        return raw


class WinRateAggregator:
    """Collapse raw judge calls into pairwise scores and per-config win rates."""

    def __init__(self, dimensions: tuple[str, ...] = DEFAULT_DIMENSIONS) -> None:
        self.dimensions = dimensions

    def pairwise_scores(
        self,
        comparisons: list[RawComparison],
    ) -> dict[str, dict[str, dict[str, float]]]:
        """Average debiased points per config pair and rubric dimension."""
        buckets: dict[str, dict[str, list[float]]] = {}
        for row in comparisons:
            pair_key = _pair_key(row.config_a, row.config_b)
            buckets.setdefault(pair_key, {dim: [] for dim in self.dimensions})
            for dim in self.dimensions:
                points = points_for_config(
                    row.verdicts[dim],
                    favored_config=row.config_a,
                    config_a=row.config_a,
                    assistant_a_config=row.assistant_a_config,
                )
                buckets[pair_key][dim].append(points)

        return {
            pair_key: {dim: mean(values) for dim, values in dim_map.items()}
            for pair_key, dim_map in buckets.items()
        }

    def per_config_win_rates(
        self,
        config_ids: list[str],
        pairwise: dict[str, dict[str, dict[str, float]]],
    ) -> dict[str, dict[str, float]]:
        """Macro-average each config's score over all head-to-head opponents."""
        result = {config_id: {dim: 0.0 for dim in self.dimensions} for config_id in config_ids}
        counts = {config_id: {dim: 0 for dim in self.dimensions} for config_id in config_ids}

        for pair_key, dim_scores in pairwise.items():
            config_a, config_b = _split_pair_key(pair_key)
            for dim, score_for_a in dim_scores.items():
                result[config_a][dim] += score_for_a
                result[config_b][dim] += 1.0 - score_for_a
                counts[config_a][dim] += 1
                counts[config_b][dim] += 1

        for config_id in config_ids:
            for dim in self.dimensions:
                n = counts[config_id][dim]
                result[config_id][dim] = result[config_id][dim] / n if n else 0.0
        return result


class WinRateMetric(Metric):
    """Run side-by-side judging for every config pair, paper, and judge in a batch."""

    metric_name = "win_rate"

    def __init__(
        self,
        batch: Batch,
        judge_models: list[str],
        *,
        dimensions: tuple[str, ...] = DEFAULT_DIMENSIONS,
        client_factory: Callable[[str], JudgeClient] | None = None,
    ) -> None:
        super().__init__(batch)
        self.judge_models = judge_models
        self.dimensions = dimensions
        self.client_factory = client_factory or (lambda model: OpenRouterLLM(model))
        self.judge = SideBySideJudge(self.client_factory, dimensions)
        self.aggregator = WinRateAggregator(dimensions)

    def run(self) -> dict[str, Any]:
        """Collect all comparisons and aggregate win rates."""
        if len(self.judge_models) < 2:
            raise ValueError("at least two judge models are required (P4)")

        run_index = self.batch.runs_by_config_paper()
        config_ids = self.batch.config_ids()
        pairs = unordered_pairs(config_ids)
        paper_ids = self.batch.paper_ids()

        comparisons: list[RawComparison] = []
        for config_a, config_b in pairs:
            for paper_id in paper_ids:
                artifacts_a = self._artifacts_for(run_index, config_a, paper_id)
                artifacts_b = self._artifacts_for(run_index, config_b, paper_id)
                review_a = artifacts_a.final_review()
                review_b = artifacts_b.final_review()
                paper_text = artifacts_a.paper["paper_text"]

                for judge_model in self.judge_models:
                    comparisons.extend(
                        self.judge.compare(
                            config_a=config_a,
                            config_b=config_b,
                            paper_id=paper_id,
                            judge_model=judge_model,
                            paper_text=paper_text,
                            review_a=review_a,
                            review_b=review_b,
                        )
                    )

        pairwise = self.aggregator.pairwise_scores(comparisons)
        per_config = self.aggregator.per_config_win_rates(config_ids, pairwise)
        return {
            "dimensions": list(self.dimensions),
            "judges": list(self.judge_models),
            "rubric_version": RUBRIC_VERSION,
            "rubric": RUBRIC_TEXT,
            "raw_comparisons": [_comparison_to_dict(row) for row in comparisons],
            "pairwise": pairwise,
            "per_config": per_config,
        }

    def _artifacts_for(
        self,
        run_index: dict[tuple[str, str], Any],
        config_id: str,
        paper_id: str,
    ) -> RunArtifacts:
        key = (config_id, paper_id)
        if key not in run_index:
            raise KeyError(f"missing run for config={config_id!r} paper={paper_id!r}")
        return self.batch.open_run(run_index[key])


def _comparison_to_dict(row: RawComparison) -> dict[str, Any]:
    return {
        "config_a": row.config_a,
        "config_b": row.config_b,
        "paper_id": row.paper_id,
        "judge_model": row.judge_model,
        "assistant_a_config": row.assistant_a_config,
        "verdicts": row.verdicts,
        "reasons": row.reasons,
        "thought": row.thought,
        "raw_response": row.raw_response,
    }


def _pair_key(config_a: str, config_b: str) -> str:
    first, second = sorted((config_a, config_b))
    return f"{first}__vs__{second}"


def _split_pair_key(pair_key: str) -> tuple[str, str]:
    left, right = pair_key.split("__vs__", maxsplit=1)
    return left, right



def _normalize_verdict(value: str) -> str | None:
    cleaned = value.strip().upper()
    if cleaned in {"A", "B", "TIE"}:
        return "Tie" if cleaned == "TIE" else cleaned
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Metric 1: LLM-as-judge side-by-side win-rate")
    add_common_args(parser)
    parser.add_argument(
        "--judge",
        action="append",
        dest="judges",
        default=None,
        help=(
            "Judge model id (repeatable; P4 requires >=2 out-of-suite judges; "
            f"default: {', '.join(DEFAULT_JUDGES)})"
        ),
    )
    parser.add_argument(
        "--dimension",
        action="append",
        dest="dimensions",
        help="Rubric dimension to score (repeatable; default: all core dimensions)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for Metric 1."""
    args = build_parser().parse_args(argv)

    dimensions = tuple(args.dimensions) if args.dimensions else DEFAULT_DIMENSIONS
    if "overall" not in dimensions:
        raise SystemExit("overall dimension is mandatory")

    judges = list(args.judges) if args.judges else list(DEFAULT_JUDGES)
    if len(judges) < 2:
        raise SystemExit("P4 requires at least two --judge models")

    batch = load_batch(args)
    metric = WinRateMetric(batch, judges, dimensions=dimensions)
    output_path = metric.write()
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
