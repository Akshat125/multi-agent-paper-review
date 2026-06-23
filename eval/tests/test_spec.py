"""Tests for eval/utils/spec.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from utils.spec import (
    build_matrix,
    collect_warnings,
    derive_homogeneous,
    is_run_complete,
    load_spec,
    resolve_spec,
    run_name,
    select_papers,
)

PAPERS = {
    "p1": {"id": "p1", "stratum": "normal", "paper_text": "a"},
    "p2": {"id": "p2", "stratum": "controversial", "paper_text": "b"},
    "p3": {"id": "p3", "stratum": "normal", "paper_text": "c"},
}

RAW_SPEC = {
    "batch": "pilot",
    "pool": {"A": "slug-a", "B": "slug-b", "C": "slug-c"},
    "configs": {
        "All-A": {"leader": "A", "clarity": "A", "experiments": "A", "impact": "A"},
        "All-B": {"leader": "B", "clarity": "B", "experiments": "B", "impact": "B"},
        "All-C": {"leader": "C", "clarity": "C", "experiments": "C", "impact": "C"},
        "het": {"leader": "A", "clarity": "B", "experiments": "C", "impact": "A"},
    },
    "papers": "all",
    "replicates": 1,
}


def test_resolve_pool_keys_to_slugs():
    spec = resolve_spec(RAW_SPEC)
    assert spec.configs["het"].models == {
        "leader": "slug-a",
        "clarity": "slug-b",
        "experiments": "slug-c",
        "impact": "slug-a",
    }
    assert spec.configs["All-A"].homogeneous is True
    assert spec.configs["het"].homogeneous is False


def test_raw_slug_passes_through_when_not_a_pool_key():
    raw = dict(RAW_SPEC)
    raw["configs"] = {
        "x": {"leader": "openai/gpt-5", "clarity": "A", "experiments": "A", "impact": "A"}
    }
    spec = resolve_spec(raw)
    assert spec.configs["x"].models["leader"] == "openai/gpt-5"
    assert spec.configs["x"].models["clarity"] == "slug-a"


def test_derive_homogeneous():
    assert derive_homogeneous({"leader": "m", "clarity": "m", "experiments": "m", "impact": "m"})
    assert not derive_homogeneous({"leader": "m", "clarity": "n", "experiments": "m", "impact": "m"})


def test_missing_role_raises():
    raw = dict(RAW_SPEC)
    raw["configs"] = {"bad": {"leader": "A", "clarity": "A", "experiments": "A"}}
    with pytest.raises(ValueError, match="missing role 'impact'"):
        resolve_spec(raw)


def test_replicates_override():
    spec = resolve_spec(RAW_SPEC, replicates_override=3)
    assert spec.replicates == 3


def test_bad_replicates_raises():
    raw = dict(RAW_SPEC)
    raw["replicates"] = 0
    with pytest.raises(ValueError, match="replicates must be"):
        resolve_spec(raw)


def test_select_papers_all_is_sorted():
    spec = resolve_spec(RAW_SPEC)
    assert select_papers(spec, PAPERS) == ["p1", "p2", "p3"]


def test_select_papers_cli_ids_override_and_validate():
    spec = resolve_spec(RAW_SPEC)
    assert select_papers(spec, PAPERS, cli_ids=["p2"]) == ["p2"]
    with pytest.raises(ValueError, match="not in dataset"):
        select_papers(spec, PAPERS, cli_ids=["nope"])


def test_select_papers_stratum_and_n():
    spec = resolve_spec(RAW_SPEC)
    assert select_papers(spec, PAPERS, cli_stratum="normal") == ["p1", "p3"]
    assert select_papers(spec, PAPERS, cli_stratum="normal", cli_n=1) == ["p1"]


def test_select_papers_spec_stratum_selector():
    raw = dict(RAW_SPEC)
    raw["papers"] = {"stratum": "controversial"}
    spec = resolve_spec(raw)
    assert select_papers(spec, PAPERS) == ["p2"]


def test_build_matrix_counts_and_replicates():
    spec = resolve_spec(RAW_SPEC, replicates_override=2)
    items = build_matrix(spec, ["p1", "p2"])
    assert len(items) == 4 * 2 * 2
    names = {i.run_name for i in items}
    assert "All-A__p1" in names
    assert "All-A__p1__r1" in names


def test_run_name():
    assert run_name("All-A", "p1", 0) == "All-A__p1"
    assert run_name("All-A", "p1", 2) == "All-A__p1__r2"


def test_is_run_complete(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    assert not is_run_complete(run_dir)
    (run_dir / "final_review.md").write_text("x", encoding="utf-8")
    (run_dir / "review.json").write_text("{}", encoding="utf-8")
    (run_dir / "trace.jsonl").write_text(
        json.dumps({"type": "run_header"}) + "\n", encoding="utf-8"
    )
    assert not is_run_complete(run_dir)  # no run_footer yet
    (run_dir / "trace.jsonl").write_text(
        json.dumps({"type": "run_footer"}) + "\n", encoding="utf-8"
    )
    assert is_run_complete(run_dir)


def test_warning_when_missing_homogeneous_baseline():
    raw = dict(RAW_SPEC)
    raw["configs"] = {
        "All-A": {"leader": "A", "clarity": "A", "experiments": "A", "impact": "A"},
        "het": {"leader": "A", "clarity": "B", "experiments": "C", "impact": "A"},
    }
    spec = resolve_spec(raw)
    warnings = collect_warnings(spec)
    assert any("homogeneous" in w for w in warnings)


def test_no_homogeneous_warning_when_pool_covered():
    spec = resolve_spec(RAW_SPEC)
    assert collect_warnings(spec) == []


def test_price_warning_for_unpriced_model():
    spec = resolve_spec(RAW_SPEC)
    prices = {"slug-a": {"in": 1.0, "out": 2.0}}  # b and c unpriced
    warnings = collect_warnings(spec, prices=prices)
    assert any("price" in w.lower() or "cost" in w.lower() for w in warnings)


def test_load_spec_from_file(tmp_path: Path):
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(RAW_SPEC), encoding="utf-8")
    spec = load_spec(path)
    assert spec.name == "pilot"
    assert len(spec.configs) == 4
