from harness.registries import AgentExecutionContext, AgentExecutionResult, AgentStepTrace


def execute(input_text: str, context: AgentExecutionContext) -> AgentExecutionResult:
    cleaned_input = " ".join(input_text.split())
    output = f"{{module_name}} received: {cleaned_input}"
    return AgentExecutionResult(
        output=output,
        steps=[AgentStepTrace(name="service_node", output=output)],
        metadata={"module_id": context.module_id, "agent_id": context.agent_id},
    )


def run(input_text: str) -> str:
    cleaned_input = " ".join(input_text.split())
    return f"{{module_name}} received: {cleaned_input}"
