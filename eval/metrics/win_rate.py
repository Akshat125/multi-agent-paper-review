"""Metric 1 — LLM-as-judge side-by-side win-rate."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from crewai import LLM

from .batch import Batch, RunArtifacts, unordered_pairs, write_metric
from .rubric import (
    DEFAULT_DIMENSIONS,
    RUBRIC_TEXT,
    RUBRIC_VERSION,
    build_comparison_prompt,
    dimension_labels,
)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
THOUGHT_RE = re.compile(r"THOUGHT:\s*(.*?)\s*REVIEW COMPARISON JSON:", re.DOTALL | re.IGNORECASE)
BETTER_ASSISTANT_RE = re.compile(
    r'"(?P<label>[^"]+) Better Assistant":\s*"(?P<verdict>A|B|Tie)"',
    re.IGNORECASE,
)


class JudgeClient(Protocol):
    def judge(self, prompt: str) -> str: ...


@dataclass(frozen=True)
class RawComparison:
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
    """Parse ScholarPeer H.2 THOUGHT + REVIEW COMPARISON JSON."""
    thought_match = THOUGHT_RE.search(text)
    thought = thought_match.group(1).strip() if thought_match else ""

    label_map = {label: key for label, key in dimension_labels(dimensions)}
    verdicts: dict[str, str] = {}
    reasons: dict[str, str] = {}

    try:
        payload = _extract_json_payload(text)
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
    """Map an A/B/Tie verdict to points for ``favored_config``."""
    normalized = _normalize_verdict(verdict)
    if normalized is None or normalized == "Tie":
        return 0.5
    assistant_a_won = normalized == "A"
    favored_is_assistant_a = favored_config == assistant_a_config
    return 1.0 if assistant_a_won == favored_is_assistant_a else 0.0


class OpenRouterJudge:
    """Thin wrapper around CrewAI's OpenRouter-compatible LLM."""

    def __init__(self, model: str, api_key: str | None = None) -> None:
        self.model = model
        self._llm = LLM(
            model=_openrouter_model(model),
            base_url=OPENROUTER_BASE_URL,
            api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
        )

    def judge(self, prompt: str) -> str:
        response = self._llm.call(prompt)
        return response if isinstance(response, str) else str(response)


class SideBySideJudge:
    """Run one debiased comparison (both presentation orders)."""

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
    """Aggregate raw comparisons into pairwise scores and per-config win rates."""

    def __init__(self, dimensions: tuple[str, ...] = DEFAULT_DIMENSIONS) -> None:
        self.dimensions = dimensions

    def pairwise_scores(
        self,
        comparisons: list[RawComparison],
    ) -> dict[str, dict[str, dict[str, float]]]:
        """Return ``pair_key -> dimension -> score_for_a``."""
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
            pair_key: {dim: _mean(values) for dim, values in dim_map.items()}
            for pair_key, dim_map in buckets.items()
        }

    def per_config_win_rates(
        self,
        config_ids: list[str],
        pairwise: dict[str, dict[str, dict[str, float]]],
    ) -> dict[str, dict[str, float]]:
        """Macro-average ``score(config vs opponent)`` over opponents per dimension."""
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


class WinRateMetric:
    """Orchestrate side-by-side judging for every config pair and paper in a batch."""

    def __init__(
        self,
        batch: Batch,
        judge_models: list[str],
        *,
        dimensions: tuple[str, ...] = DEFAULT_DIMENSIONS,
        client_factory: Callable[[str], JudgeClient] | None = None,
    ) -> None:
        self.batch = batch
        self.judge_models = judge_models
        self.dimensions = dimensions
        self.client_factory = client_factory or (lambda model: OpenRouterJudge(model))
        self.judge = SideBySideJudge(self.client_factory, dimensions)
        self.aggregator = WinRateAggregator(dimensions)

    def run(self) -> dict[str, Any]:
        if len(self.judge_models) < 2:
            raise ValueError("at least two judge models are required (P4)")

        run_index = self.batch.runs_by_config_paper()
        config_ids = self.batch.config_ids()
        pairs = unordered_pairs(config_ids)
        paper_ids = sorted({paper_id for _, paper_id in run_index})

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

    def write(self, payload: dict[str, Any] | None = None) -> Any:
        data = payload if payload is not None else self.run()
        return write_metric(self.batch, "win_rate", data)

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


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _openrouter_model(model_name: str) -> str:
    return model_name if model_name.startswith("openrouter/") else f"openrouter/{model_name}"


def _extract_json_payload(text: str) -> dict[str, Any]:
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
        raise ValueError("could not parse REVIEW COMPARISON JSON from judge response") from exc
    if not isinstance(payload, dict):
        raise ValueError("judge JSON must be an object")
    return payload


def _normalize_verdict(value: str) -> str | None:
    cleaned = value.strip().upper()
    if cleaned in {"A", "B", "TIE"}:
        return "Tie" if cleaned == "TIE" else cleaned
    return None
