"""Parse structured fields from a leader-produced peer review."""

from __future__ import annotations

import re
from typing import Any

_SECTION_NAMES = ("summary", "strengths", "weaknesses", "questions")
# Rating line: leader prompt asks for a final ``RATING: N`` line, but models
# sometimes decorate it with a markdown header or bold (e.g. ``### RATING: 8``
# or ``**RATING:** 8``). Tolerate those prefixes/wrappers so the score is still
# recovered; the literal placeholder ``RATING: <integer 1-10>`` stays unmatched
# (no digit), so a degenerate review correctly yields ``None``.
_RATING_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:\*\*)?RATING(?:\*\*)?\s*:\s*\**\s*(\d+)\s*\**\s*$",
    re.IGNORECASE | re.MULTILINE,
)
# Matches ## Summary, # Summary, **Summary**, **Strengths:**, Questions:, etc.
_HEADER_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:\*\*)?"
    r"(summary|strengths|weaknesses|questions)"
    r"(?:\*\*)?\s*:?\s*(?:\*\*)?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def normalize_final_review(text: str) -> str:
    """Return the review text trimmed to ``[first section header … RATING line]``.

    The leader prompt asks the model to "draft a high-level plan" and "write the
    current step you are working on", which some models (notably Mistral) dump
    into their *final* task output as a preamble (e.g. ``### Current Step: …`` or
    ``**Step 1** …``) before the actual ``## Summary``. The judge and comment
    extractor read ``final_review.md`` verbatim, so that scaffolding leaks into
    the metrics. This strips any leading preamble before the first recognised
    section header and any trailing text after the ``RATING:`` line, preserving
    the model's own review prose in between.

    Falls back to the original text when no section header is found (so a
    genuinely degenerate output is never silently blanked).
    """
    if not text or not isinstance(text, str):
        return text

    first_header = _HEADER_RE.search(text)
    if first_header is None:
        return text

    start = first_header.start()
    end = len(text)
    last_rating = None
    for m in _RATING_RE.finditer(text):
        last_rating = m
    if last_rating is not None:
        end = last_rating.end()

    return text[start:end].strip() + "\n"


def parse_review(text: str) -> dict[str, Any]:
    """Return ``summary``, ``strengths``, ``weaknesses``, ``questions``, ``rating``.

    Missing sections become empty strings. ``rating`` is an int 1-10 or ``None``.
    Never raises on malformed input.
    """
    if not text or not isinstance(text, str):
        return _empty_result()

    rating = _parse_rating(text)
    sections = _parse_sections(text)
    return {**sections, "rating": rating}


def _empty_result() -> dict[str, Any]:
    return {name: "" for name in _SECTION_NAMES} | {"rating": None}


def _parse_rating(text: str) -> int | None:
    matches = _RATING_RE.findall(text)
    if not matches:
        return None
    try:
        value = int(matches[-1])
    except ValueError:
        return None
    if 1 <= value <= 10:
        return value
    return None


def _parse_sections(text: str) -> dict[str, str]:
    headers: list[tuple[str, int, int]] = []
    for match in _HEADER_RE.finditer(text):
        name = match.group(1).lower()
        headers.append((name, match.start(), match.end()))

    if not headers:
        return {name: "" for name in _SECTION_NAMES}

    # Drop rating line and anything after it from section bodies
    rating_match = None
    for m in _RATING_RE.finditer(text):
        rating_match = m

    body_end = rating_match.start() if rating_match else len(text)

    sections: dict[str, str] = {name: "" for name in _SECTION_NAMES}
    for i, (name, _start, end) in enumerate(headers):
        if name not in sections:
            continue
        next_start = headers[i + 1][1] if i + 1 < len(headers) else body_end
        body = _clean_section_body(text[end:next_start])
        sections[name] = body

    return sections


def _clean_section_body(raw: str) -> str:
    """Strip whitespace and stray markdown horizontal rules from a section body."""
    lines = raw.strip().splitlines()
    cleaned = [line for line in lines if line.strip() != "---"]
    return "\n".join(cleaned).strip()
