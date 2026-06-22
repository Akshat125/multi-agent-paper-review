"""Tests for Metric 1 aggregation and parsing (no live judge calls)."""

from __future__ import annotations

import json

from metrics.rubric import DEFAULT_DIMENSIONS, dimension_labels
from metrics.win_rate import (
    RawComparison,
    SideBySideJudge,
    WinRateAggregator,
    WinRateMetric,
    parse_judge_response,
    points_for_config,
)


class FakeJudge:
    def __init__(self, response: str) -> None:
        self.response = response
        self.prompts: list[str] = []

    def judge(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


def _sxs_response(**overrides: str) -> str:
    fields: dict[str, str] = {}
    for label, key in dimension_labels(DEFAULT_DIMENSIONS):
        fields[f"{label} Reason"] = overrides.get(f"{key}_reason", "test reason")
        fields[f"{label} Better Assistant"] = overrides.get(key, "A")
    return (
        "THOUGHT:\nNotes.\nREVIEW COMPARISON JSON:\n```json\n"
        + json.dumps(fields)
        + "\n```"
    )


def test_parse_judge_response_accepts_scholarpeer_json():
    text = _sxs_response(overall="B", significance="Tie")
    thought, verdicts, reasons = parse_judge_response(text, ("overall", "significance"))
    assert thought == "Notes."
    assert verdicts == {"overall": "B", "significance": "Tie"}
    assert "overall" in reasons


def test_parse_overall_uses_scholarpeer_json_prefix():
    """H.2 uses 'Overall Better Assistant', not 'Overall Judgment Better Assistant'."""
    text = (
        "THOUGHT:\nok\nREVIEW COMPARISON JSON:\n```json\n"
        + json.dumps({"Overall Reason": "r", "Overall Better Assistant": "A"})
        + "\n```"
    )
    _, verdicts, _ = parse_judge_response(text, ("overall",))
    assert verdicts == {"overall": "A"}


def test_parse_falls_back_to_regex_when_json_block_missing_fields():
    text = (
        "THOUGHT:\nok\nREVIEW COMPARISON JSON:\n```json\n{}\n```\n"
        '"Overall Better Assistant": "B"'
    )
    _, verdicts, _ = parse_judge_response(text, ("overall",))
    assert verdicts == {"overall": "B"}


def test_build_prompt_uses_scholarpeer_headers():
    from metrics.rubric import build_comparison_prompt

    prompt = build_comparison_prompt("paper body", "review A text", "review B text")
    assert "#### Paper Text: ####" in prompt
    assert "#### Assistant A's Review: ####" in prompt
    assert "#### Assistant B's Review: ####" in prompt
    assert "Technical Accuracy Better Assistant" in prompt
    assert "Google Search" not in prompt


def test_points_for_config_position_debias():
    # A judge that always picks Assistant A should average to 0.5 after both orders.
    assert (
        points_for_config("A", "All-A", "All-A", "All-A")
        + points_for_config("A", "All-A", "All-A", "All-B")
    ) / 2 == 0.5
    assert points_for_config("A", "All-A", "All-A", "All-A") == 1.0
    assert points_for_config("B", "All-A", "All-A", "All-B") == 1.0


def test_aggregator_pairwise_and_per_config():
    comparisons = [
        RawComparison("All-A", "All-B", "paper_a", "judge", "All-A", {"overall": "A"}, {}, "", ""),
        RawComparison("All-A", "All-B", "paper_a", "judge", "All-B", {"overall": "B"}, {}, "", ""),
        RawComparison("All-A", "All-B", "paper_b", "judge", "All-A", {"overall": "Tie"}, {}, "", ""),
        RawComparison("All-A", "All-B", "paper_b", "judge", "All-B", {"overall": "Tie"}, {}, "", ""),
    ]
    aggregator = WinRateAggregator(("overall",))
    pairwise = aggregator.pairwise_scores(comparisons)
    pair_key = "All-A__vs__All-B"
    assert pairwise[pair_key]["overall"] == 0.75

    per_config = aggregator.per_config_win_rates(["All-A", "All-B"], pairwise)
    assert per_config["All-A"]["overall"] == 0.75
    assert per_config["All-B"]["overall"] == 0.25


def test_win_rate_metric_with_order_aware_fake_judge(tiny_batch):
    class OrderAwareFakeJudge:
        def judge(self, prompt: str) -> str:
            # Use rsplit — the system prompt also contains the Assistant A/B header examples.
            parts = prompt.rsplit("#### Assistant A's Review: ####", maxsplit=1)[1]
            assistant_a, assistant_b = parts.split("#### Assistant B's Review: ####", maxsplit=1)
            if "Review A on" in assistant_a:
                winner = "A"
            elif "Review A on" in assistant_b:
                winner = "B"
            else:
                winner = "A"
            return _sxs_response(overall=winner)

    metric = WinRateMetric(
        tiny_batch,
        ["fake-judge-a", "fake-judge-b"],
        dimensions=("overall",),
        client_factory=lambda _m: OrderAwareFakeJudge(),
    )
    payload = metric.run()

    assert payload["per_config"]["All-A"]["overall"] == 1.0
    assert payload["per_config"]["All-B"]["overall"] == 0.0


def test_win_rate_metric_position_bias_averages_to_half(tiny_batch):
    response = _sxs_response(overall="A")

    metric = WinRateMetric(
        tiny_batch,
        ["fake-judge-a", "fake-judge-b"],
        dimensions=("overall",),
        client_factory=lambda _m: FakeJudge(response),
    )
    payload = metric.run()

    assert len(payload["raw_comparisons"]) == 8  # 1 pair × 2 papers × 2 judges × 2 orders
    assert payload["per_config"]["All-A"]["overall"] == 0.5
    assert payload["per_config"]["All-B"]["overall"] == 0.5


def test_side_by_side_judge_calls_both_orders(tiny_batch):
    fake = FakeJudge(_sxs_response(overall="A"))

    judge = SideBySideJudge(lambda _m: fake, dimensions=("overall",))
    rows = judge.compare(
        config_a="All-A",
        config_b="All-B",
        paper_id="paper_a",
        judge_model="fake",
        paper_text="paper",
        review_a="review A",
        review_b="review B",
    )
    assert len(rows) == 2
    assert {row.assistant_a_config for row in rows} == {"All-A", "All-B"}
    assert len(fake.prompts) == 2
