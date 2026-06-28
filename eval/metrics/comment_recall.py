"""Metric 2 — comment recall + comment count (MARG §6).

Measures how many human-flagged issues each config's review covers, plus
``n_comments`` as a verbosity guard. Uses a three-stage LLM alignment pipeline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from prompts.comment_recall import (  # noqa: E402
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
from metrics.base import Metric  # noqa: E402
from utils.run_set import RunSet  # noqa: E402
from utils.cli import add_common_args, load_run_set  # noqa: E402
from utils.llm import LLMClient, OpenRouterLLM  # noqa: E402
from utils.stats import derive_seed, mean  # noqa: E402

DEFAULT_ALIGNMENT_MODEL = "openai/gpt-5-mini"
DEFAULT_SEED = 42
PARSE_MAX_ATTEMPTS = 3


def _call_and_parse(
    llm: LLMClient,
    prompt: str,
    parse: Callable[[str], Any],
    *,
    what: str,
    max_attempts: int = PARSE_MAX_ATTEMPTS,
) -> Any:
    """Call the alignment model and parse its response, re-calling on parse failure.

    ``OpenRouterLLM.call`` already retries transport errors (429/5xx) internally, but
    parsing happens here, after it returns — so a syntactically malformed or
    schema-invalid JSON response (which raises ``ValueError``) would otherwise abort
    the whole unit, and with it the entire metric. This mirrors win_rate's
    ``_execute_task``: a fresh call is issued each attempt because provider/sampling
    variation usually yields parseable JSON on a retry even at temperature 0.
    """
    last_error: ValueError | None = None
    for _ in range(max(1, max_attempts)):
        try:
            return parse(llm.call(prompt))
        except ValueError as exc:  # raised by extract_json / the stage parsers
            last_error = exc
    raise ValueError(
        f"{what}: unparseable response after {max_attempts} attempts: {last_error}"
    ) from last_error


def _text_hash(text: str) -> str:
    """Stable digest of a review body, so regenerating it invalidates its cache entry."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def _human_review_text(paper: dict[str, Any]) -> str:
    """Reconstruct the exact text fed to human-comment extraction (for cache hashing).

    Uses the same non-empty predicate as :func:`extract_human_comments`, so the hash
    changes iff the set/content of contributing human reviews changes.
    """
    sections: list[str] = []
    for review in paper.get("human_reviews", []):
        formatted = format_human_review(review)
        if formatted.strip():
            sections.append(formatted)
    return "\n\n".join(sections)


