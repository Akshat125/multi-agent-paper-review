"""Tests for Metric 4 Spearman decision score alignment."""

from __future__ import annotations

import numpy as np
import pytest

from metrics.spearman import (
    ScorePair,
    SpearmanMetric,
    bootstrap_spearman_ci,
    collect_score_pairs,
    human_mean_rating,
    spearman_alignment,
)
from utils.batch import Batch


def test_human_mean_rating(tiny_dataset):
    import json

    paper = json.loads(tiny_dataset.read_text())["papers"][0]
    assert human_mean_rating(paper) == 7.5


def test_collect_score_pairs(tiny_batch: Batch):
    pairs = collect_score_pairs(tiny_batch, "All-A")
    assert len(pairs) == 2
    assert pairs[0].paper_id == "paper_a"
    assert pairs[0].config_score == 7.0
    assert pairs[0].human_mean == 7.5


def test_spearman_alignment_perfect_positive():
    pairs = [
        ScorePair("p1", "normal", 8.0, 7.0),
        ScorePair("p2", "normal", 6.0, 5.0),
        ScorePair("p3", "controversial", 4.0, 3.0),
    ]
    result = spearman_alignment(pairs, bootstrap_n=500, seed=0)
    assert result["rho"] == 1.0
    assert result["p_value"] is not None
    assert result["n"] == 3


def test_spearman_alignment_perfect_negative():
    pairs = [
        ScorePair("p1", "normal", 4.0, 8.0),
        ScorePair("p2", "normal", 6.0, 6.0),
        ScorePair("p3", "controversial", 8.0, 4.0),
    ]
    result = spearman_alignment(pairs, bootstrap_n=500, seed=0)
    assert result["rho"] == -1.0


def test_spearman_alignment_too_few_points():
    pairs = [ScorePair("p1", "normal", 7.0, 7.5)]
    result = spearman_alignment(pairs)
    assert result["rho"] is None
    assert result["n"] == 1


def test_bootstrap_ci_bounds_perfect_correlation():
    config = np.array([7.0, 6.0, 5.0])
    human = np.array([7.5, 6.0, 4.5])
    low, high = bootstrap_spearman_ci(config, human, n_bootstrap=500, seed=0)
    assert low == 1.0
    assert high == 1.0


def test_spearman_metric_end_to_end(tiny_batch: Batch):
    metric = SpearmanMetric(tiny_batch, bootstrap_n=200, seed=0)
    payload = metric.run()

    all_a = payload["per_config"]["All-A"]["overall"]
    all_b = payload["per_config"]["All-B"]["overall"]

    assert all_a["rho"] == pytest.approx(1.0)
    assert all_b["rho"] == pytest.approx(-1.0)
    assert len(payload["per_config"]["All-A"]["pairs"]) == 2
    assert "normal" in payload["per_config"]["All-A"]["by_stratum"]
    assert "controversial" in payload["per_config"]["All-A"]["by_stratum"]
