"""Tests for Metric 3 — per-role cross-model diversity."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from metrics.diversity import (
    DEFAULT_EMBEDDING_MODEL,
    DiversityMetric,
    collect_homogeneous_configs,
    compute_diversity,
    cosine_sim_matrix,
    irsim,
    vendi_score,
)
from utils.batch import Batch


# ---------------------------------------------------------------------------
# Fake embedder
# ---------------------------------------------------------------------------


class FakeEmbedder:
    """Returns pre-configured vectors keyed by text content."""

    def __init__(self, vectors: dict[str, np.ndarray]) -> None:
        self._vectors = vectors

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.stack([self._vectors[t] for t in texts])


def _unit(v: list[float]) -> np.ndarray:
    a = np.array(v, dtype=float)
    return a / np.linalg.norm(a)


# ---------------------------------------------------------------------------
# Math unit tests
# ---------------------------------------------------------------------------


def test_irsim_identical_embeddings():
    v = _unit([1.0, 0.0, 0.0])
    embeddings = np.stack([v, v, v])
    sim_mat = cosine_sim_matrix(embeddings)
    assert irsim(sim_mat) == pytest.approx(1.0)


def test_irsim_orthogonal_embeddings():
    e = np.eye(3)
    sim_mat = cosine_sim_matrix(e)
    assert irsim(sim_mat) == pytest.approx(0.0)


def test_irsim_single_raises_no_error_and_returns_one():
    v = _unit([1.0, 0.0])
    sim_mat = cosine_sim_matrix(np.stack([v]))
    assert irsim(sim_mat) == pytest.approx(1.0)


def test_vendi_identical_is_one():
    v = _unit([1.0, 0.0, 0.0])
    embeddings = np.stack([v, v, v])
    sim_mat = cosine_sim_matrix(embeddings)
    assert vendi_score(sim_mat) == pytest.approx(1.0, abs=1e-5)


def test_vendi_orthogonal_equals_n_models():
    e = np.eye(3)
    sim_mat = cosine_sim_matrix(e)
    assert vendi_score(sim_mat) == pytest.approx(3.0, abs=1e-5)


def test_vendi_two_identical_is_one():
    v = _unit([1.0, 0.0])
    sim_mat = cosine_sim_matrix(np.stack([v, v]))
    assert vendi_score(sim_mat) == pytest.approx(1.0, abs=1e-5)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

ROLES_LABELS = {
    "leader": "Review Leader",
    "clarity": "Clarity Reviewer",
    "experiments": "Experiments Reviewer",
    "impact": "Impact Reviewer",
}


def _write_trace(
    run_dir: Path,
    role_outputs: dict[str, str],
    model: str = "model-x",
) -> None:
    """Write trace.jsonl with run_header + delegation_finished per expert role."""
    records: list[dict[str, Any]] = [
        {
            "type": "run_header",
            "models": {role: model for role in ROLES_LABELS},
            "roles": ROLES_LABELS,
        }
    ]
    for role_key, label in ROLES_LABELS.items():
        if role_key == "leader":
            continue
        output = role_outputs.get(role_key, f"expert output for {role_key}")
        records.append(
            {
                "type": "delegation_finished",
                "expert_role": label,
                "output": output,
                "output_chars": len(output),
                "status": "ok",
            }
        )
    records.append({"type": "run_footer", "duration_ms": 1000})

    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "trace.jsonl").write_text(
        "\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8"
    )


def _write_run(
    run_dir: Path,
    review_text: str,
    role_outputs: dict[str, str],
    rating: int = 7,
    model: str = "model-x",
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "final_review.md").write_text(review_text, encoding="utf-8")
    (run_dir / "review.json").write_text(
        json.dumps({"summary": "s", "strengths": "s", "weaknesses": "w",
                    "questions": "q", "rating": rating}),
        encoding="utf-8",
    )
    _write_trace(run_dir, role_outputs, model=model)


@pytest.fixture
def diversity_batch(tmp_path: Path) -> tuple[Batch, dict[str, dict[str, str]]]:
    """Batch with three homogeneous configs (All-A/B/C) over two papers.

    Returns the batch and a mapping of (config_id, paper_id) → role_outputs
    so tests can inspect what was written.
    """
    dataset = {
        "papers": [
            {"id": "p1", "decision": "Accept", "stratum": "normal",
             "ratings": [7, 8], "paper_text": "Paper one.", "human_reviews": []},
            {"id": "p2", "decision": "Reject", "stratum": "controversial",
             "ratings": [4, 5], "paper_text": "Paper two.", "human_reviews": []},
        ]
    }
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(json.dumps(dataset), encoding="utf-8")

    configs = {
        "All-A": {"models": {r: "model-a" for r in ROLES_LABELS}, "homogeneous": True},
        "All-B": {"models": {r: "model-b" for r in ROLES_LABELS}, "homogeneous": True},
        "All-C": {"models": {r: "model-c" for r in ROLES_LABELS}, "homogeneous": True},
        "het-01": {
            "models": {"leader": "model-a", "clarity": "model-b",
                       "experiments": "model-c", "impact": "model-a"},
            "homogeneous": False,
        },
    }

    batch_dir = tmp_path / "eval" / "runs" / "test_batch"
    batch_dir.mkdir(parents=True)
    (batch_dir / "configs.json").write_text(json.dumps(configs), encoding="utf-8")

    # Distinct per-role outputs for each config so diversity > 0
    role_outputs_by_config: dict[str, dict[str, str]] = {
        "All-A": {
            "clarity": "Model A on clarity: very concise.",
            "experiments": "Model A on experiments: robust baselines.",
            "impact": "Model A on impact: highly significant.",
        },
        "All-B": {
            "clarity": "Model B on clarity: verbose and repetitive.",
            "experiments": "Model B on experiments: weak ablations.",
            "impact": "Model B on impact: incremental contribution.",
        },
        "All-C": {
            "clarity": "Model C on clarity: missing key details.",
            "experiments": "Model C on experiments: missing comparisons.",
            "impact": "Model C on impact: narrowly applicable.",
        },
        "het-01": {
            "clarity": "Het on clarity.",
            "experiments": "Het on experiments.",
            "impact": "Het on impact.",
        },
    }

    runs: list[dict[str, Any]] = []
    for config_id in configs:
        for paper_id in ("p1", "p2"):
            run_dir = tmp_path / "eval" / "outputs" / f"{config_id}_{paper_id}"
            review_text = f"Final review by {config_id} on {paper_id}.\nRATING: 7"
            _write_run(
                run_dir,
                review_text,
                role_outputs_by_config[config_id],
                model=configs[config_id]["models"]["leader"],
            )
            runs.append({
                "config_id": config_id,
                "paper_id": paper_id,
                "run_dir": str(run_dir.relative_to(tmp_path)),
                "replicate": 0,
            })

    with (batch_dir / "runs.jsonl").open("w", encoding="utf-8") as fh:
        for row in runs:
            fh.write(json.dumps(row) + "\n")

    batch = Batch.load("test_batch", root=tmp_path, dataset_path=dataset_path)
    return batch, role_outputs_by_config


# ---------------------------------------------------------------------------
# RunArtifacts.role_output tests
# ---------------------------------------------------------------------------


def test_role_output_leader(diversity_batch):
    batch, _ = diversity_batch
    run_index = batch.runs_by_config_paper()
    artifacts = batch.open_run(run_index[("All-A", "p1")])
    output = artifacts.role_output("leader")
    assert "RATING: 7" in output


def test_role_output_expert(diversity_batch):
    batch, role_outputs = diversity_batch
    run_index = batch.runs_by_config_paper()
    artifacts = batch.open_run(run_index[("All-B", "p1")])
    assert artifacts.role_output("clarity") == role_outputs["All-B"]["clarity"]
    assert artifacts.role_output("experiments") == role_outputs["All-B"]["experiments"]
    assert artifacts.role_output("impact") == role_outputs["All-B"]["impact"]


def test_role_output_unknown_role_raises(diversity_batch):
    batch, _ = diversity_batch
    run_index = batch.runs_by_config_paper()
    artifacts = batch.open_run(run_index[("All-A", "p1")])
    with pytest.raises(KeyError, match="not found in run_header.roles"):
        artifacts.role_output("nonexistent")


# ---------------------------------------------------------------------------
# collect_homogeneous_configs
# ---------------------------------------------------------------------------


def test_collect_homogeneous_configs(diversity_batch):
    batch, _ = diversity_batch
    homo = collect_homogeneous_configs(batch)
    assert homo == ["All-A", "All-B", "All-C"]


# ---------------------------------------------------------------------------
# compute_diversity
# ---------------------------------------------------------------------------


def _make_embedder_from_outputs(
    role_outputs: dict[str, dict[str, str]],
    configs: list[str],
) -> FakeEmbedder:
    """Build a FakeEmbedder that assigns unique orthogonal-ish vectors per text."""
    dim = 8
    rng = np.random.default_rng(0)

    vectors: dict[str, np.ndarray] = {}
    # leader outputs (final_review.md content)
    for i, config_id in enumerate(configs):
        for paper_id in ("p1", "p2"):
            text = f"Final review by {config_id} on {paper_id}.\nRATING: 7"
            v = rng.standard_normal(dim)
            vectors[text] = v / np.linalg.norm(v)

    # expert role outputs
    for config_id in configs:
        for role_key in ("clarity", "experiments", "impact"):
            text = role_outputs[config_id][role_key]
            v = rng.standard_normal(dim)
            vectors[text] = v / np.linalg.norm(v)

    return FakeEmbedder(vectors)


def test_compute_diversity_uses_only_homogeneous(diversity_batch):
    batch, role_outputs = diversity_batch
    homo = collect_homogeneous_configs(batch)
    embedder = _make_embedder_from_outputs(role_outputs, homo)

    result = compute_diversity(batch, embedder, compute_vendi=False)

    assert result["homogeneous_configs"] == homo
    assert "het-01" not in str(result["homogeneous_configs"])


def test_compute_diversity_per_role_keys(diversity_batch):
    batch, role_outputs = diversity_batch
    homo = collect_homogeneous_configs(batch)
    embedder = _make_embedder_from_outputs(role_outputs, homo)

    result = compute_diversity(batch, embedder, compute_vendi=True)

    for role in ("leader", "clarity", "experiments", "impact"):
        assert role in result["per_role"], f"missing role {role!r} in per_role"
        assert role in result["per_role_per_paper"]

    for role in ("leader", "clarity", "experiments", "impact"):
        for paper_id in ("p1", "p2"):
            assert paper_id in result["per_role_per_paper"][role]


def test_compute_diversity_values_in_range(diversity_batch):
    batch, role_outputs = diversity_batch
    homo = collect_homogeneous_configs(batch)
    embedder = _make_embedder_from_outputs(role_outputs, homo)

    result = compute_diversity(batch, embedder, compute_vendi=True)

    for role, agg in result["per_role"].items():
        assert 0.0 <= agg["similarity"] <= 1.0, role
        assert 0.0 <= agg["diversity"] <= 1.0, role
        assert agg["diversity"] == pytest.approx(1.0 - agg["similarity"], abs=1e-5)
        assert 1.0 <= agg["vendi_score"] <= 3.0, role
        assert agg["n_papers"] == 2


def test_compute_diversity_identical_texts_gives_zero_diversity(tmp_path: Path):
    """When all models produce the exact same output, diversity must be 0."""
    dataset = {
        "papers": [
            {"id": "p1", "decision": "Accept", "stratum": "normal",
             "ratings": [7], "paper_text": "X", "human_reviews": []}
        ]
    }
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(json.dumps(dataset), encoding="utf-8")

    same_text = "Identical expert output."
    configs = {
        "All-A": {"models": {r: "model-a" for r in ROLES_LABELS}, "homogeneous": True},
        "All-B": {"models": {r: "model-b" for r in ROLES_LABELS}, "homogeneous": True},
    }
    batch_dir = tmp_path / "eval" / "runs" / "same"
    batch_dir.mkdir(parents=True)
    (batch_dir / "configs.json").write_text(json.dumps(configs), encoding="utf-8")

    runs = []
    for config_id in configs:
        run_dir = tmp_path / "eval" / "outputs" / f"{config_id}_p1"
        _write_run(run_dir, f"Leader review.\nRATING: 7",
                   {"clarity": same_text, "experiments": same_text, "impact": same_text})
        runs.append({"config_id": config_id, "paper_id": "p1",
                     "run_dir": str(run_dir.relative_to(tmp_path)), "replicate": 0})

    (batch_dir / "runs.jsonl").write_text(
        "\n".join(json.dumps(r) for r in runs) + "\n", encoding="utf-8"
    )

    batch = Batch.load("same", root=tmp_path, dataset_path=dataset_path)

    v = _unit([1.0, 0.0, 0.0])
    embedder = FakeEmbedder({
        same_text: v,
        "Leader review.\nRATING: 7": v,
    })

    result = compute_diversity(batch, embedder, compute_vendi=True)

    for role in ("clarity", "experiments", "impact"):
        assert result["per_role"][role]["diversity"] == pytest.approx(0.0, abs=1e-5)
        assert result["per_role"][role]["vendi_score"] == pytest.approx(1.0, abs=1e-5)


def test_compute_diversity_raises_without_homogeneous(tmp_path: Path):
    dataset = {
        "papers": [
            {"id": "p1", "decision": "Accept", "stratum": "normal",
             "ratings": [7], "paper_text": "X", "human_reviews": []}
        ]
    }
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(json.dumps(dataset), encoding="utf-8")

    configs = {
        "het-only": {
            "models": {"leader": "a", "clarity": "b", "experiments": "c", "impact": "a"},
            "homogeneous": False,
        }
    }
    batch_dir = tmp_path / "eval" / "runs" / "nohomo"
    batch_dir.mkdir(parents=True)
    (batch_dir / "configs.json").write_text(json.dumps(configs), encoding="utf-8")

    run_dir = tmp_path / "eval" / "outputs" / "het-only_p1"
    _write_run(run_dir, "Review.\nRATING: 7",
               {"clarity": "c", "experiments": "e", "impact": "i"})
    (batch_dir / "runs.jsonl").write_text(
        json.dumps({"config_id": "het-only", "paper_id": "p1",
                    "run_dir": str(run_dir.relative_to(tmp_path)), "replicate": 0}) + "\n",
        encoding="utf-8",
    )

    batch = Batch.load("nohomo", root=tmp_path, dataset_path=dataset_path)

    with pytest.raises(ValueError, match="≥2 homogeneous"):
        compute_diversity(batch, FakeEmbedder({}))


# ---------------------------------------------------------------------------
# DiversityMetric end-to-end
# ---------------------------------------------------------------------------


def test_diversity_metric_run(diversity_batch):
    batch, role_outputs = diversity_batch
    homo = collect_homogeneous_configs(batch)
    embedder = _make_embedder_from_outputs(role_outputs, homo)

    metric = DiversityMetric(batch, embedder=embedder)
    payload = metric.run()

    assert payload["embedding_model"] == DEFAULT_EMBEDDING_MODEL
    assert payload["compute_vendi"] is True
    assert payload["homogeneous_configs"] == homo
    assert set(payload["per_role"].keys()) == {"leader", "clarity", "experiments", "impact"}


def test_diversity_metric_write(diversity_batch, tmp_path: Path):
    batch, role_outputs = diversity_batch
    homo = collect_homogeneous_configs(batch)
    embedder = _make_embedder_from_outputs(role_outputs, homo)

    metric = DiversityMetric(batch, embedder=embedder)
    out_path = metric.write()

    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["metric"] == "diversity"
    assert data["batch"] == "test_batch"
    assert "computed_at" in data
    assert "per_role" in data
