from collections.abc import Callable

from pydantic import BaseModel


class SkillDefinition(BaseModel):
    id: str
    name: str
    description: str


def mock_summarize(task_input: str) -> str:
    cleaned_input = " ".join(task_input.split())
    return f"Mock skill summary: {cleaned_input}"


SKILLS: dict[str, tuple[SkillDefinition, Callable[[str], str]]] = {
    "mock_summarize": (
        SkillDefinition(
            id="mock_summarize",
            name="Mock Summarize",
            description="Returns a deterministic summary for demo_agent.",
        ),
        mock_summarize,
    )
}


def list_skills() -> list[SkillDefinition]:
    return [definition for definition, _handler in SKILLS.values()]


def get_skill(skill_id: str) -> Callable[[str], str]:
    return SKILLS[skill_id][1]
