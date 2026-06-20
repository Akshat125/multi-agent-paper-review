"""Prompt loading.

Per-agent prompts live as markdown files in ``src/agents/prompts/<role>.md``.
Each file contains a system prompt and a task prompt separated by HTML-comment
markers::

    <!-- SYSTEM -->
    ...system prompt...
    <!-- TASK -->
    ...task prompt...

System prompts are adapted from the MAMORX paper appendix (tool placeholders
removed since this implementation uses no external tools). Task prompts are
authored for this project.
"""

from __future__ import annotations

from pathlib import Path

ROLES = ("leader", "clarity", "experiments", "impact")

_SYSTEM_MARKER = "<!-- SYSTEM -->"
_TASK_MARKER = "<!-- TASK -->"


class PromptLoader:
    """Load and expose system + task prompts for each agent role."""

    def __init__(self, prompts_dir: str | Path | None = None) -> None:
        self.prompts_dir = (
            Path(prompts_dir)
            if prompts_dir is not None
            else Path(__file__).parent / "prompts"
        )
        self._cache: dict[str, dict[str, str]] = {}

    def get(self, role: str) -> dict[str, str]:
        """Return ``{"system": ..., "task": ...}`` for ``role``."""
        if role not in ROLES:
            raise ValueError(f"Unknown role '{role}'. Valid roles: {ROLES}")
        if role not in self._cache:
            self._cache[role] = self._load(role)
        return self._cache[role]

    def system(self, role: str) -> str:
        return self.get(role)["system"]

    def task(self, role: str) -> str:
        return self.get(role)["task"]

    @staticmethod
    def render(template: str, variables: dict[str, str]) -> str:
        """Substitute ``{key}`` placeholders in ``template``."""
        text = template
        for key, value in variables.items():
            text = text.replace(f"{{{key}}}", value)
        return text

    def all(self) -> dict[str, dict[str, str]]:
        return {role: self.get(role) for role in ROLES}

    def _load(self, role: str) -> dict[str, str]:
        path = self.prompts_dir / f"{role}.md"
        if not path.is_file():
            raise FileNotFoundError(f"Prompt file not found: {path}")
        raw = path.read_text(encoding="utf-8")

        if _SYSTEM_MARKER not in raw or _TASK_MARKER not in raw:
            raise ValueError(
                f"Prompt file {path} must contain both '{_SYSTEM_MARKER}' and "
                f"'{_TASK_MARKER}' markers."
            )

        after_system = raw.split(_SYSTEM_MARKER, 1)[1]
        system_part, task_part = after_system.split(_TASK_MARKER, 1)
        system_text = system_part.strip()
        task_text = task_part.strip()

        if not system_text:
            raise ValueError(f"Empty system prompt in {path}")
        if not task_text:
            raise ValueError(f"Empty task prompt in {path}")

        return {"system": system_text, "task": task_text}
