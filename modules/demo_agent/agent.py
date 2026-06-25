from harness.state_machine.demo_agent_graph import run_demo_agent_graph
from harness.state_machine.types import DemoAgentState
from harness.registries.types import (
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStepTrace,
)


def execute(task_input: str, context: AgentExecutionContext) -> AgentExecutionResult:
    state = run_demo_agent_state_machine(task_input)
    return AgentExecutionResult(
        output=state.final_output or "",
        steps=[
            AgentStepTrace(
                name=node_trace.name,
                output=node_trace.output,
                status=node_trace.status,
                error_type=node_trace.error_type,
                error_message=node_trace.error_message,
                state=node_trace.state,
            )
            for node_trace in state.node_traces
        ],
        metadata={
            "module_id": context.module_id,
            "agent_id": context.agent_id,
            "workflow": "state_machine",
        },
    )


def run_demo_agent(task_input: str) -> str:
    state = run_demo_agent_state_machine(task_input)
    return state.final_output or ""


def run_demo_agent_state_machine(task_input: str) -> DemoAgentState:
    return run_demo_agent_graph(task_input)
