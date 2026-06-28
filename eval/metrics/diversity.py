"""Metric 3 — per-role cross-model diversity (H2 mechanism).

Measures how much different models diverge in their per-role outputs using
embedding cosine similarity. Restricted to the homogeneous-config runs
(All-A / All-B / All-C, each running one model in all roles) and, within those,
to the *common papers* where every homogeneous config supplies every role. That
common-paper restriction keeps the comparison balanced (same configs, same
papers, same model count per cell) and lets an otherwise single-agent config
(e.g. All-C/llama, which only delegates on some papers) join on exactly the
papers where it produced expert outputs.

Two descriptive jobs only:
  (1) Precondition — models genuinely produce different content per role.
  (2) Localization — which role is most model-sensitive (feeds DH3/DH5).

This is NOT a diversity→quality regression; that attribution lives in the
DH5 single-role swaps and Metric 2 recall.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any, Protocol

import numpy as np

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from metrics.base import Metric  # noqa: E402
from utils.run_set import RunSet, ROLES  # noqa: E402
from utils.cli import add_common_args, load_run_set  # noqa: E402
from utils.stats import mean  # noqa: E402

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

        IRSim_r(p) = 1/(M(M-1)) * Σ_{i≠j} cos(E(o_r^i), E(o_r^j))
    """
    m = sim_matrix.shape[0]
    if m < 2:
        return 1.0
    off_diag = sim_matrix.sum() - np.trace(sim_matrix)
    return float(off_diag / (m * (m - 1)))


def vendi_score(sim_matrix: np.ndarray) -> float:
    """Effective number of distinct outputs via matrix-entropy (Von Neumann).

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


def collect_homogeneous_configs(run_set: RunSet) -> list[str]:
    """Sorted config_ids of homogeneous runs in this batch."""
    return sorted(cid for cid, cfg in run_set.configs.items() if cfg.homogeneous)


def common_papers(
    run_set: RunSet,
    config_ids: list[str],
    run_index: dict[tuple[str, str], Any],
    paper_ids: list[str],
) -> list[str]:
    """Papers where *every* given config has *every* role's output.

    This is the balanced comparison set: on these papers each config supplies a
    full set of per-role texts, so a single-agent config (e.g. All-C/llama) can
    join the cross-model comparison on exactly the papers where it did delegate.
    """
    selected: list[str] = []
    for paper_id in paper_ids:
        ok = True
        for config_id in config_ids:
            key = (config_id, paper_id)
            if key not in run_index:
                ok = False
                break
            artifacts = run_set.open_run(run_index[key])
            if not all(artifacts.has_role_output(role) for role in ROLES):
                ok = False
                break
        if ok:
            selected.append(paper_id)
    return selected


def _diversity_for_configs(
    run_set: RunSet,
    embedder: Embedder,
    config_ids: list[str],
    run_index: dict[tuple[str, str], Any],
    paper_ids: list[str],
    *,
    compute_vendi: bool,
) -> dict[str, Any]:
    """Per-role IRSim diversity over ``config_ids`` × ``paper_ids``.

    A (role, paper) cell is included only when ≥2 of the configs have that
    role's output; configs missing the output for that cell are skipped. Each
    cell records which configs contributed. Aggregates per role by
    macro-averaging over the included papers.
    """
    per_role_per_paper: dict[str, dict[str, dict[str, Any]]] = {
        role: {} for role in ROLES
    }

    for role in ROLES:
        for paper_id in paper_ids:
            texts: list[str] = []
            contributing: list[str] = []
            for config_id in config_ids:
                key = (config_id, paper_id)
                if key not in run_index:
                    continue
                artifacts = run_set.open_run(run_index[key])
                if not artifacts.has_role_output(role):
                    continue
                texts.append(artifacts.role_output(role))
                contributing.append(config_id)

            if len(texts) < 2:
                continue

            embeddings = embedder.encode(texts)
            sim_mat = cosine_sim_matrix(embeddings)
            sim = irsim(sim_mat)

            entry: dict[str, Any] = {
                "n_models": len(texts),
                "configs": contributing,
                "similarity": sim,
                "diversity": 1.0 - sim,
            }
            if compute_vendi:
                entry["vendi_score"] = vendi_score(sim_mat)

            per_role_per_paper[role][paper_id] = entry

    per_role: dict[str, dict[str, Any]] = {}
    for role in ROLES:
        by_paper = per_role_per_paper[role]
        if not by_paper:
            continue
        diversities = [v["diversity"] for v in by_paper.values()]
        similarities = [v["similarity"] for v in by_paper.values()]
        agg: dict[str, Any] = {
            "diversity": mean(diversities),
            "similarity": mean(similarities),
            "n_papers": len(diversities),
        }
        if compute_vendi:
            vendis = [v["vendi_score"] for v in by_paper.values() if "vendi_score" in v]
            if vendis:
                agg["vendi_score"] = mean(vendis)
        per_role[role] = agg

    return {"per_role_per_paper": per_role_per_paper, "per_role": per_role}


def compute_diversity(
    run_set: RunSet,
    embedder: Embedder,
    *,
    compute_vendi: bool = True,
) -> dict[str, Any]:
    """Balanced per-role cross-model diversity over the homogeneous configs.

    Restricts to ``common_papers`` — the papers where every homogeneous config
    supplies every role — so all configs are compared on the same papers with
    the same model count per cell. This naturally includes an otherwise
    single-agent config (e.g. All-C/llama) on exactly the papers where it
    delegated, rather than dropping it entirely or mixing model counts.

    For each role × common paper, embeds one output per config and computes
    IRSim-derived diversity (and optionally Vendi Score), then macro-averages
    per role over papers.
    """
    homo_ids = collect_homogeneous_configs(run_set)
    if len(homo_ids) < 2:
        raise ValueError(
            f"Metric 3 requires ≥2 homogeneous configs; "
            f"found {len(homo_ids)}: {homo_ids}"
        )

    run_index = run_set.runs_by_config_paper()
    paper_ids = run_set.paper_ids()

    papers = common_papers(run_set, homo_ids, run_index, paper_ids)
    if not papers:
        raise ValueError(
            "Metric 3 found no papers where every homogeneous config "
            f"({homo_ids}) supplies all roles; cannot compute diversity."
        )

    result = _diversity_for_configs(
        run_set, embedder, homo_ids, run_index, papers,
        compute_vendi=compute_vendi,
    )

    return {
        "homogeneous_configs": homo_ids,
        "papers": papers,
        "n_papers": len(papers),
        **result,
    }


# ---------------------------------------------------------------------------
# Metric class
# ---------------------------------------------------------------------------


class DiversityMetric(Metric):
    """Metric 3: per-role cross-model diversity over homogeneous config runs."""

    metric_name = "diversity"

    def __init__(
        self,
        run_set: RunSet,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        *,
        compute_vendi: bool = True,
        embedder: Embedder | None = None,
    ) -> None:
        super().__init__(run_set)
        self.embedding_model = embedding_model
        self.compute_vendi = compute_vendi
        self._embedder = embedder

    def _get_embedder(self) -> Embedder:
        if self._embedder is not None:
            return self._embedder
        return SentenceTransformerEmbedder(self.embedding_model)

    def run(self) -> dict[str, Any]:
        embedder = self._get_embedder()
        result = compute_diversity(self.run_set, embedder, compute_vendi=self.compute_vendi)
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
    run_set = load_run_set(args, load_dotenv_file=False)
    metric = DiversityMetric(
        run_set,
        args.embedding_model,
        compute_vendi=not args.no_vendi,
    )
    output_path = metric.write()
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
