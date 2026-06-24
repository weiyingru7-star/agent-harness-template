from harness.state_machine.demo_agent_graph import run_demo_agent_graph


def test_demo_agent_state_machine_runs_nodes_in_order() -> None:
    state = run_demo_agent_graph("hello   state")

    assert [trace.name for trace in state.node_traces] == [
        "input_node",
        "skill_node",
        "tool_node",
        "final_node",
    ]
    assert state.normalized_input == "hello state"
    assert state.skill_output == "Mock skill summary: hello state"
    assert state.tool_output == "Mock tool echo: Mock skill summary: hello state"
    assert state.final_output == (
        "demo_agent mock response | "
        "skill=Mock skill summary: hello state | "
        "tool=Mock tool echo: Mock skill summary: hello state"
    )
