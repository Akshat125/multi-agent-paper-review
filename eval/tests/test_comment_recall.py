"""Tests for Metric 2 comment recall (no live LLM calls)."""

from __future__ import annotations

import json

from metrics.comment_recall import (
    CommentRecallMetric,
    compute_recall,
    extract_comments,
    extract_human_comments,
    filter_pairs,
    match_candidates,
)
from prompts.comment_recall import (
    consolidate_candidates,
    dedupe_comments,
    format_human_review,
    is_match,
    parse_extraction_response,
    parse_filter_response,
    parse_match_response,
    strip_rating_line,
)


class StageFakeLLM:
    """Return canned JSON based on prompt stage markers."""

    def call(self, prompt: str) -> str:
        if "Extract atomic, actionable comments" in prompt:
            if "weak baselines" in prompt.lower() or "weak baseline" in prompt.lower():
                return _json({"comments": [{"id": "gen_0", "text": "Weak baselines used."}]})
            if "significance" in prompt.lower():
                return _json({"comments": [{"id": "gen_0", "text": "No significance tests."}]})
            if "baselines are too weak" in prompt.lower():
                return _json({"comments": [{"id": "real_0", "text": "The baselines are too weak."}]})
            if "attention module" in prompt.lower():
                return _json(
                    {"comments": [{"id": "real_0", "text": "Missing ablation on the attention module."}]}
                )
            if "statistical significance testing" in prompt.lower():
                return _json(
                    {
                        "comments": [
                            {
                                "id": "real_0",
                                "text": "The evaluation lacks statistical significance testing.",
                            }
                        ]
                    }
                )
            return _json({"comments": []})

        if "Identify all pairs" in prompt:
            return _json({"pairs": [{"gen_id": "gen_0", "real_id": "real_0"}]})

        if '"relatedness"' in prompt:
            return _json({"relatedness": "high", "specificity": "same"})

        raise AssertionError(f"unexpected prompt: {prompt[:120]!r}")


def _json(payload: dict) -> str:
    return "```json\n" + json.dumps(payload) + "\n```"


def test_strip_rating_line():
    text = "Summary here.\n\nRATING: 7"
    assert strip_rating_line(text) == "Summary here."


def test_format_human_review():
    review = {
        "content": {
            "weaknesses": "Weak baselines.",
            "questions": "Add stronger baselines?",
        }
    }
    text = format_human_review(review)
    assert "## Weaknesses" in text
    assert "Weak baselines." in text
    assert "## Questions" in text


def test_parse_extraction_response():
    comments = parse_extraction_response(
        _json({"comments": [{"id": "c1", "text": "Issue A"}]}),
        "gen",
    )
    assert comments == [{"id": "c1", "text": "Issue A"}]


def test_parse_match_response():
    pairs = parse_match_response(_json({"pairs": [{"gen_id": "gen_0", "real_id": "real_1"}]}))
    assert pairs == [("gen_0", "real_1")]


def test_parse_filter_response():
    relatedness, specificity = parse_filter_response(
        _json({"relatedness": "medium", "specificity": "more"})
    )
    assert relatedness == "medium"
    assert specificity == "more"


def test_is_match_gate():
    assert is_match("high", "same")
    assert is_match("medium", "more")
    assert not is_match("weak", "same")
    assert not is_match("high", "less")


def test_consolidate_candidates_threshold():
    pass_pairs = [
        [("gen_0", "real_0"), ("gen_1", "real_1")],
        [("gen_0", "real_0")],
        [("gen_0", "real_0"), ("gen_1", "real_2")],
    ]
    assert consolidate_candidates(pass_pairs, threshold=2) == [("gen_0", "real_0")]


def test_compute_recall_and_zero_real():
    c_gen = [{"id": "gen_0", "text": "A"}]
    c_real = [{"id": "real_0", "text": "B"}, {"id": "real_1", "text": "C"}]
    matches = [{"gen_id": "gen_0", "real_id": "real_0"}]
    stats = compute_recall(c_gen, c_real, matches)
    assert stats["recall"] == 0.5
    assert stats["n_comments"] == 1
    assert stats["real_matched_count"] == 1
    assert stats["gen_matched_count"] == 1

    empty_stats = compute_recall(c_gen, [], matches)
    assert empty_stats["recall"] == 0.0


