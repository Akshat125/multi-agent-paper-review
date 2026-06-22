"""Shared fixtures for eval tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from metrics.batch import Batch


@pytest.fixture
def tiny_dataset(tmp_path: Path) -> Path:
    payload = {
        "papers": [
            {
                "id": "paper_a",
                "decision": "Accept",
                "stratum": "normal",
                "ratings": [7, 8, 7, 8],
                "paper_text": "\\begin{abstract}Alpha abstract.\\end{abstract}",
                "human_reviews": [],
            },
            {
                "id": "paper_b",
                "decision": "Reject",
                "stratum": "controversial",
                "ratings": [4, 6, 5, 5],
                "paper_text": "Beta body " * 100,
                "human_reviews": [],
            },
        ]
    }
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def write_run_artifacts(run_dir: Path, review_text: str, rating: int = 7) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "final_review.md").write_text(review_text, encoding="utf-8")
    (run_dir / "review.json").write_text(
        json.dumps(
            {
                "summary": "summary",
                "strengths": "strengths",
                "weaknesses": "weaknesses",
                "questions": "questions",
                "rating": rating,
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "trace.jsonl").write_text(
        json.dumps({"type": "run_footer", "duration_ms": 1000}) + "\n",
        encoding="utf-8",
    )


@pytest.fixture
def tiny_batch(tmp_path: Path, tiny_dataset: Path) -> Batch:
    batch_dir = tmp_path / "eval" / "runs" / "pilot"
    batch_dir.mkdir(parents=True)

    configs = {
        "All-A": {
            "models": {
                "leader": "model-a",
                "clarity": "model-a",
                "experiments": "model-a",
                "impact": "model-a",
            },
            "homogeneous": True,
        },
        "All-B": {
            "models": {
                "leader": "model-b",
                "clarity": "model-b",
                "experiments": "model-b",
                "impact": "model-b",
            },
            "homogeneous": True,
        },
    }
    (batch_dir / "configs.json").write_text(json.dumps(configs), encoding="utf-8")

    runs = []
    for config_id, paper_id, review in (
        ("All-A", "paper_a", "Review A on paper_a\nRATING: 7"),
        ("All-A", "paper_b", "Review A on paper_b\nRATING: 6"),
        ("All-B", "paper_a", "Review B on paper_a\nRATING: 8"),
        ("All-B", "paper_b", "Review B on paper_b\nRATING: 5"),
    ):
        run_dir = tmp_path / "eval" / "outputs" / f"{config_id}_{paper_id}"
        write_run_artifacts(run_dir, review)
        rel = run_dir.relative_to(tmp_path)
        runs.append(
            {
                "config_id": config_id,
                "paper_id": paper_id,
                "run_dir": str(rel),
                "replicate": 0,
            }
        )

    with (batch_dir / "runs.jsonl").open("w", encoding="utf-8") as fh:
        for row in runs:
            fh.write(json.dumps(row) + "\n")

    return Batch.load("pilot", root=tmp_path, dataset_path=tiny_dataset)
