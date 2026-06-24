from app.registries.skills import get_skill
from app.registries.tools import get_tool


def run_demo_agent(task_input: str) -> str:
    skill = get_skill("mock_summarize")
    tool = get_tool("mock_echo")

    skill_output = skill(task_input)
    tool_output = tool(skill_output)

    return f"demo_agent mock response | skill={skill_output} | tool={tool_output}"
