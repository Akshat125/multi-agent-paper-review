"""Metric 2 — comment recall + comment count (MARG §6).

Measures how many human-flagged issues each config's review covers, plus
``n_comments`` as a verbosity guard. Uses a three-stage LLM alignment pipeline.
"""

from __future__ import annotations

import argparse
import random
from typing import Any, Callable

from prompts.comment_recall import (
    PROMPT_VERSION,
    Comment,
    Pair,
    build_extraction_prompt,
    build_filter_prompt,
    build_match_prompt,
    consolidate_candidates,
    dedupe_comments,
    format_human_review,
    is_match,
    parse_extraction_response,
    parse_filter_response,
    parse_match_response,
    shuffle_comments,
    strip_rating_line,
)
from metrics.base import Metric
from utils.batch import Batch
from utils.cli import add_common_args, load_batch
from utils.llm import LLMClient, OpenRouterLLM
from utils.stats import derive_seed, mean

DEFAULT_ALIGNMENT_MODEL = "openai/gpt-5-mini"
DEFAULT_SEED = 42


def extract_comments(llm: LLMClient, review_text: str, id_prefix: str) -> list[Comment]:
    """Run stage 1 extraction on one review body."""
    if not review_text.strip():
        return []
    response = llm.call(build_extraction_prompt(review_text))
    return parse_extraction_response(response, id_prefix)


def extract_human_comments(llm: LLMClient, paper: dict[str, Any]) -> list[Comment]:
    """Extract and union human comments for a paper (computed once per paper)."""
    all_comments: list[Comment] = []
    for review in paper.get("human_reviews", []):
        review_text = format_human_review(review)
        if not review_text.strip():
            continue
        all_comments.extend(extract_comments(llm, review_text, "real"))
    return dedupe_comments(all_comments, "real")


def match_candidates(
    llm: LLMClient,
    c_gen: list[Comment],
    c_real: list[Comment],
    *,
    passes: int = 5,
    threshold: int = 2,
    seed: int = DEFAULT_SEED,
    rng_factory: Callable[[int], random.Random] | None = None,
) -> list[Pair]:
    """Run repeated shuffled match passes and keep stable candidate pairs."""
    if not c_gen or not c_real:
        return []

    pass_pairs: list[list[Pair]] = []
    for pass_index in range(passes):
        rng = (rng_factory or random.Random)(seed + pass_index)
        shuffled_gen = shuffle_comments(c_gen, rng)
        shuffled_real = shuffle_comments(c_real, rng)
        response = llm.call(build_match_prompt(shuffled_gen, shuffled_real))
        pass_pairs.append(parse_match_response(response))
    return consolidate_candidates(pass_pairs, threshold)


def filter_pairs(
    llm: LLMClient,
    c_gen: list[Comment],
    c_real: list[Comment],
    candidates: list[Pair],
) -> list[dict[str, Any]]:
    """Score each candidate pair and keep those passing the relatedness gate."""
    gen_by_id = {comment["id"]: comment for comment in c_gen}
    real_by_id = {comment["id"]: comment for comment in c_real}
    matches: list[dict[str, Any]] = []

    for gen_id, real_id in candidates:
        gen_comment = gen_by_id.get(gen_id)
        real_comment = real_by_id.get(real_id)
        if gen_comment is None or real_comment is None:
            continue
        response = llm.call(build_filter_prompt(gen_comment, real_comment))
        relatedness, specificity = parse_filter_response(response)
        if is_match(relatedness, specificity):
            matches.append(
                {
                    "gen_id": gen_id,
                    "real_id": real_id,
                    "relatedness": relatedness,
                    "specificity": specificity,
                    "gen_text": gen_comment["text"],
                    "real_text": real_comment["text"],
                }
            )
    return matches


