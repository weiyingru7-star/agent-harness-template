from app.registries.skills import get_skill
from app.registries.tools import get_tool
from harness.state_machine.types import DemoAgentNodeTrace, DemoAgentState


def input_node(state: DemoAgentState) -> DemoAgentState:
    state.normalized_input = " ".join(state.input.split())
    _record_node(state, "input_node", state.normalized_input)
    return state


def skill_node(state: DemoAgentState) -> DemoAgentState:
    skill = get_skill("mock_summarize")
    state.skill_output = skill(state.normalized_input or state.input)
    _record_node(state, "skill_node", state.skill_output)
    return state


def tool_node(state: DemoAgentState) -> DemoAgentState:
    tool = get_tool("mock_echo")
    state.tool_output = tool(state.skill_output or "")
    _record_node(state, "tool_node", state.tool_output)
    return state


def final_node(state: DemoAgentState) -> DemoAgentState:
    state.final_output = (
        "demo_agent mock response | "
        f"skill={state.skill_output} | "
        f"tool={state.tool_output}"
    )
    _record_node(state, "final_node", state.final_output)
    return state


def run_demo_agent_graph(task_input: str) -> DemoAgentState:
    state = DemoAgentState(input=task_input)
    for node in (input_node, skill_node, tool_node, final_node):
        state = node(state)
    return state


def _record_node(state: DemoAgentState, name: str, output: str) -> None:
    snapshot = state.model_dump(exclude={"node_traces"})
    state.node_traces.append(DemoAgentNodeTrace(name=name, output=output, state=snapshot))
