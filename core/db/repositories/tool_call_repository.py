from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.run import ToolCall
from core.db.models import ToolCallRecord


class ToolCallRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, tool_call: ToolCall) -> ToolCall:
        self.session.add(
            ToolCallRecord(
                id=tool_call.id,
                run_id=tool_call.run_id,
                step_id=tool_call.step_id,
                trace_id=tool_call.trace_id,
                span_id=tool_call.span_id,
                tool_id=tool_call.tool_id,
                tool_name=tool_call.tool_name,
                arguments=tool_call.arguments,
                result=tool_call.result,
                status=tool_call.status,
                started_at=tool_call.started_at,
                ended_at=tool_call.ended_at,
                duration_ms=tool_call.duration_ms,
                error_type=tool_call.error_type,
                error_message=tool_call.error_message,
                metadata_=tool_call.metadata,
                created_at=tool_call.created_at,
            )
        )
        self.session.flush()
        return tool_call

    def get(self, tool_call_id: str) -> ToolCall | None:
        record = self.session.get(ToolCallRecord, tool_call_id)
        if record is None:
            return None
        return self._to_model(record)

    def list_by_run(self, run_id: str) -> list[ToolCall]:
        records = self.session.scalars(
            select(ToolCallRecord)
            .where(ToolCallRecord.run_id == run_id)
            .order_by(ToolCallRecord.created_at)
        ).all()
        return [self._to_model(record) for record in records]

    @staticmethod
    def _to_model(record: ToolCallRecord) -> ToolCall:
        return ToolCall(
            id=record.id,
            run_id=record.run_id,
            step_id=record.step_id,
            trace_id=record.trace_id,
            span_id=record.span_id,
            tool_id=record.tool_id,
            tool_name=record.tool_name,
            arguments=record.arguments or {},
            result=record.result or {},
            status=record.status,
            started_at=record.started_at,
            ended_at=record.ended_at,
            duration_ms=record.duration_ms,
            error_type=record.error_type,
            error_message=record.error_message,
            metadata=record.metadata_ or {},
            created_at=record.created_at,
        )
