"""Metric 1 — LLM-as-judge side-by-side win-rate.

Compares configs head-to-head on each paper using out-of-suite judges.
Position-debiased (both orders) and aggregated into per-config win rates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from prompts.win_rate import (  # noqa: E402
    DEFAULT_DIMENSIONS,
    RUBRIC_TEXT,
    RUBRIC_VERSION,
    build_comparison_prompt,
    dimension_labels,
)
from metrics.base import Metric  # noqa: E402
from utils.run_set import RunSet, RunArtifacts, unordered_pairs  # noqa: E402
from utils.cli import add_common_args, load_run_set  # noqa: E402
from utils.llm import LLMClient, OpenRouterLLM, extract_json  # noqa: E402
from utils.stats import mean  # noqa: E402

DEFAULT_JUDGES: tuple[str, ...] = (
    "openai/gpt-5-mini",
    "deepseek/deepseek-v3.2",
)

THOUGHT_RE = re.compile(r"THOUGHT:\s*(.*?)\s*REVIEW COMPARISON JSON:", re.DOTALL | re.IGNORECASE)
BETTER_ASSISTANT_RE = re.compile(
    r'"(?P<label>[^"]+) Better Assistant":\s*"(?P<verdict>A|B|Tie)"',
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RawComparison:
    """One debiased judge call: one config pair, paper, judge, and presentation order."""
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
    """Parse ScholarPeer H.2 THOUGHT + REVIEW COMPARISON JSON into verdicts."""
    thought_match = THOUGHT_RE.search(text)
    thought = thought_match.group(1).strip() if thought_match else ""

    label_map = {label: key for label, key in dimension_labels(dimensions)}
    verdicts: dict[str, str] = {}
    reasons: dict[str, str] = {}

    try:
        payload = extract_json(text)
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
    """Convert an A/B/Tie verdict into points for one config, accounting for swap order."""
    normalized = _normalize_verdict(verdict)
    if normalized is None or normalized == "Tie":
        return 0.5
    assistant_a_won = normalized == "A"
    favored_is_assistant_a = favored_config == assistant_a_config
    return 1.0 if assistant_a_won == favored_is_assistant_a else 0.0


@dataclass(frozen=True)
class _JudgeTask:
    """One atomic judge call: a config pair, paper, judge, and a fixed A/B order.

    Reviews and paper text are resolved on the main thread so worker threads only
    issue the network call + parse (no file I/O, fully self-contained, cacheable).
    """

    config_a: str
    config_b: str
    paper_id: str
    judge_model: str
    assistant_a_config: str
    assistant_a_review: str
    assistant_b_review: str
    paper_text: str
    content_hash: str
    cache_key: str


def _content_hash(assistant_a_review: str, assistant_b_review: str) -> str:
    """Stable digest of the exact reviews shown, so a regenerated review misses cache."""
    h = hashlib.sha1()
    h.update(assistant_a_review.encode("utf-8"))
    h.update(b"\x00")
    h.update(assistant_b_review.encode("utf-8"))
    return h.hexdigest()[:16]


def _cache_key(
    *,
    rubric_version: str,
    judge_model: str,
    paper_id: str,
    config_a: str,
    config_b: str,
    assistant_a_config: str,
    content_hash: str,
) -> str:
    """Deterministic key over everything that determines the judge's raw response.

    Excludes the rubric *dimensions* on purpose: they only affect parsing, so a cached
    raw response can be re-parsed for any ``--dimension`` subset without re-calling.
    """
    raw = "|".join(
        (
            rubric_version,
            judge_model,
            paper_id,
            config_a,
            config_b,
            assistant_a_config,
            content_hash,
        )
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _comparison_from_response(
    task: _JudgeTask,
    response: str,
    dimensions: tuple[str, ...],
) -> RawComparison:
    """Parse a (possibly cached) judge response into a RawComparison for ``task``."""
    thought, verdicts, reasons = parse_judge_response(response, dimensions)
    return RawComparison(
        config_a=task.config_a,
        config_b=task.config_b,
        paper_id=task.paper_id,
        judge_model=task.judge_model,
        assistant_a_config=task.assistant_a_config,
        verdicts=verdicts,
        reasons=reasons,
        thought=thought,
        raw_response=response,
    )


def _execute_task(
    task: _JudgeTask,
    client_factory: Callable[[str], LLMClient],
    dimensions: tuple[str, ...],
    *,
    max_attempts: int,
) -> tuple[RawComparison, str]:
    """Issue one judge call with bounded retries; return (comparison, raw_response).

    A fresh client is built per task so concurrent threads share no LLM state. Both
    transport errors and unparseable responses are retried (a malformed verdict may
    parse on a re-call). Raises after ``max_attempts`` failures.
    """
    client = client_factory(task.judge_model)
    prompt = build_comparison_prompt(
        task.paper_text, task.assistant_a_review, task.assistant_b_review
    )
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.call(prompt)
            comparison = _comparison_from_response(task, response, dimensions)
            return comparison, response
        except Exception as exc:  # noqa: BLE001 - retry transport + parse failures alike
            last_error = exc
            if attempt < max_attempts:
                time.sleep(min(2.0 * attempt, 8.0))
    raise RuntimeError(
        f"judge call failed after {max_attempts} attempts "
        f"(pair={task.config_a} vs {task.config_b}, paper={task.paper_id}, "
        f"judge={task.judge_model}, order_a={task.assistant_a_config}): {last_error!r}"
    ) from last_error


class SideBySideJudge:
    """Run one config-pair comparison in both Assistant A/B presentation orders."""

    def __init__(
        self,
        client_factory: Callable[[str], LLMClient],
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
        """Call the judge twice with swapped review positions."""
        client = self.client_factory(judge_model)
        raw: list[RawComparison] = []

        for assistant_a_config in (config_a, config_b):
            assistant_a_review = review_a if assistant_a_config == config_a else review_b
            assistant_b_review = review_b if assistant_a_config == config_a else review_a
            prompt = build_comparison_prompt(paper_text, assistant_a_review, assistant_b_review)
            response = client.call(prompt)
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
    """Collapse raw judge calls into pairwise scores and per-config win rates."""

    def __init__(self, dimensions: tuple[str, ...] = DEFAULT_DIMENSIONS) -> None:
        self.dimensions = dimensions

    def pairwise_scores(
        self,
        comparisons: list[RawComparison],
    ) -> dict[str, dict[str, float]]:
        """Average debiased points per config pair and rubric dimension."""
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
            pair_key: {dim: mean(values) for dim, values in dim_map.items()}
            for pair_key, dim_map in buckets.items()
        }

    def per_config_win_rates(
        self,
        config_ids: list[str],
        pairwise: dict[str, dict[str, float]],
    ) -> dict[str, dict[str, float]]:
        """Macro-average each config's score over all head-to-head opponents."""
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


