"""Prompts and parsers for Metric 2 — comment recall (MARG §6).

Builds extraction, matching, and filter prompts plus JSON parsers for the
three-stage alignment pipeline described in ``seminar-paper/paper-context/eval-metrics.md`` §2.
"""

from __future__ import annotations

import random
import re
from typing import Any

from utils.llm import extract_json

PROMPT_VERSION = "marg_comment_recall_v1"

RATING_LINE_RE = re.compile(r"^\s*RATING:\s*\d+\s*$", re.IGNORECASE | re.MULTILINE)

RELATEDNESS_LEVELS = frozenset({"none", "weak", "medium", "high"})
SPECIFICITY_LEVELS = frozenset({"less", "same", "more"})
MATCH_RELATEDNESS = frozenset({"medium", "high"})
MATCH_SPECIFICITY = frozenset({"same", "more"})

Comment = dict[str, str]
Pair = tuple[str, str]


def strip_rating_line(text: str) -> str:
    """Remove the trailing ``RATING: N`` line from a generated review."""
    return RATING_LINE_RE.sub("", text).strip()


def format_human_review(review: dict[str, Any]) -> str:
    """Serialize one human review's actionable sections for extraction."""
    content = review.get("content") or {}
    sections: list[str] = []
    for key in ("weaknesses", "questions", "suggestions"):
        value = content.get(key) or review.get(key)
        if value:
            sections.append(f"## {key.title()}\n{value}")
    return "\n\n".join(sections)


def build_extraction_prompt(review_text: str) -> str:
    """Ask the LLM to split a review into atomic actionable comments."""
    return f"""Extract atomic, actionable comments from the peer review below.

Rules:
- Each comment should be one distinct criticism, concern, or concrete suggestion.
- Keep actionable criticism and improvement suggestions.
- Ignore positive remarks, praise, and minor grammar/style nits.
- Do not merge unrelated points into one comment.

Respond with JSON only:
```json
{{"comments": [{{"id": "c1", "text": "..."}}]}}
```

#### Review: ####
{review_text}"""


def build_match_prompt(c_gen: list[Comment], c_real: list[Comment]) -> str:
    """Ask the LLM for many-to-many candidate pairs between generated and human comments."""
    gen_block = "\n".join(f'- {c["id"]}: {c["text"]}' for c in c_gen)
    real_block = "\n".join(f'- {c["id"]}: {c["text"]}' for c in c_real)
    return f"""Identify all pairs of generated and human comments that refer to the same underlying issue.

Rules:
- A pair matches when the generated comment addresses the same substantive point as the human comment.
- Include many-to-many matches when several comments cover the same issue.
- Do not match comments that only share vague topical overlap.

Respond with JSON only:
```json
{{"pairs": [{{"gen_id": "gen_0", "real_id": "real_1"}}]}}
```

#### Generated comments: ####
{gen_block}

#### Human comments: ####
{real_block}"""


def build_filter_prompt(gen_comment: Comment, real_comment: Comment) -> str:
    """Ask the LLM to score relatedness and specificity for one candidate pair."""
    return f"""Score whether these two review comments refer to the same underlying issue.

Generated comment ({gen_comment["id"]}):
{gen_comment["text"]}

Human comment ({real_comment["id"]}):
{real_comment["text"]}

Respond with JSON only:
```json
{{"relatedness": "none|weak|medium|high", "specificity": "less|same|more"}}
```"""


def parse_extraction_response(text: str, id_prefix: str) -> list[Comment]:
    """Turn an extraction JSON payload into a normalized comment list."""
    payload = extract_json(text)
    raw = payload.get("comments", [])
    if not isinstance(raw, list):
        raise ValueError("extraction response must include a comments list")

    comments: list[Comment] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        comment_text = str(item.get("text", "")).strip()
        if not comment_text:
            continue
        comment_id = str(item.get("id") or f"{id_prefix}_{index}")
        comments.append({"id": comment_id, "text": comment_text})
    return comments


def parse_match_response(text: str) -> list[Pair]:
    """Turn a match JSON payload into ``(gen_id, real_id)`` candidate pairs."""
    payload = extract_json(text)
    raw = payload.get("pairs", [])
    if not isinstance(raw, list):
        raise ValueError("match response must include a pairs list")

    pairs: list[Pair] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        gen_id = str(item.get("gen_id", "")).strip()
        real_id = str(item.get("real_id", "")).strip()
        if gen_id and real_id:
            pairs.append((gen_id, real_id))
    return pairs


def parse_filter_response(text: str) -> tuple[str, str]:
    """Read relatedness and specificity labels from a filter JSON payload."""
    payload = extract_json(text)
    relatedness = str(payload.get("relatedness", "")).strip().lower()
    specificity = str(payload.get("specificity", "")).strip().lower()
    if relatedness not in RELATEDNESS_LEVELS:
        raise ValueError(f"invalid relatedness {relatedness!r}")
    if specificity not in SPECIFICITY_LEVELS:
        raise ValueError(f"invalid specificity {specificity!r}")
    return relatedness, specificity


def is_match(relatedness: str, specificity: str) -> bool:
    """Apply the MARG §6 acceptance rule to a scored candidate pair."""
    return relatedness in MATCH_RELATEDNESS and specificity in MATCH_SPECIFICITY


def consolidate_candidates(pass_pairs: list[list[Pair]], threshold: int) -> list[Pair]:
    """Keep pairs that survive repeated shuffled match passes (≥ threshold votes)."""
    counts: dict[Pair, int] = {}
    for pairs in pass_pairs:
        for pair in set(pairs):
            counts[pair] = counts.get(pair, 0) + 1
    return sorted(pair for pair, count in counts.items() if count >= threshold)


def shuffle_comments(comments: list[Comment], rng: random.Random) -> list[Comment]:
    """Shuffle comment order to reduce position bias across match passes."""
    shuffled = list(comments)
    rng.shuffle(shuffled)
    return shuffled


def dedupe_comments(comments: list[Comment], id_prefix: str) -> list[Comment]:
    """Collapse duplicate human comments before alignment."""
    seen: set[str] = set()
    deduped: list[Comment] = []
    for comment in comments:
        key = comment["text"].strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append({"id": f"{id_prefix}_{len(deduped)}", "text": comment["text"]})
    return deduped
