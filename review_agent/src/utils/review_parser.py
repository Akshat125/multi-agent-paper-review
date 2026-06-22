"""Parse structured fields from a leader-produced peer review."""

from __future__ import annotations

import re
from typing import Any

_SECTION_NAMES = ("summary", "strengths", "weaknesses", "questions")
_RATING_RE = re.compile(r"RATING:\s*(\d+)", re.IGNORECASE)
# Matches ## Summary, # Summary, **Summary**, Summary (line-start, case-insensitive)
_HEADER_RE = re.compile(
    r"^\s*(?:#{1,6}\s*|\*\*)?(summary|strengths|weaknesses|questions)(?:\*\*)?\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


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
        body = text[end:next_start].strip()
        sections[name] = body

    return sections