class WinRateMetric(Metric):
    """Run side-by-side judging for every config pair, paper, and judge in a batch."""

    metric_name = "win_rate"

    def __init__(
        self,
        run_set: RunSet,
        judge_models: list[str],
        *,
        dimensions: tuple[str, ...] = DEFAULT_DIMENSIONS,
        client_factory: Callable[[str], LLMClient] | None = None,
        concurrency: int = 8,
        max_attempts: int = 3,
        use_cache: bool = True,
        log: Callable[[str], None] = print,
    ) -> None:
        super().__init__(run_set)
        self.judge_models = judge_models
        self.dimensions = dimensions
        self.client_factory = client_factory or (lambda model: OpenRouterLLM(model))
        self.judge = SideBySideJudge(self.client_factory, dimensions)
        self.aggregator = WinRateAggregator(dimensions)
        self.concurrency = max(1, concurrency)
        self.max_attempts = max(1, max_attempts)
        self.use_cache = use_cache
        self._log = log
        self._cache_file = run_set.results_dir / "cache" / "win_rate.jsonl"

    def run(self) -> dict[str, Any]:
        """Collect all comparisons (parallel, resumable) and aggregate win rates."""
        if len(self.judge_models) < 1:
            raise ValueError("at least one judge model is required")

        run_index = self.run_set.runs_by_config_paper()
        config_ids = self.run_set.config_ids()
        paper_ids = self.run_set.paper_ids()

        tasks = self._build_tasks(run_index, config_ids, paper_ids)
        cache = self._load_cache()

        comparisons: list[RawComparison] = []
        to_run: list[_JudgeTask] = []
        for task in tasks:
            cached = cache.get(task.cache_key)
            if cached is not None:
                try:
                    comparisons.append(
                        _comparison_from_response(task, cached, self.dimensions)
                    )
                    continue
                except ValueError:
                    pass  # stale/unparseable cache entry -> re-run this call
            to_run.append(task)

        n_cached = len(tasks) - len(to_run)
        self._log(
            f"win-rate: {len(tasks)} judge calls "
            f"({n_cached} cached, {len(to_run)} to run) "
            f"at concurrency {self.concurrency}"
        )

        comparisons.extend(self._run_tasks(to_run))
        comparisons.sort(
            key=lambda c: (
                c.config_a,
                c.config_b,
                c.paper_id,
                c.judge_model,
                c.assistant_a_config,
            )
        )

        pairwise = self.aggregator.pairwise_scores(comparisons)
        per_config = self.aggregator.per_config_win_rates(config_ids, pairwise)
        per_judge = self._per_judge_breakdown(comparisons, config_ids)
        return {
            "dimensions": list(self.dimensions),
            "judges": list(self.judge_models),
            "rubric_version": RUBRIC_VERSION,
            "rubric": RUBRIC_TEXT,
            "run_stats": {
                "n_calls": len(tasks),
                "n_cached": n_cached,
                "n_executed": len(to_run),
                "concurrency": self.concurrency,
            },
            "raw_comparisons": [_comparison_to_dict(row) for row in comparisons],
            "pairwise": pairwise,
            "per_config": per_config,
            "per_judge": per_judge,
        }

    def _build_tasks(
        self,
        run_index: dict[tuple[str, str], Any],
        config_ids: list[str],
        paper_ids: list[str],
    ) -> list[_JudgeTask]:
        """Resolve every (pair, paper, judge, order) into a self-contained judge call."""
        tasks: list[_JudgeTask] = []
        for config_a, config_b in unordered_pairs(config_ids):
            for paper_id in paper_ids:
                artifacts_a = self._artifacts_for(run_index, config_a, paper_id)
                artifacts_b = self._artifacts_for(run_index, config_b, paper_id)
                review_a = artifacts_a.final_review()
                review_b = artifacts_b.final_review()
                paper_text = artifacts_a.paper["paper_text"]
                for judge_model in self.judge_models:
                    for assistant_a_config in (config_a, config_b):
                        a_review = review_a if assistant_a_config == config_a else review_b
                        b_review = review_b if assistant_a_config == config_a else review_a
                        chash = _content_hash(a_review, b_review)
                        tasks.append(
                            _JudgeTask(
                                config_a=config_a,
                                config_b=config_b,
                                paper_id=paper_id,
                                judge_model=judge_model,
                                assistant_a_config=assistant_a_config,
                                assistant_a_review=a_review,
                                assistant_b_review=b_review,
                                paper_text=paper_text,
                                content_hash=chash,
                                cache_key=_cache_key(
                                    rubric_version=RUBRIC_VERSION,
                                    judge_model=judge_model,
                                    paper_id=paper_id,
                                    config_a=config_a,
                                    config_b=config_b,
                                    assistant_a_config=assistant_a_config,
                                    content_hash=chash,
                                ),
                            )
                        )
        return tasks

    def _run_tasks(self, to_run: list[_JudgeTask]) -> list[RawComparison]:
        """Execute pending judge calls across a thread pool, caching each success."""
        if not to_run:
            return []

        results: list[RawComparison] = []
        failures: list[tuple[_JudgeTask, Exception]] = []
        lock = threading.Lock()
        total = len(to_run)
        done = 0

        with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
            futures = {
                pool.submit(
                    _execute_task,
                    task,
                    self.client_factory,
                    self.dimensions,
                    max_attempts=self.max_attempts,
                ): task
                for task in to_run
            }
            for future in as_completed(futures):
                task = futures[future]
                done += 1
                try:
                    comparison, raw_response = future.result()
                except Exception as exc:  # noqa: BLE001 - one bad call must not nuke progress
                    failures.append((task, exc))
                    self._log(f"[{done}/{total}] FAILED {task.cache_key}: {exc!r}")
                    continue
                with lock:
                    self._append_cache(task, raw_response)
                    results.append(comparison)
                self._log(
                    f"[{done}/{total}] {task.config_a} vs {task.config_b} "
                    f"| {task.paper_id} | {task.judge_model}"
                )

        if failures:
            raise RuntimeError(
                f"{len(failures)}/{total} judge calls failed after {self.max_attempts} "
                f"attempts each. Successful calls are cached at {self._cache_file}; "
                f"re-run to resume only the failures. First error: {failures[0][1]!r}"
            )
        return results

    def _load_cache(self) -> dict[str, str]:
        """Read prior judge responses keyed by cache_key (empty if caching is off)."""
        if not self.use_cache or not self._cache_file.is_file():
            return {}
        cache: dict[str, str] = {}
        for line in self._cache_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = record.get("cache_key")
            raw = record.get("raw_response")
            if isinstance(key, str) and isinstance(raw, str):
                cache[key] = raw
        return cache

    def _append_cache(self, task: _JudgeTask, raw_response: str) -> None:
        """Append one completed judge response to the resume cache (call under lock)."""
        if not self.use_cache:
            return
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "cache_key": task.cache_key,
            "config_a": task.config_a,
            "config_b": task.config_b,
            "paper_id": task.paper_id,
            "judge_model": task.judge_model,
            "assistant_a_config": task.assistant_a_config,
            "content_hash": task.content_hash,
            "rubric_version": RUBRIC_VERSION,
            "raw_response": raw_response,
        }
        with self._cache_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _per_judge_breakdown(
        self,
        comparisons: list[RawComparison],
        config_ids: list[str],
    ) -> dict[str, dict[str, Any]]:
        """Same pairwise / per-config scores, split out per judge for agreement checks."""
        per_judge: dict[str, dict[str, Any]] = {}
        for judge_model in self.judge_models:
            judge_comparisons = [c for c in comparisons if c.judge_model == judge_model]
            judge_pairwise = self.aggregator.pairwise_scores(judge_comparisons)
            per_judge[judge_model] = {
                "pairwise": judge_pairwise,
                "per_config": self.aggregator.per_config_win_rates(config_ids, judge_pairwise),
            }
        return per_judge

    def _artifacts_for(
        self,
        run_index: dict[tuple[str, str], Any],
        config_id: str,
        paper_id: str,
    ) -> RunArtifacts:
        key = (config_id, paper_id)
        if key not in run_index:
            raise KeyError(f"missing run for config={config_id!r} paper={paper_id!r}")
        return self.run_set.open_run(run_index[key])


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



