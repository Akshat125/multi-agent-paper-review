"""Metric 3 — per-role cross-model diversity (H2 mechanism).

Measures how much different models diverge in their per-role outputs using
embedding cosine similarity, restricted to the homogeneous-config runs
(All-A / All-B / All-C) where each config runs one model in all roles.

Two descriptive jobs only:
  (1) Precondition — models genuinely produce different content per role.
  (2) Localization — which role is most model-sensitive (feeds DH3/DH5).

This is NOT a diversity→quality regression; that attribution lives in the
DH5 single-role swaps and Metric 2 recall.
"""

from __future__ import annotations

import argparse
import math
from typing import Any, Protocol

import numpy as np

from metrics.base import Metric
from utils.batch import Batch, ROLES
from utils.cli import add_common_args, load_batch
from utils.stats import mean

DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class Embedder(Protocol):
    """Minimal embedding interface; injectable so tests can avoid a real model."""

    def encode(self, texts: list[str]) -> np.ndarray:
        """Return an (n, d) float array of embeddings for the given texts."""
        ...


class SentenceTransformerEmbedder:
    """Production embedder backed by sentence-transformers (P5)."""

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL) -> None:
        from sentence_transformers import SentenceTransformer  # type: ignore[import]

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        return self._model.encode(  # type: ignore[return-value]
            texts, normalize_embeddings=True, show_progress_bar=False
        )


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------


def cosine_sim_matrix(embeddings: np.ndarray) -> np.ndarray:
    """(n, n) cosine similarity matrix from an (n, d) embedding array."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    normed = embeddings / norms
    return normed @ normed.T


def irsim(sim_matrix: np.ndarray) -> float:
    """Mean pairwise cosine similarity (off-diagonal) for M models.

    Formula from eval-metrics.md §3:
        IRSim_r(p) = 1/(M(M-1)) * Σ_{i≠j} cos(E(o_r^i), E(o_r^j))
    """
    m = sim_matrix.shape[0]
    if m < 2:
        return 1.0
    off_diag = sim_matrix.sum() - np.trace(sim_matrix)
    return float(off_diag / (m * (m - 1)))


def vendi_score(sim_matrix: np.ndarray) -> float:
    """Effective number of distinct outputs via matrix-entropy (Von Neumann).

    Formula from eval-metrics.md §3:
        K = sim_matrix / M  (normalized so trace = 1)
        VS = exp(-Σ λ_k log λ_k)     where λ_k are eigenvalues of K
    Result in [1, M]: 1 = all identical, M = all orthogonal.
    """
    m = sim_matrix.shape[0]
    if m < 2:
        return 1.0
    k = sim_matrix / m
    eigenvalues = np.linalg.eigvalsh(k)
    eigenvalues = eigenvalues[eigenvalues > 0]
    entropy = -float(np.sum(eigenvalues * np.log(eigenvalues)))
    return float(math.exp(entropy))


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------


def collect_homogeneous_configs(batch: Batch) -> list[str]:
    """Sorted config_ids of homogeneous runs in this batch."""
    return sorted(cid for cid, cfg in batch.configs.items() if cfg.homogeneous)


def compute_diversity(
    batch: Batch,
    embedder: Embedder,
    *,
    compute_vendi: bool = True,
) -> dict[str, Any]:
    """Per-role diversity over the homogeneous configs of a batch.

    For each role × paper, collects one output per homogeneous config, embeds
    them, and computes IRSim-derived diversity (and optionally Vendi Score).
    Aggregates per role via macro-average over papers.
    """
    homo_ids = collect_homogeneous_configs(batch)
    if len(homo_ids) < 2:
        raise ValueError(
            f"Metric 3 requires ≥2 homogeneous configs; "
            f"found {len(homo_ids)}: {homo_ids}"
        )

    run_index = batch.runs_by_config_paper()
    paper_ids = batch.paper_ids()

    per_role_per_paper: dict[str, dict[str, dict[str, Any]]] = {
        role: {} for role in ROLES
    }

    for role in ROLES:
        for paper_id in paper_ids:
            texts: list[str] = []
            for config_id in homo_ids:
                key = (config_id, paper_id)
                if key not in run_index:
                    continue
                artifacts = batch.open_run(run_index[key])
                texts.append(artifacts.role_output(role))

            if len(texts) < 2:
                continue

            embeddings = embedder.encode(texts)
            sim_mat = cosine_sim_matrix(embeddings)
            sim = irsim(sim_mat)
            diversity = 1.0 - sim

            entry: dict[str, Any] = {
                "n_models": len(texts),
                "similarity": round(sim, 6),
                "diversity": round(diversity, 6),
            }
            if compute_vendi:
                entry["vendi_score"] = round(vendi_score(sim_mat), 6)

            per_role_per_paper[role][paper_id] = entry

    per_role: dict[str, dict[str, Any]] = {}
    for role in ROLES:
        by_paper = per_role_per_paper[role]
        if not by_paper:
            continue
        diversities = [v["diversity"] for v in by_paper.values()]
        similarities = [v["similarity"] for v in by_paper.values()]
        agg: dict[str, Any] = {
            "diversity": round(mean(diversities), 6),
            "similarity": round(mean(similarities), 6),
            "n_papers": len(diversities),
        }
        if compute_vendi:
            vendis = [v["vendi_score"] for v in by_paper.values() if "vendi_score" in v]
            if vendis:
                agg["vendi_score"] = round(mean(vendis), 6)
        per_role[role] = agg

    return {
        "homogeneous_configs": homo_ids,
        "per_role_per_paper": per_role_per_paper,
        "per_role": per_role,
    }


# ---------------------------------------------------------------------------
# Metric class
# ---------------------------------------------------------------------------


class DiversityMetric(Metric):
    """Metric 3: per-role cross-model diversity over homogeneous config runs."""

    metric_name = "diversity"

    def __init__(
        self,
        batch: Batch,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        *,
        compute_vendi: bool = True,
        embedder: Embedder | None = None,
    ) -> None:
        super().__init__(batch)
        self.embedding_model = embedding_model
        self.compute_vendi = compute_vendi
        self._embedder = embedder

    def _get_embedder(self) -> Embedder:
        if self._embedder is not None:
            return self._embedder
        return SentenceTransformerEmbedder(self.embedding_model)

    def run(self) -> dict[str, Any]:
        embedder = self._get_embedder()
        result = compute_diversity(self.batch, embedder, compute_vendi=self.compute_vendi)
        return {
            "embedding_model": self.embedding_model,
            "compute_vendi": self.compute_vendi,
            **result,
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Metric 3: per-role cross-model diversity")
    add_common_args(parser)
    parser.add_argument(
        "--embedding-model",
        default=DEFAULT_EMBEDDING_MODEL,
        help="SentenceTransformer model id (P5)",
    )
    parser.add_argument(
        "--no-vendi",
        action="store_true",
        help="Skip Vendi Score computation",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for Metric 3."""
    args = build_parser().parse_args(argv)
    batch = load_batch(args, load_dotenv_file=False)
    metric = DiversityMetric(
        batch,
        args.embedding_model,
        compute_vendi=not args.no_vendi,
    )
    output_path = metric.write()
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
