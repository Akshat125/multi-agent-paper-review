"""Tests for eval/experiments.py orchestration (no live model backend)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments import (
    BatchPaths,
    dry_run_report,
    execute,
    plan_runs,
    write_configs,
)
from utils.batch import Batch
from utils.spec import resolve_spec

RAW_SPEC = {
    "batch": "pilot",
    "pool": {"A": "slug-a", "B": "slug-b", "C": "slug-c"},
    "configs": {
        "All-A": {"leader": "A", "clarity": "A", "experiments": "A", "impact": "A"},
        "All-B": {"leader": "B", "clarity": "B", "experiments": "B", "impact": "B"},
        "All-C": {"leader": "C", "clarity": "C", "experiments": "C", "impact": "C"},
    },
    "papers": "all",
    "replicates": 1,
}


@pytest.fixture
def dataset(tmp_path: Path) -> Path:
    payload = {
        "papers": [
            {
                "id": "p1",
                "decision": "Accept",
                "stratum": "normal",
                "ratings": [7, 8, 7, 8],
                "paper_text": "Paper one body.",
                "human_reviews": [],
            },
            {
                "id": "p2",
                "decision": "Reject",
                "stratum": "controversial",
                "ratings": [4, 6, 5, 5],
                "paper_text": "Paper two body.",
                "human_reviews": [],
            },
        ]
    }
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _load_papers(dataset: Path) -> dict:
    data = json.loads(dataset.read_text(encoding="utf-8"))
    return {p["id"]: p for p in data["papers"]}


def fake_runner_factory(fail_on: set[str] | None = None):
    """Build a runner that writes valid artifacts, optionally failing some combos."""
    fail_on = fail_on or set()
    calls: list[str] = []

    def runner(models, paper_text, paper_id, output_dir, run_name_):
        calls.append(run_name_)
        if run_name_ in fail_on:
            raise RuntimeError("boom")
        run_dir = output_dir / run_name_
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "final_review.md").write_text("review\nRATING: 7", encoding="utf-8")
        (run_dir / "review.json").write_text(
            json.dumps({"summary": "", "strengths": "", "weaknesses": "", "questions": "", "rating": 7}),
            encoding="utf-8",
        )
        (run_dir / "trace.jsonl").write_text(
            json.dumps({"type": "run_footer", "duration_ms": 1}) + "\n", encoding="utf-8"
        )
        return run_dir

    runner.calls = calls  # type: ignore[attr-defined]
    return runner


def test_write_configs_matches_batch_schema(tmp_path: Path):
    spec = resolve_spec(RAW_SPEC)
    paths = BatchPaths(root=tmp_path, name="pilot")
    write_configs(spec, paths)
    data = json.loads(paths.configs_path.read_text(encoding="utf-8"))
    assert data["All-A"]["homogeneous"] is True
    assert data["All-A"]["models"]["leader"] == "slug-a"


def test_execute_runs_all_and_registry_loads(tmp_path: Path, dataset: Path):
    spec = resolve_spec(RAW_SPEC)
    papers = _load_papers(dataset)
    paths = BatchPaths(root=tmp_path, name="pilot")
    items, paper_ids = plan_runs(spec, papers)
    assert len(items) == 6  # 3 configs x 2 papers

    runner = fake_runner_factory()
    summary = execute(spec, papers, paths, items, runner=runner, log=lambda _: None)
    assert summary.done == 6 and summary.failed == 0
    assert len(runner.calls) == 6  # type: ignore[attr-defined]

    batch = Batch.load("pilot", root=tmp_path, dataset_path=dataset)
    assert len(batch.runs_by_config_paper()) == 6


def test_execute_is_resumable(tmp_path: Path, dataset: Path):
    spec = resolve_spec(RAW_SPEC)
    papers = _load_papers(dataset)
    paths = BatchPaths(root=tmp_path, name="pilot")
    items, _ = plan_runs(spec, papers)

    first = fake_runner_factory()
    execute(spec, papers, paths, items, runner=first, log=lambda _: None)

    second = fake_runner_factory()
    summary = execute(spec, papers, paths, items, runner=second, log=lambda _: None)
    assert summary.skipped == 6 and summary.done == 0
    assert len(second.calls) == 0  # type: ignore[attr-defined]
    # runs.jsonl stayed append-only (no duplicate lines).
    lines = paths.runs_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 6


def test_execute_repairs_orphan_artifacts(tmp_path: Path, dataset: Path):
    spec = resolve_spec(RAW_SPEC)
    papers = _load_papers(dataset)
    paths = BatchPaths(root=tmp_path, name="pilot")
    items, _ = plan_runs(spec, papers)

    # Produce artifacts on disk but no registry (simulate crash before append).
    runner = fake_runner_factory()
    for item in items:
        runner(spec.configs[item.config_id].models, "x", item.paper_id, paths.outputs_dir, item.run_name)
    assert not paths.runs_path.exists()

    summary = execute(spec, papers, paths, items, runner=fake_runner_factory(), log=lambda _: None)
    assert summary.repaired == 6 and summary.done == 0
    assert len(paths.runs_path.read_text().strip().splitlines()) == 6


def test_execute_records_failures(tmp_path: Path, dataset: Path):
    spec = resolve_spec(RAW_SPEC)
    papers = _load_papers(dataset)
    paths = BatchPaths(root=tmp_path, name="pilot")
    items, _ = plan_runs(spec, papers)

    runner = fake_runner_factory(fail_on={"All-A__p1"})
    summary = execute(spec, papers, paths, items, runner=runner, log=lambda _: None)
    assert summary.failed == 1 and summary.done == 5
    errors = paths.errors_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(errors) == 1
    assert json.loads(errors[0])["config_id"] == "All-A"
    # The failed combo never entered runs.jsonl.
    assert len(paths.runs_path.read_text().strip().splitlines()) == 5


def test_dry_run_report_has_no_side_effects(tmp_path: Path, dataset: Path):
    spec = resolve_spec(RAW_SPEC)
    papers = _load_papers(dataset)
    paths = BatchPaths(root=tmp_path, name="pilot")
    items, paper_ids = plan_runs(spec, papers)

    report = dry_run_report(spec, paths, items, paper_ids, warnings=["w1"])
    assert "6" in report and "pending" in report and "w1" in report
    assert not paths.batch_dir.exists()  # nothing written


def test_limit_caps_runs(tmp_path: Path, dataset: Path):
    spec = resolve_spec(RAW_SPEC)
    papers = _load_papers(dataset)
    items, _ = plan_runs(spec, papers, limit=2)
    assert len(items) == 2