def _normalize_verdict(value: str) -> str | None:
    cleaned = value.strip().upper()
    if cleaned in {"A", "B", "TIE"}:
        return "Tie" if cleaned == "TIE" else cleaned
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Metric 1: LLM-as-judge side-by-side win-rate")
    add_common_args(parser)
    parser.add_argument(
        "--judge",
        action="append",
        dest="judges",
        default=None,
        help=(
            "Judge model id (repeatable; P4 requires >=2 out-of-suite judges; "
            f"default: {', '.join(DEFAULT_JUDGES)})"
        ),
    )
    parser.add_argument(
        "--dimension",
        action="append",
        dest="dimensions",
        help="Rubric dimension to score (repeatable; default: all core dimensions)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=8,
        help="Parallel judge calls (default 8; use 1 for sequential). Each is one "
        "OpenRouter request; raise cautiously to avoid judge-side 429s.",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Retries per judge call before failing (default 3).",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore and do not write the resume cache (eval/results/<set>/cache/win_rate.jsonl).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for Metric 1."""
    args = build_parser().parse_args(argv)

    dimensions = tuple(args.dimensions) if args.dimensions else DEFAULT_DIMENSIONS
    if "overall" not in dimensions:
        raise SystemExit("overall dimension is mandatory")

    judges = list(args.judges) if args.judges else list(DEFAULT_JUDGES)
    if len(judges) < 1:
        raise SystemExit("at least one --judge model is required")
    if len(judges) < 2:
        print(
            "warning: running with a single judge — fine for pilot pruning, but the "
            "published (Stage 2) result should use >=2 judges (P4) for agreement.",
            file=sys.stderr,
        )

    run_set = load_run_set(args)
    metric = WinRateMetric(
        run_set,
        judges,
        dimensions=dimensions,
        concurrency=args.concurrency,
        max_attempts=args.max_attempts,
        use_cache=not args.no_cache,
    )
    output_path = metric.write()
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
