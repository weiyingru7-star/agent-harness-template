from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Message
from core.db.models import MessageRecord


class MessageRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _new_id() -> str:
        return f"msg_{uuid4().hex[:12]}"

    @staticmethod
    def _from_record(rec: MessageRecord) -> Message:
        return Message(
            id=rec.id,
            conversation_id=rec.conversation_id,
            tenant_id=rec.tenant_id,
            user_id=rec.user_id,
            role=rec.role,
            content=rec.content,
            run_id=rec.run_id,
            metadata=rec.metadata_,
            created_at=rec.created_at,
        )

    def create(
        self,
        conversation_id: str,
        tenant_id: str,
        user_id: str,
        role: str,
        content: str = "",
        run_id: str | None = None,
        metadata: dict | None = None,
    ) -> Message:
        msg_id = self._new_id()
        record = MessageRecord(
            id=msg_id,
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            content=content,
            run_id=run_id,
            metadata_=metadata or {},
        )
        self.session.add(record)
        self.session.flush()
        return self._from_record(record)

    def list_by_conversation(self, conversation_id: str) -> list[Message]:
        stmt = (
            select(MessageRecord)
            .where(MessageRecord.conversation_id == conversation_id)
            .order_by(MessageRecord.created_at.asc(), MessageRecord.id.asc())
        )
        return [self._from_record(r) for r in self.session.execute(stmt).scalars().all()]

    def get_by_id(self, message_id: str) -> Message | None:
        """Get a single message by ID without tenant filtering."""
        record = self.session.get(MessageRecord, message_id)
        if record is None:
            return None
        return self._from_record(record)