def test_dedupe_comments():
    comments = [
        {"id": "real_0", "text": "Same issue."},
        {"id": "real_1", "text": " same issue. "},
        {"id": "real_2", "text": "Different issue."},
    ]
    deduped = dedupe_comments(comments, "real")
    assert len(deduped) == 2
    assert deduped[0]["id"] == "real_0"
    assert deduped[1]["id"] == "real_1"


def test_match_candidates_uses_threshold_with_deterministic_rng():
    llm = StageFakeLLM()
    c_gen = [{"id": "gen_0", "text": "x"}]
    c_real = [{"id": "real_0", "text": "y"}]
    pairs = match_candidates(
        llm,
        c_gen,
        c_real,
        passes=3,
        threshold=2,
        seed=1,
        rng_factory=lambda seed: __import__("random").Random(seed),
    )
    assert pairs == [("gen_0", "real_0")]


def test_build_parser_defaults_to_gpt5_mini():
    from metrics.comment_recall import DEFAULT_ALIGNMENT_MODEL, build_parser

    args = build_parser().parse_args(["--batch", "pilot"])
    assert args.model == DEFAULT_ALIGNMENT_MODEL


def test_main_uses_default_alignment_model(tiny_batch, tmp_path, monkeypatch):
    from metrics import comment_recall as comment_recall_module

    captured: list[str] = []

    class StubMetric:
        def __init__(self, batch, model, **kwargs):
            captured.append(model)

        def write(self):
            return tmp_path / "comment_recall.json"

    monkeypatch.setattr(comment_recall_module, "CommentRecallMetric", StubMetric)
    monkeypatch.setattr(comment_recall_module, "load_batch", lambda _args: tiny_batch)

    assert comment_recall_module.main(["--batch", "pilot"]) == 0
    assert captured == [comment_recall_module.DEFAULT_ALIGNMENT_MODEL]


def test_comment_recall_metric_end_to_end(tiny_batch):
    tiny_batch.runs[0].run_dir  # ensure fixture loaded

    # Make generated reviews mention issues aligned with fake extraction responses.
    for run in tiny_batch.runs:
        review_path = run.run_dir / "final_review.md"
        if run.paper_id == "paper_a":
            review_path.write_text("Weak baselines used in experiments.\nRATING: 7", encoding="utf-8")
        else:
            review_path.write_text("No significance tests reported.\nRATING: 5", encoding="utf-8")

    metric = CommentRecallMetric(
        tiny_batch,
        "fake-model",
        match_passes=2,
        match_threshold=2,
        client_factory=lambda _m: StageFakeLLM(),
    )
    payload = metric.run()

    assert payload["per_config"]["All-A"]["recall"] == 0.75
    assert payload["per_config"]["All-B"]["recall"] == 0.75
    assert payload["per_config"]["All-A"]["n_comments"] == 1.0
    paper_row = payload["per_paper"]["All-A"]["paper_a"]
    assert paper_row["n_real"] == 2
    assert paper_row["recall"] == 0.5
    assert len(paper_row["matches"]) == 1


def test_extract_and_filter_helpers():
    llm = StageFakeLLM()
    comments = extract_comments(llm, "Weak baselines used.", "gen")
    assert comments[0]["text"] == "Weak baselines used."

    paper = {
        "human_reviews": [
            {"content": {"weaknesses": "The baselines are too weak."}},
        ]
    }
    real = extract_human_comments(llm, paper)
    assert len(real) == 1

    matches = filter_pairs(
        llm,
        [{"id": "gen_0", "text": "g"}],
        [{"id": "real_0", "text": "r"}],
        [("gen_0", "real_0")],
    )
    assert matches[0]["relatedness"] == "high"
