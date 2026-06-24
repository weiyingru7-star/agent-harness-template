from harness.state_machine.demo_agent_graph import run_demo_agent_graph
from harness.state_machine.types import DemoAgentState


def run_demo_agent(task_input: str) -> str:
    state = run_demo_agent_state_machine(task_input)
    return state.final_output or ""


def run_demo_agent_state_machine(task_input: str) -> DemoAgentState:
    return run_demo_agent_graph(task_input)
