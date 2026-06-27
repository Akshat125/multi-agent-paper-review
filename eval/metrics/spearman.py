"""Metric 4 — decision score alignment via Spearman rank correlation.

Judge-free anchor: does each config's ``review.json`` rating rank papers the same
way as human mean scores? Reports overall and per-stratum ρ with p-value and bootstrap CI.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from metrics.base import Metric  # noqa: E402
from utils.run_set import RunSet  # noqa: E402
from utils.cli import add_common_args, load_run_set  # noqa: E402
from utils.stats import derive_seed  # noqa: E402

STRATA = ("normal", "controversial")
DEFAULT_SEED = 42


@dataclass(frozen=True)
class ScorePair:
    paper_id: str
    stratum: str
    config_score: float
    human_mean: float


def human_mean_rating(paper: dict[str, Any]) -> float:
    """Ground-truth decision score: mean of human reviewer ratings for one paper."""
    ratings = paper["ratings"]
    return sum(ratings) / len(ratings)


def collect_score_pairs(run_set: RunSet, config_id: str) -> list[ScorePair]:
    """Join config ``review.json`` ratings with dataset human means for one config."""
    run_index = run_set.runs_by_config_paper()
    pairs: list[ScorePair] = []
    for paper_id in run_set.paper_ids():
        paper = run_set.papers[paper_id]
        run = run_index[(config_id, paper_id)]
        artifacts = run_set.open_run(run)
        pairs.append(
            ScorePair(
                paper_id=paper_id,
                stratum=paper["stratum"],
                config_score=artifacts.review_rating(),
                human_mean=human_mean_rating(paper),
            )
        )
    return pairs


def _pairs_to_arrays(pairs: list[ScorePair]) -> tuple[np.ndarray, np.ndarray]:
    config_scores = np.array([pair.config_score for pair in pairs], dtype=float)
    human_scores = np.array([pair.human_mean for pair in pairs], dtype=float)
    return config_scores, human_scores


def bootstrap_spearman_ci(
    config_scores: np.ndarray,
    human_scores: np.ndarray,
    *,
    n_bootstrap: int = 2000,
    seed: int = DEFAULT_SEED,
) -> tuple[float, float]:
    """Percentile bootstrap CI for Spearman ρ over paper-level resamples."""
    n = len(config_scores)
    if n < 2:
        return float("nan"), float("nan")

    rng = np.random.default_rng(seed)
    rhos: list[float] = []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        sample_config = config_scores[idx]
        sample_human = human_scores[idx]
        if np.unique(sample_config).size < 2 or np.unique(sample_human).size < 2:
            continue
        rho, _ = spearmanr(sample_config, sample_human)
        if not np.isnan(rho):
            rhos.append(float(rho))

    if not rhos:
        return float("nan"), float("nan")

    low, high = np.percentile(rhos, [2.5, 97.5])
    return float(low), float(high)


def spearman_alignment(
    pairs: list[ScorePair],
    *,
    bootstrap_n: int = 2000,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    """Compute tie-corrected Spearman ρ, p-value, and bootstrap CI for one slice."""
    n = len(pairs)
    if n < 2:
        return {
            "rho": None,
            "p_value": None,
            "ci_low": None,
            "ci_high": None,
            "n": n,
        }

    config_scores, human_scores = _pairs_to_arrays(pairs)
    rho, p_value = spearmanr(config_scores, human_scores)
    ci_low, ci_high = bootstrap_spearman_ci(
        config_scores,
        human_scores,
        n_bootstrap=bootstrap_n,
        seed=seed,
    )

    return {
        "rho": None if np.isnan(rho) else float(rho),
        "p_value": None if np.isnan(p_value) else float(p_value),
        "ci_low": None if np.isnan(ci_low) else ci_low,
        "ci_high": None if np.isnan(ci_high) else ci_high,
        "n": n,
    }


def pairs_to_dicts(pairs: list[ScorePair]) -> list[dict[str, Any]]:
    """Serialize score pairs for inspection in metric output."""
    return [
        {
            "paper_id": pair.paper_id,
            "stratum": pair.stratum,
            "config_score": pair.config_score,
            "human_mean": pair.human_mean,
        }
        for pair in pairs
    ]


class SpearmanMetric(Metric):
    """Spearman rank correlation between config ratings and human mean scores."""

    metric_name = "spearman"

    def __init__(
        self,
        run_set: RunSet,
        *,
        bootstrap_n: int = 2000,
        seed: int = DEFAULT_SEED,
    ) -> None:
        super().__init__(run_set)
        self.bootstrap_n = bootstrap_n
        self.seed = seed

    def run(self) -> dict[str, Any]:
        """Compute overall and per-stratum alignment for every config in the batch."""
        per_config: dict[str, Any] = {}

        for config_id in self.run_set.config_ids():
            pairs = collect_score_pairs(self.run_set, config_id)
            overall = spearman_alignment(
                pairs,
                bootstrap_n=self.bootstrap_n,
                seed=self.seed,
            )
            by_stratum = {
                stratum: spearman_alignment(
                    [pair for pair in pairs if pair.stratum == stratum],
                    bootstrap_n=self.bootstrap_n,
                    seed=derive_seed(self.seed, self.run_set.name, stratum),
                )
                for stratum in STRATA
            }
            per_config[config_id] = {
                "overall": overall,
                "by_stratum": by_stratum,
                "pairs": pairs_to_dicts(pairs),
            }

        return {
            "bootstrap_n": self.bootstrap_n,
            "per_config": per_config,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Metric 4: Spearman decision score alignment")
    add_common_args(parser)
    parser.add_argument(
        "--bootstrap-n",
        type=int,
        default=2000,
        help="Bootstrap resamples for the Spearman CI",
    )
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED, help="RNG seed for bootstrap resampling"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for Metric 4."""
    args = build_parser().parse_args(argv)
    run_set = load_run_set(args, load_dotenv_file=False)
    metric = SpearmanMetric(run_set, bootstrap_n=args.bootstrap_n, seed=args.seed)
    output_path = metric.write()
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
