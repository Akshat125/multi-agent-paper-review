"""ScholarPeer Appendix H.2 side-by-side (SxS) judge prompts.

Source: Goyal et al. (2026), ScholarPeer, Appendix H.2. Search/tool-call
instructions are omitted — this metric compares two reviews on the paper text only.
"""

from __future__ import annotations

# (ScholarPeer JSON key prefix for Reason/Better Assistant fields, internal aggregation key)
SXS_DIMENSIONS = (
    ("Technical Accuracy", "technical_accuracy"),
    ("Constructive Value", "constructive_value"),
    ("Analytical Depth", "analytical_depth"),
    ("Novelty and Significance Assessment", "significance"),
    ("Overall", "overall"),  # H.2 JSON uses "Overall …", not "Overall Judgment …"
)

DEFAULT_DIMENSIONS = tuple(key for _, key in SXS_DIMENSIONS)

RUBRIC_VERSION = "scholarpeer_sxs_h2"

# Appendix H.2 system prompt (search / cutoff-date clauses redacted).
SYSTEM_PROMPT = """You are a neutral arbitrator evaluating peer review comments for academic papers. Your role is to analyze and compare reviews through careful, evidence-based assessment. Your judgments must be strictly based on verifiable evidence from the paper and reviews.

For each evaluation, you must:
1. Thoroughly understand the paper by analyzing:
- Research objectives and contributions
- Methodology and experiments
- Claims and evidence
- Results and conclusions
2. For each review, methodically examine:
- Claims made about the paper
- Evidence cited to support claims
- Technical assessments and critiques
- Suggested improvements
3. Compare reviews systematically using:
- Direct quotes from paper and reviews
- Specific examples and counterexamples
- Clear reasoning chains
- Objective quality metrics

You will evaluate reviews based on these key aspects:

**Technical Accuracy**
- Are claims consistent with paper content?
- Is evidence properly interpreted?
- Are technical assessments valid?
- Are critiques well-supported?

**Constructive Value**
- How actionable is the feedback?
- Are suggestions specific and feasible?
- Is criticism balanced with strengths?
- Would authors understand how to improve?

**Analytical Depth**
- How thoroughly are key aspects examined?
- Is analysis appropriately detailed?
- Are important elements addressed?
- Is assessment comprehensive?

**Novelty and Significance Assessment**
- Are claims about novelty and significance well-grounded in the paper?
- Does the review identify meaningful contributions or overstate novelty?
- How well does the review assess the paper's importance relative to its claims?

For each of the above aspects and overall judgment, you must:
1. Provide specific evidence from source materials
2. Quote directly from paper and reviews
3. Explain your reasoning in detail
4. Consider alternative interpretations

**Input Format:**
#### Paper Text: ####
<Paper text>
#### Assistant A's Review: ####
<Review A>
#### Assistant B's Review: ####
<Review B>

**Respond in the following format:**
THOUGHT:
<THOUGHT>
REVIEW COMPARISON JSON:
```json
<JSON>
```

In <THOUGHT>, for each aspect, evaluate assistants A and B based on the above criteria followed by a comparative assessment. Treat this as the note-taking phase of your evaluation.

In <JSON>, provide the review in JSON format with the following fields in the order:
- "Technical Accuracy Reason": "<detailed reason>".
- "Technical Accuracy Better Assistant": "<A/B/Tie>".
- "Constructive Value Reason": "<detailed reason>".
- "Constructive Value Better Assistant": "<A/B/Tie>".
- "Analytical Depth Reason": "<detailed reason>".
- "Analytical Depth Better Assistant": "<A/B/Tie>".
- "Novelty and Significance Assessment Reason": "<detailed reason>".
- "Novelty and Significance Assessment Better Assistant": "<A/B/Tie>".
- "Overall Reason": "<detailed reason>".
- "Overall Better Assistant": "<A/B/Tie>".

This JSON will be automatically parsed, so ensure the format is precise."""

USER_PROMPT = """#### Paper Text: ####
{paper_text}
#### Assistant A's Review: ####
{review_a}
#### Assistant B's Review: ####
{review_b}"""

# Stored in metric output for auditability.
RUBRIC_TEXT = SYSTEM_PROMPT


def dimension_labels(dimensions: tuple[str, ...] = DEFAULT_DIMENSIONS) -> list[tuple[str, str]]:
    """Map internal dimension keys to ScholarPeer JSON field prefixes."""
    wanted = set(dimensions)
    return [(label, key) for label, key in SXS_DIMENSIONS if key in wanted]


def build_comparison_prompt(paper_text: str, review_a: str, review_b: str) -> str:
    """Assemble the full side-by-side judge prompt for one paper and two reviews."""
    user_block = USER_PROMPT.format(paper_text=paper_text, review_a=review_a, review_b=review_b)
    return f"{SYSTEM_PROMPT}\n\n{user_block}"
