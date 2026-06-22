"""Unit tests for parse_review."""

from __future__ import annotations

from src.utils.review_parser import parse_review

_SAMPLE = """\
## Summary
The paper proposes GraphAny for inductive node classification.

## Strengths
1. Novel problem setting.
2. Strong empirical results.

## Weaknesses
1. Missing ablations.
2. Unclear notation in Section 3.

## Questions
1. How does the method scale to large graphs?
2. Why not compare against GAT?

RATING: 7
"""


def test_well_formed_review():
    result = parse_review(_SAMPLE)
    assert result["summary"].startswith("The paper proposes GraphAny")
    assert "Novel problem setting" in result["strengths"]
    assert "Missing ablations" in result["weaknesses"]
    assert "scale to large graphs" in result["questions"]
    assert result["rating"] == 7


def test_missing_rating():
    text = _SAMPLE.replace("RATING: 7", "")
    result = parse_review(text)
    assert result["rating"] is None
    assert "GraphAny" in result["summary"]


def test_multiple_rating_lines_last_wins():
    text = _SAMPLE + "\nRATING: 9\n"
    assert parse_review(text)["rating"] == 9


def test_out_of_range_rating_returns_none():
    text = _SAMPLE.replace("RATING: 7", "RATING: 11")
    assert parse_review(text)["rating"] is None


def test_rating_at_boundary():
    text = _SAMPLE.replace("RATING: 7", "RATING: 1")
    assert parse_review(text)["rating"] == 1
    text = _SAMPLE.replace("RATING: 7", "RATING: 10")
    assert parse_review(text)["rating"] == 10


def test_header_variants():
    text = """\
# Summary
One-line summary.

**Strengths**
- good

## Weaknesses
- bad

Questions:
- q1

RATING: 5
"""
    result = parse_review(text)
    assert result["summary"] == "One-line summary."
    assert "good" in result["strengths"]
    assert "bad" in result["weaknesses"]
    assert "q1" in result["questions"]
    assert result["rating"] == 5


def test_empty_and_garbage_input():
    for text in ("", "   ", "no headers here", None):
        result = parse_review(text)  # type: ignore[arg-type]
        assert result["rating"] is None
        assert all(result[k] == "" for k in ("summary", "strengths", "weaknesses", "questions"))


def test_rating_case_insensitive():
    text = _SAMPLE.replace("RATING: 7", "rating: 8")
    assert parse_review(text)["rating"] == 8


def test_strips_horizontal_rules_from_sections():
    text = """\
## Summary
Intro.

## Strengths
---
1. Good idea.
---

## Weaknesses
1. Gap.

## Questions
1. Why?

RATING: 6
"""
    result = parse_review(text)
    assert "---" not in result["strengths"]
    assert "Good idea." in result["strengths"]


def test_bold_header_with_colon_inside():
    text = """\
## Summary
One-line summary.

**Strengths:**
- good

RATING: 5
"""
    result = parse_review(text)
    assert result["summary"] == "One-line summary."
    assert "good" in result["strengths"]
    assert result["rating"] == 5


def test_ignores_incidental_rating_in_body():
    text = """\
## Summary
Use RATING: 9 as an example in the rubric discussion.

## Strengths
- good

## Weaknesses
- bad

## Questions
- q1

RATING: 6
"""
    result = parse_review(text)
    assert "RATING: 9" in result["summary"]
    assert result["rating"] == 6
    assert "good" in result["strengths"]
