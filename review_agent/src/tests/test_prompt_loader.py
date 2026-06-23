"""Unit tests for PromptLoader."""

from __future__ import annotations

import pytest

from src.agents.prompt_loader import ROLES, PromptLoader

_TOOL_PLACEHOLDERS = (
    "{paper_read_tool}",
    "{paper_search_tool}",
    "{num_agents}",
    "{review_leader}",
)


@pytest.fixture()
def loader() -> PromptLoader:
    return PromptLoader()


def test_all_roles_return_nonempty_system_and_task(loader):
    for role in ROLES:
        prompt = loader.get(role)
        assert prompt["system"].strip(), f"empty system prompt for {role}"
        assert prompt["task"].strip(), f"empty task prompt for {role}"


def test_no_tool_placeholders_remain(loader):
    for role in ROLES:
        prompt = loader.get(role)
        combined = prompt["system"] + prompt["task"]
        for placeholder in _TOOL_PLACEHOLDERS:
            assert placeholder not in combined, f"{placeholder} left in {role}"


def test_leader_prompt_has_role_placeholders(loader):
    combined = loader.system("leader") + loader.task("leader")
    for key in ("leader_role", "clarity_role", "experiments_role", "impact_role"):
        assert f"{{{key}}}" in combined, f"missing {{{key}}} in leader prompt"


def test_render_substitutes_placeholders(loader):
    rendered = PromptLoader.render(
        "Hello {clarity_role} and {paper_text}",
        {"clarity_role": "Clarity Reviewer", "paper_text": "PAPER BODY"},
    )
    assert rendered == "Hello Clarity Reviewer and PAPER BODY"


def test_only_leader_task_has_paper_placeholder(loader):
    assert "{paper_text}" in loader.task("leader")
    for role in ("clarity", "experiments", "impact"):
        assert "{paper_text}" not in loader.task(role)
        assert "{paper_text}" not in loader.system(role)


def test_unknown_role_raises(loader):
    with pytest.raises(ValueError):
        loader.get("not-a-role")