def extract_comments(llm: LLMClient, review_text: str, id_prefix: str) -> list[Comment]:
    """Run stage 1 extraction on one review body."""
    if not review_text.strip():
        return []
    return _call_and_parse(
        llm,
        build_extraction_prompt(review_text),
        lambda response: parse_extraction_response(response, id_prefix),
        what="extraction",
    )


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
        pass_pairs.append(
            _call_and_parse(
                llm,
                build_match_prompt(shuffled_gen, shuffled_real),
                parse_match_response,
                what="match",
            )
        )
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
        relatedness, specificity = _call_and_parse(
            llm,
            build_filter_prompt(gen_comment, real_comment),
            parse_filter_response,
            what="filter",
        )
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
        run_set: RunSet,
        model: str,
        *,
        match_passes: int = 5,
        match_threshold: int = 2,
        seed: int = DEFAULT_SEED,
        client_factory: Callable[[str], LLMClient] | None = None,
        concurrency: int = 8,
        use_cache: bool = True,
        log: Callable[[str], None] = print,
    ) -> None:
        super().__init__(run_set)
        self.model = model
        self.match_passes = match_passes
        self.match_threshold = match_threshold
        self.seed = seed
        self.client_factory = client_factory or (lambda _model: OpenRouterLLM(_model))
        self.concurrency = max(1, concurrency)
        self.use_cache = use_cache
        self._log = log
        self._cache_file = run_set.results_dir / "cache" / "comment_recall.jsonl"

    def run(self) -> dict[str, Any]:
        """Extract, align, score, and aggregate recall + n_comments (resumable).

        Two independent phases, each parallelized across the units that determine
        the work: human-comment extraction is done **once per paper** (Phase 1) and
        completes before per-(config, paper) scoring (Phase 2) so ``c_real`` is never
        recomputed per config. Per-unit seeds make the output identical regardless of
        completion order or concurrency.
        """
        run_index = self.run_set.runs_by_config_paper()
        config_ids = self.run_set.config_ids()
        paper_ids = self.run_set.paper_ids()
        cache = self._load_cache()

        c_real_by_paper, human_hash_by_paper, n_cached_h, n_run_h = self._resolve_human_comments(
            paper_ids, cache
        )
        per_paper, n_cached_r, n_run_r = self._resolve_results(
            config_ids, paper_ids, run_index, c_real_by_paper, human_hash_by_paper, cache
        )

        per_config: dict[str, dict[str, float]] = {}
        for config_id in config_ids:
            paper_stats = per_paper[config_id].values()
            per_config[config_id] = {
                "recall": mean([row["recall"] for row in paper_stats]),
                "n_comments": mean([row["n_comments"] for row in paper_stats]),
            }

        total_units = len(paper_ids) + len(config_ids) * len(paper_ids)
        n_cached = n_cached_h + n_cached_r
        self._log(
            f"comment_recall: {total_units} units "
            f"({n_cached} resumed from cache, {n_run_h + n_run_r} computed) "
            f"at concurrency {self.concurrency}"
        )

        return {
            "alignment_model": self.model,
            "prompt_version": PROMPT_VERSION,
            "match_passes": self.match_passes,
            "match_threshold": self.match_threshold,
            "per_paper": per_paper,
            "per_config": per_config,
        }

    def _resolve_human_comments(
        self,
        paper_ids: list[str],
        cache: dict[str, dict[str, Any]],
    ) -> tuple[dict[str, list[Comment]], dict[str, str], int, int]:
        """Phase 1: extract ``c_real`` once per paper (cache hits resolved up front)."""
        c_real_by_paper: dict[str, list[Comment]] = {}
        human_hash_by_paper: dict[str, str] = {}
        pending: list[tuple[str, str]] = []

        for paper_id in paper_ids:
            human_hash = _text_hash(_human_review_text(self.run_set.papers[paper_id]))
            human_hash_by_paper[paper_id] = human_hash
            key = self._creal_cache_key(paper_id, human_hash)
            cached = cache.get(key)
            if cached is not None and isinstance(cached.get("c_real"), list):
                c_real_by_paper[paper_id] = cached["c_real"]
            else:
                pending.append((paper_id, key))

        def work(item: tuple[str, str]) -> tuple[str, str, list[Comment]]:
            paper_id, key = item
            client = self.client_factory(self.model)
            return paper_id, key, extract_human_comments(client, self.run_set.papers[paper_id])

        def on_success(result: tuple[str, str, list[Comment]]) -> None:
            paper_id, key, c_real = result
            c_real_by_paper[paper_id] = c_real
            self._append_cache(key, {"kind": "c_real", "paper_id": paper_id, "c_real": c_real})

        self._run_pool(work, pending, on_success, label="human-extract")
        return c_real_by_paper, human_hash_by_paper, len(paper_ids) - len(pending), len(pending)

    def _resolve_results(
        self,
        config_ids: list[str],
        paper_ids: list[str],
        run_index: dict[tuple[str, str], Any],
        c_real_by_paper: dict[str, list[Comment]],
        human_hash_by_paper: dict[str, str],
        cache: dict[str, dict[str, Any]],
    ) -> tuple[dict[str, dict[str, Any]], int, int]:
        """Phase 2: score each (config, paper) unit, reusing the per-paper ``c_real``."""
        per_paper: dict[str, dict[str, Any]] = {config_id: {} for config_id in config_ids}
        pending: list[tuple[str, str, str, str]] = []

        for config_id in config_ids:
            for paper_id in paper_ids:
                artifacts = self.run_set.open_run(run_index[(config_id, paper_id)])
                review_text = strip_rating_line(artifacts.final_review())
                key = self._result_cache_key(
                    config_id,
                    paper_id,
                    gen_hash=_text_hash(review_text),
                    human_hash=human_hash_by_paper[paper_id],
                )
                cached = cache.get(key)
                if cached is not None and isinstance(cached.get("row"), dict):
                    per_paper[config_id][paper_id] = cached["row"]
                else:
                    pending.append((config_id, paper_id, key, review_text))

        def work(item: tuple[str, str, str, str]) -> tuple[str, str, str, dict[str, Any]]:
            config_id, paper_id, key, review_text = item
            client = self.client_factory(self.model)
            c_real = c_real_by_paper[paper_id]
            c_gen = extract_comments(client, review_text, "gen")
            candidates = match_candidates(
                client,
                c_gen,
                c_real,
                passes=self.match_passes,
                threshold=self.match_threshold,
                seed=derive_seed(self.seed, self.run_set.name, config_id, paper_id),
            )
            matches = filter_pairs(client, c_gen, c_real, candidates)
            stats = compute_recall(c_gen, c_real, matches)
            row = {**stats, "c_gen": c_gen, "c_real": c_real, "matches": matches}
            return config_id, paper_id, key, row

        def on_success(result: tuple[str, str, str, dict[str, Any]]) -> None:
            config_id, paper_id, key, row = result
            per_paper[config_id][paper_id] = row
            self._append_cache(
                key,
                {"kind": "result", "config_id": config_id, "paper_id": paper_id, "row": row},
            )

        self._run_pool(work, pending, on_success, label="result")
        n_total = len(config_ids) * len(paper_ids)
        return per_paper, n_total - len(pending), len(pending)

    def _run_pool(
        self,
        work: Callable[[Any], Any],
        items: list[Any],
        on_success: Callable[[Any], None],
        *,
        label: str,
    ) -> None:
        """Run ``work`` over ``items``, applying ``on_success`` on the main thread.

        ``on_success`` (which appends to the resume cache and fills result dicts) is
        only ever called here on the consuming thread, so cache writes need no lock.
        Failures are collected so one unit dying never discards completed work — the
        successes are cached and a summary error tells the caller to re-run to resume.
        """
        if not items:
            return

        total = len(items)
        done = 0
        failures: list[tuple[Any, Exception]] = []

        if self.concurrency == 1:
            for item in items:
                done += 1
                try:
                    value = work(item)
                except Exception as exc:  # noqa: BLE001 - one unit must not nuke progress
                    failures.append((item, exc))
                    self._log(f"[{done}/{total}] {label} FAILED: {exc!r}")
                    continue
                on_success(value)
                self._log(f"[{done}/{total}] {label}")
        else:
            with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
                futures = {pool.submit(work, item): item for item in items}
                for future in as_completed(futures):
                    item = futures[future]
                    done += 1
                    try:
                        value = future.result()
                    except Exception as exc:  # noqa: BLE001 - one unit must not nuke progress
                        failures.append((item, exc))
                        self._log(f"[{done}/{total}] {label} FAILED: {exc!r}")
                        continue
                    on_success(value)
                    self._log(f"[{done}/{total}] {label}")

        if failures:
            raise RuntimeError(
                f"{len(failures)}/{total} {label} units failed after per-call retries. "
                f"Successful units are cached at {self._cache_file}; re-run to resume only "
                f"the failures. First error: {failures[0][1]!r}"
            )

    def _creal_cache_key(self, paper_id: str, human_hash: str) -> str:
        """Key for one paper's human-comment extraction (``c_real``)."""
        raw = "|".join(
            (
                "c_real",
                self.run_set.name,
                paper_id,
                self.model,
                PROMPT_VERSION,
                human_hash,
            )
        )
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

    def _result_cache_key(
        self,
        config_id: str,
        paper_id: str,
        *,
        gen_hash: str,
        human_hash: str,
    ) -> str:
        """Key for one (config, paper) result.

        Folds in everything that changes the output: run-set, config, paper, model,
        prompt version, the match-pass/threshold/seed knobs, the generated review's
        hash (so a regenerated review misses cache), and the human-review hash (since
        matches depend on ``c_real`` too).
        """
        raw = "|".join(
            (
                "result",
                self.run_set.name,
                config_id,
                paper_id,
                self.model,
                PROMPT_VERSION,
                str(self.match_passes),
                str(self.match_threshold),
                str(self.seed),
                gen_hash,
                human_hash,
            )
        )
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

    def _load_cache(self) -> dict[str, dict[str, Any]]:
        """Read prior completed units keyed by cache_key (empty if caching is off)."""
        if not self.use_cache or not self._cache_file.is_file():
            return {}
        cache: dict[str, dict[str, Any]] = {}
        for line in self._cache_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = record.get("cache_key")
            if isinstance(key, str):
                cache[key] = record
        return cache

    def _append_cache(self, cache_key: str, payload: dict[str, Any]) -> None:
        """Append one completed unit to the resume cache."""
        if not self.use_cache:
            return
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
        record = {"cache_key": cache_key, **payload}
        with self._cache_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


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
    parser.add_argument(
        "--concurrency",
        type=int,
        default=8,
        help="Parallel (config, paper) units / human extractions (default 8; use 1 for "
        "sequential). Each unit issues its own OpenRouter calls; raise cautiously to "
        "avoid alignment-model 429s (per-call retry/backoff absorbs transient ones).",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore and do not write the resume cache "
        "(eval/results/<set>/cache/comment_recall.jsonl).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for Metric 2."""
    args = build_parser().parse_args(argv)
    run_set = load_run_set(args)
    metric = CommentRecallMetric(
        run_set,
        args.model,
        match_passes=args.match_passes,
        match_threshold=args.match_threshold,
        seed=args.seed,
        concurrency=args.concurrency,
        use_cache=not args.no_cache,
    )
    output_path = metric.write()
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
