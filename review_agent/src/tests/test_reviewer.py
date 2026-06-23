"""Unit tests for MultiAgentReviewer (CrewAI fully mocked, no network)."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest import mock

import pytest
from crewai import Process

from src.agents.reviewer import ROLE_LABELS, MultiAgentReviewer
from src.utils import TraceLogger

_MODELS = dict(
    leader_model="openai/gpt-4o",
    clarity_model="anthropic/claude-sonnet-4-5",
    experiments_model="meta-llama/llama-3.1-70b-instruct",
    impact_model="openai/gpt-4o",
)

_STRUCTURED_REVIEW = """\
## Summary
Brief summary.

## Strengths
- Strong idea.

## Weaknesses
- Missing baseline.

## Questions
- Why no ablation?

RATING: 6
"""


def _patch_crewai():
    return (
        mock.patch("src.agents.reviewer.LLM"),
        mock.patch("src.agents.reviewer.Agent"),
        mock.patch("src.agents.reviewer.Task"),
        mock.patch("src.agents.reviewer.Crew"),
    )


def test_builds_four_llms_with_openrouter_prefix():
    p_llm, p_agent, p_task, p_crew = _patch_crewai()
    with p_llm as mock_llm, p_agent, p_task, p_crew:
        MultiAgentReviewer(**_MODELS, api_key="k")
        assert mock_llm.call_count == 4
        models = {c.kwargs["model"] for c in mock_llm.call_args_list}
        assert models == {
            "openrouter/openai/gpt-4o",
            "openrouter/anthropic/claude-sonnet-4-5",
            "openrouter/meta-llama/llama-3.1-70b-instruct",
        }
        # base_url and temperature propagated to every LLM
        for c in mock_llm.call_args_list:
            assert c.kwargs["base_url"].endswith("openrouter.ai/api/v1")
            assert c.kwargs["temperature"] == 0.0
            assert "additional_params" not in c.kwargs


def test_qwen_models_disable_thinking_mode():
    p_llm, p_agent, p_task, p_crew = _patch_crewai()
    with p_llm as mock_llm, p_agent, p_task, p_crew:
        MultiAgentReviewer(
            leader_model="qwen/qwen3-32b",
            clarity_model="qwen/qwen3-32b",
            experiments_model="mistralai/mistral-small-3.2-24b-instruct",
            impact_model="qwen/qwen3-32b",
            api_key="k",
        )
        for c in mock_llm.call_args_list:
            if "qwen" in c.kwargs["model"].lower():
                assert c.kwargs["additional_params"] == {"enable_thinking": False}
            else:
                assert "additional_params" not in c.kwargs


def test_review_runs_hierarchical_crew_and_returns_text():
    p_llm, p_agent, p_task, p_crew = _patch_crewai()
    with p_llm, p_agent as mock_agent, p_task as mock_task, p_crew as mock_crew:
        agents_seq = [SimpleNamespace(tag=f"agent{i}") for i in range(4)]
        mock_agent.side_effect = agents_seq

        reviewer = MultiAgentReviewer(**_MODELS, api_key="k")
        mock_crew.return_value.kickoff.return_value = SimpleNamespace(raw="FINAL REVIEW")

        out = reviewer.review("dummy paper text")

        assert out == "FINAL REVIEW"
        mock_crew.return_value.kickoff.assert_called_once()

        # Paper text and registered role labels are injected into the leader task.
        description = mock_task.call_args.kwargs["description"]
        assert "dummy paper text" in description
        assert ROLE_LABELS["clarity"] in description
        assert "{clarity_role}" not in description

        # Crew is hierarchical, leader is the manager, three experts are workers.
        crew_kwargs = mock_crew.call_args.kwargs
        assert crew_kwargs["process"] is Process.hierarchical
        assert crew_kwargs["manager_agent"] is agents_seq[0]
        assert crew_kwargs["agents"] == agents_seq[1:4]


def test_review_falls_back_to_str_when_no_raw():
    p_llm, p_agent, p_task, p_crew = _patch_crewai()
    with p_llm, p_agent, p_task, p_crew as mock_crew:
        reviewer = MultiAgentReviewer(**_MODELS, api_key="k")

        class _NoRaw:
            def __str__(self) -> str:
                return "stringified review"

        mock_crew.return_value.kickoff.return_value = _NoRaw()
        assert reviewer.review("paper") == "stringified review"


def test_leader_backstory_uses_registered_role_labels():
    p_llm, p_agent, p_task, p_crew = _patch_crewai()
    with p_llm, p_agent as mock_agent, p_task, p_crew:
        MultiAgentReviewer(**_MODELS, api_key="k")
        leader_call = mock_agent.call_args_list[0]
        backstory = leader_call.kwargs["backstory"]
        assert ROLE_LABELS["clarity"] in backstory
        assert "{clarity_role}" not in backstory


def test_empty_model_raises():
    p_llm, p_agent, p_task, p_crew = _patch_crewai()
    with p_llm, p_agent, p_task, p_crew:
        with pytest.raises(ValueError):
            MultiAgentReviewer(
                leader_model="",
                clarity_model="a",
                experiments_model="b",
                impact_model="c",
                api_key="k",
            )


def test_empty_paper_text_raises():
    p_llm, p_agent, p_task, p_crew = _patch_crewai()
    with p_llm, p_agent, p_task, p_crew:
        reviewer = MultiAgentReviewer(**_MODELS, api_key="k")
        with pytest.raises(ValueError):
            reviewer.review("")


def test_review_with_trace_writes_review_json(tmp_path):
    p_llm, p_agent, p_task, p_crew = _patch_crewai()
    with p_llm, p_agent, p_task, p_crew as mock_crew:
        reviewer = MultiAgentReviewer(**_MODELS, api_key="k")
        mock_crew.return_value.kickoff.return_value = SimpleNamespace(
            raw=_STRUCTURED_REVIEW
        )
        trace = TraceLogger(output_dir=tmp_path, run_name="traced")

        out = reviewer.review("paper text", trace_logger=trace, paper_id="p1")

        assert out == _STRUCTURED_REVIEW
        assert trace.review_path.read_text() == _STRUCTURED_REVIEW
        parsed = json.loads(trace.review_json_path.read_text())
        assert parsed["rating"] == 6
        assert "Brief summary" in parsed["summary"]
        assert "Missing baseline" in parsed["weaknesses"]

        records = [
            json.loads(line)
            for line in trace.trace_path.read_text().splitlines()
            if line.strip()
        ]
        types = [r["type"] for r in records]
        assert "review_parsed" in types
        parsed_rec = next(r for r in records if r["type"] == "review_parsed")
        assert parsed_rec["rating"] == 6
        assert parsed_rec["summary_chars"] == len(parsed["summary"])
