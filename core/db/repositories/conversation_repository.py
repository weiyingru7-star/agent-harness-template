from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from core.db.models import ConversationRecord


class ConversationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _new_id() -> str:
        return f"conv_{uuid4().hex[:12]}"

    @staticmethod
    def _from_record(rec: ConversationRecord) -> Conversation:
        return Conversation(
            id=rec.id,
            user_id=rec.user_id,
            tenant_id=rec.tenant_id,
            agent_template_id=rec.agent_template_id,
            metadata=rec.metadata_,
            created_at=rec.created_at,
            updated_at=rec.updated_at,
        )

    def create(
        self,
        user_id: str,
        tenant_id: str,
        agent_template_id: str | None = None,
        metadata: dict | None = None,
    ) -> Conversation:
        conv_id = self._new_id()
        record = ConversationRecord(
            id=conv_id,
            user_id=user_id,
            tenant_id=tenant_id,
            agent_template_id=agent_template_id,
            metadata_=metadata or {},
        )
        self.session.add(record)
        self.session.flush()
        return self._from_record(record)

    def get(self, conversation_id: str) -> Conversation | None:
        record = self.session.get(ConversationRecord, conversation_id)
        if record is None:
            return None
        return self._from_record(record)

    def list_by_user(self, user_id: str) -> list[Conversation]:
        stmt = (
            select(ConversationRecord)
            .where(ConversationRecord.user_id == user_id)
            .order_by(ConversationRecord.created_at.desc())
        )
        return [self._from_record(r) for r in self.session.execute(stmt).scalars().all()]

    def list_by_tenant(self, tenant_id: str) -> list[Conversation]:
        stmt = (
            select(ConversationRecord)
            .where(ConversationRecord.tenant_id == tenant_id)
            .order_by(ConversationRecord.created_at.desc())
        )
        return [self._from_record(r) for r in self.session.execute(stmt).scalars().all()]
