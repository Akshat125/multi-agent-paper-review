"""Multi-agent peer reviewer.

A centralized CrewAI system with one leader (which also acts as the hierarchical
manager) and three expert agents. The *only* variable between experimental
configurations is which model is assigned to each role; prompts, topology, and
aggregation logic are fixed.

Design notes
------------
- Each role gets its own ``crewai.LLM`` pointed at OpenRouter
  (``model="openrouter/<model_name>"``), so a single OpenRouter key reaches any
  vendor through the OpenAI-compatible interface.
- The experiment is a 4-tuple ``(leader, clarity, experiments, impact)`` -- only
  four models. The hierarchical manager therefore *is* the leader agent
  (``manager_agent=leader_agent``); the three experts are the worker ``agents``.
  No fifth manager model is invented.

Example
-------
Run a live review (requires ``OPENROUTER_API_KEY`` in the environment)::

    import json
    from pathlib import Path

    from src.agents.reviewer import MultiAgentReviewer
    from src.utils import TraceLogger

    paper = json.loads(Path("dataset/eval_sample_30.json").read_text())["papers"][0]
    reviewer = MultiAgentReviewer(
        leader_model="openai/gpt-4o",
        clarity_model="anthropic/claude-sonnet-4-5",
        experiments_model="meta-llama/llama-3.1-70b-instruct",
        impact_model="openai/gpt-4o",
    )
    review = reviewer.review(paper["paper_text"], trace_logger=TraceLogger())
    print(review)
"""

from __future__ import annotations

import hashlib
import os
import time
from typing import Optional

# We record our own trace.jsonl; disable CrewAI's interactive tracing UX.
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")

from crewai import LLM, Agent, Crew, Process, Task
from crewai.events.listeners.tracing.utils import set_suppress_tracing_messages

set_suppress_tracing_messages(True)

from ..utils import ReviewTraceListener, TraceLogger, parse_review
from .prompt_loader import PromptLoader

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

ROLE_LABELS = {
    "leader": "Review Leader",
    "clarity": "Clarity and Reproducibility Reviewer",
    "experiments": "Experiments and Methodology Reviewer",
    "impact": "Impact and Contribution Reviewer",
}

_LEADER_GOAL = (
    "Coordinate the three expert reviewers and synthesise their feedback into a "
    "single, high-quality final peer review of the paper."
)

_EXPECTED_OUTPUT = (
    "A complete peer review with exactly these Markdown headers: "
    "## Summary, ## Strengths, ## Weaknesses, ## Questions. "
    "Section bodies should read like natural human review prose (paragraphs or bullets as warranted). "
    "The final line must be RATING: <integer 1-10> using the rubric "
    "(1-3 reject, 4-5 borderline, 6-7 weak accept, 8-10 accept). "
    "Nothing may follow the RATING line."
)

def _role_variables() -> dict[str, str]:
    """Template variables for agent-role placeholders in prompt files."""
    return {
        "leader_role": ROLE_LABELS["leader"],
        "clarity_role": ROLE_LABELS["clarity"],
        "experiments_role": ROLE_LABELS["experiments"],
        "impact_role": ROLE_LABELS["impact"],
    }


class MultiAgentReviewer:
    """Leader + three-expert hierarchical reviewer over a single paper."""

    def __init__(
        self,
        leader_model: str,
        clarity_model: str,
        experiments_model: str,
        impact_model: str,
        api_key: Optional[str] = None,
        prompt_loader: Optional[PromptLoader] = None,
    ) -> None:
        self.models = {
            "leader": leader_model,
            "clarity": clarity_model,
            "experiments": experiments_model,
            "impact": impact_model,
        }
        for role, model in self.models.items():
            if not model or not isinstance(model, str):
                raise ValueError(f"{role}_model must be a non-empty string")

        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.prompts = prompt_loader or PromptLoader()
        self._role_vars = _role_variables()

        self.llms = {role: self._make_llm(model) for role, model in self.models.items()}

        self.leader_agent = Agent(
            role=ROLE_LABELS["leader"],
            goal=_LEADER_GOAL,
            backstory=self._render_prompt(self.prompts.system("leader")),
            llm=self.llms["leader"],
            allow_delegation=True,
            verbose=False,
        )
        self.expert_agents = {
            role: Agent(
                role=ROLE_LABELS[role],
                goal=self._render_prompt(self.prompts.task(role)),
                backstory=self._render_prompt(self.prompts.system(role)),
                llm=self.llms[role],
                allow_delegation=False,
                verbose=False,
            )
            for role in ("clarity", "experiments", "impact")
        }

    def _render_prompt(self, template: str, **extra: str) -> str:
        """Substitute role and other placeholders in a prompt template."""
        return PromptLoader.render(template, {**self._role_vars, **extra})

    def _make_llm(self, model_name: str) -> LLM:
        model = (
            model_name
            if model_name.startswith("openrouter/")
            else f"openrouter/{model_name}"
        )
        kwargs: dict[str, object] = {
            "model": model,
            "base_url": OPENROUTER_BASE_URL,
            "api_key": self.api_key,
            "temperature": 0.0,
        }
        # Pool model A (Qwen) only — disable thinking mode per experiment-setup.md.
        if "qwen" in model_name.lower():
            kwargs["additional_params"] = {"enable_thinking": False}
        return LLM(**kwargs)

    def review(
        self,
        paper_text: str,
        trace_logger: Optional[TraceLogger] = None,
        paper_id: Optional[str] = None,
    ) -> str:
        """Run a full review of ``paper_text`` and return the final review text."""
        if not paper_text or not isinstance(paper_text, str):
            raise ValueError("paper_text must be a non-empty string")

        description = self._render_prompt(
            self.prompts.task("leader"),
            paper_text=paper_text,
        )

        review_task = Task(
            description=description,
            expected_output=_EXPECTED_OUTPUT,
        )

        crew = Crew(
            agents=list(self.expert_agents.values()),
            tasks=[review_task],
            process=Process.hierarchical,
            manager_agent=self.leader_agent,
            verbose=False,
            tracing=False,
        )

        if trace_logger is None:
            result = crew.kickoff()
            return getattr(result, "raw", None) or str(result)

        return self._review_with_trace(crew, paper_text, paper_id, trace_logger)

    def _review_with_trace(
        self,
        crew: Crew,
        paper_text: str,
        paper_id: Optional[str],
        trace_logger: TraceLogger,
    ) -> str:
        trace_logger.log(
            "run_header",
            paper_id=paper_id,
            paper_chars=len(paper_text),
            paper_hash=hashlib.sha256(paper_text.encode()).hexdigest()[:16],
            models=dict(self.models),
            roles=dict(ROLE_LABELS),
        )

        started = time.monotonic()
        with ReviewTraceListener(
            trace_logger, leader_role=ROLE_LABELS["leader"]
        ) as listener:
            result = crew.kickoff()
            listener.flush()
        duration_ms = round((time.monotonic() - started) * 1000, 1)

        text = getattr(result, "raw", None) or str(result)
        trace_logger.save_review(text)
        parsed = parse_review(text)
        trace_logger.save_review_json(parsed)
        trace_logger.log(
            "review_parsed",
            rating=parsed["rating"],
            summary_chars=len(parsed["summary"]),
            strengths_chars=len(parsed["strengths"]),
            weaknesses_chars=len(parsed["weaknesses"]),
            questions_chars=len(parsed["questions"]),
        )
        trace_logger.log("run_footer", duration_ms=duration_ms, **listener.counts)
        return text