def compute_recall(
    c_gen: list[Comment],
    c_real: list[Comment],
    matches: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute directional recall and comment counts from accepted matches."""
    real_matched = {match["real_id"] for match in matches}
    gen_matched = {match["gen_id"] for match in matches}
    n_real = len(c_real)
    recall = len(real_matched) / n_real if n_real else 0.0
    return {
        "recall": recall,
        "n_comments": len(c_gen),
        "n_real": n_real,
        "real_matched_count": len(real_matched),
        "gen_matched_count": len(gen_matched),
    }


class CommentRecallMetric(Metric):
    """Run the full comment-recall pipeline for every config and paper in a batch.

    Human ground-truth comments are extracted once per paper and reused across configs.
    """

    metric_name = "comment_recall"

    def __init__(
        self,
        batch: Batch,
        model: str,
        *,
        match_passes: int = 5,
        match_threshold: int = 2,
        seed: int = DEFAULT_SEED,
        client_factory: Callable[[str], LLMClient] | None = None,
    ) -> None:
        super().__init__(batch)
        self.model = model
        self.match_passes = match_passes
        self.match_threshold = match_threshold
        self.seed = seed
        self.client_factory = client_factory or (lambda _model: OpenRouterLLM(_model))

    def run(self) -> dict[str, Any]:
        """Extract, align, score, and aggregate recall + n_comments."""
        llm = self.client_factory(self.model)
        run_index = self.batch.runs_by_config_paper()
        config_ids = self.batch.config_ids()
        paper_ids = self.batch.paper_ids()

        c_real_by_paper = {
            paper_id: extract_human_comments(llm, self.batch.papers[paper_id])
            for paper_id in paper_ids
        }

        per_paper: dict[str, dict[str, Any]] = {}
        for config_id in config_ids:
            per_paper[config_id] = {}
            for paper_id in paper_ids:
                artifacts = self.batch.open_run(run_index[(config_id, paper_id)])
                review_text = strip_rating_line(artifacts.final_review())
                c_gen = extract_comments(llm, review_text, "gen")
                c_real = c_real_by_paper[paper_id]

                candidates = match_candidates(
                    llm,
                    c_gen,
                    c_real,
                    passes=self.match_passes,
                    threshold=self.match_threshold,
                    seed=derive_seed(self.seed, self.batch.name, config_id, paper_id),
                )
                matches = filter_pairs(llm, c_gen, c_real, candidates)
                stats = compute_recall(c_gen, c_real, matches)

                per_paper[config_id][paper_id] = {
                    **stats,
                    "c_gen": c_gen,
                    "c_real": c_real,
                    "matches": matches,
                }

        per_config: dict[str, dict[str, float]] = {}
        for config_id in config_ids:
            paper_stats = per_paper[config_id].values()
            per_config[config_id] = {
                "recall": mean([row["recall"] for row in paper_stats]),
                "n_comments": mean([row["n_comments"] for row in paper_stats]),
            }

        return {
            "alignment_model": self.model,
            "prompt_version": PROMPT_VERSION,
            "match_passes": self.match_passes,
            "match_threshold": self.match_threshold,
            "per_paper": per_paper,
            "per_config": per_config,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Metric 2: comment recall + comment count")
    add_common_args(parser)
    parser.add_argument(
        "--model",
        default=DEFAULT_ALIGNMENT_MODEL,
        help=f"Alignment/extraction LLM id (P6; default: {DEFAULT_ALIGNMENT_MODEL})",
    )
    parser.add_argument("--match-passes", type=int, default=5, help="Candidate match passes")
    parser.add_argument(
        "--match-threshold",
        type=int,
        default=2,
        help="Minimum passes a candidate pair must appear in",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="RNG seed for match shuffles")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for Metric 2."""
    args = build_parser().parse_args(argv)
    batch = load_batch(args)
    metric = CommentRecallMetric(
        batch,
        args.model,
        match_passes=args.match_passes,
        match_threshold=args.match_threshold,
        seed=args.seed,
    )
    output_path = metric.write()
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
