"""Tests for eval/metrics/batch.py."""

from __future__ import annotations

import json

import pytest

from metrics.batch import Batch, unordered_pairs, write_metric


def test_unordered_pairs():
    assert unordered_pairs(["b", "a", "c"]) == [("a", "b"), ("a", "c"), ("b", "c")]


def test_batch_loads_runs_and_open_run(tiny_batch: Batch):
    index = tiny_batch.runs_by_config_paper()
    assert len(index) == 4

    artifacts = tiny_batch.open_run(index[("All-A", "paper_a")])
    assert "Review A on paper_a" in artifacts.final_review()
    assert artifacts.paper["id"] == "paper_a"


def test_batch_rejects_duplicate_runs(tmp_path, tiny_dataset):
    batch_dir = tmp_path / "eval" / "runs" / "dup"
    batch_dir.mkdir(parents=True)
    (batch_dir / "configs.json").write_text(
        json.dumps(
            {
                "All-A": {
                    "models": {
                        "leader": "m",
                        "clarity": "m",
                        "experiments": "m",
                        "impact": "m",
                    },
                    "homogeneous": True,
                }
            }
        ),
        encoding="utf-8",
    )
    run_dir = tmp_path / "eval" / "outputs" / "run1"
    run_dir.mkdir(parents=True)
    for name in ("final_review.md", "review.json", "trace.jsonl"):
        (run_dir / name).write_text("{}", encoding="utf-8")

    rel = str(run_dir.relative_to(tmp_path))
    rows = [
        {"config_id": "All-A", "paper_id": "paper_a", "run_dir": rel, "replicate": 0},
        {"config_id": "All-A", "paper_id": "paper_a", "run_dir": rel, "replicate": 0},
    ]
    with (batch_dir / "runs.jsonl").open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")

    with pytest.raises(ValueError, match="duplicate registry entry"):
        Batch.load("dup", root=tmp_path, dataset_path=tiny_dataset)


def test_write_metric_envelope(tiny_batch: Batch):
    path = write_metric(tiny_batch, "win_rate", {"per_config": {"All-A": {"overall": 0.75}}})
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["metric"] == "win_rate"
    assert payload["batch"] == "pilot"
    assert "computed_at" in payload
    assert payload["per_config"]["All-A"]["overall"] == 0.75
