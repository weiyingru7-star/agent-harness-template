"""Minimal import/init test for ToolExecutionPipeline (V0.7.6 refactor)."""

from app.tool_runtime import PipelineResult, ToolExecutionPipeline, tool_execution_pipeline


def test_pipeline_can_be_imported() -> None:
    assert ToolExecutionPipeline is not None


def test_pipeline_can_be_instantiated() -> None:
    pipeline = ToolExecutionPipeline()
    assert isinstance(pipeline, ToolExecutionPipeline)


def test_pipeline_singleton_exists() -> None:
    assert isinstance(tool_execution_pipeline, ToolExecutionPipeline)


def test_pipeline_result_smoke() -> None:
    result = PipelineResult(tool_call_id="tc_test", next_sequence=42)
    assert result.tool_call_id == "tc_test"
    assert result.next_sequence == 42
