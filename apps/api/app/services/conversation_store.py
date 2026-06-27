from __future__ import annotations

from core.db import session_scope
from core.db.repositories.conversation_repository import ConversationRepository
from core.db.repositories.message_repository import MessageRepository
from app.models.conversation import (
    Conversation,
    ConversationRunResponse,
    Message,
)
from app.services.run_store import run_store


class ConversationStore:
    """Business logic for conversation and message operations."""

    def create_conversation(
        self,
        user_id: str,
        tenant_id: str,
        agent_template_id: str | None = None,
        metadata: dict | None = None,
    ) -> Conversation:
        with session_scope() as session:
            repo = ConversationRepository(session)
            return repo.create(
                user_id=user_id,
                tenant_id=tenant_id,
                agent_template_id=agent_template_id,
                metadata=metadata,
            )

    def get_conversation(self, conversation_id: str, tenant_id: str | None = None) -> Conversation | None:
        with session_scope() as session:
            repo = ConversationRepository(session)
            if tenant_id:
                return repo.get_by_id_and_tenant(conversation_id, tenant_id)
            return repo.get(conversation_id)

    def list_conversations(
        self,
        user_id: str | None = None,
        tenant_id: str | None = None,
    ) -> list[Conversation]:
        with session_scope() as session:
            repo = ConversationRepository(session)
            if user_id and tenant_id:
                return repo.list_by_user_and_tenant(user_id, tenant_id)
            if tenant_id:
                return repo.list_by_tenant(tenant_id)
            if user_id:
                return repo.list_by_user(user_id)
            return []

    def add_message(
        self,
        conversation_id: str,
        tenant_id: str,
        user_id: str,
        role: str,
        content: str = "",
        run_id: str | None = None,
        metadata: dict | None = None,
    ) -> Message:
        with session_scope() as session:
            repo = MessageRepository(session)
            return repo.create(
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                user_id=user_id,
                role=role,
                content=content,
                run_id=run_id,
                metadata=metadata,
            )

    def list_messages(self, conversation_id: str) -> list[Message]:
        with session_scope() as session:
            return MessageRepository(session).list_by_conversation(conversation_id)

    def get_message_by_id(
        self,
        message_id: str,
        tenant_id: str,
        conversation_id: str | None = None,
    ) -> Message | None:
        """Get a message by ID with tenant/conversation validation."""
        with session_scope() as session:
            msg = MessageRepository(session).get_by_id(message_id)
            if msg is None:
                return None
            if msg.tenant_id != tenant_id:
                return None
            if conversation_id is not None and msg.conversation_id != conversation_id:
                return None
            return msg

    def create_conversation_run(
        self,
        conversation_id: str,
        user_id: str,
        tenant_id: str,
        input_text: str,
        module_id: str | None = None,
        metadata: dict | None = None,
    ) -> ConversationRunResponse | None:
        """Create user message + run + optional assistant message.

        Only writes assistant message when run completes with output.
        """
        # 1. Verify conversation exists and matches user/tenant
        conv = self.get_conversation(conversation_id)
        if conv is None:
            return None
        if conv.user_id != user_id or conv.tenant_id != tenant_id:
            return None

        # 2. Create user message
        user_msg = self.add_message(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            role="user",
            content=input_text,
            metadata=metadata,
        )

        # 3. Create run with user context binding
        run = run_store.create_run(
            task_input=input_text,
            module_id=module_id,
            user_id=user_id,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=user_msg.id,
        )

        assistant_msg_id: str | None = None

        # 4. Only write assistant message if run completed with output
        if run.status == "completed" and run.output:
            assistant = self.add_message(
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                user_id=user_id,
                role="assistant",
                content=run.output,
                run_id=run.id,
            )
            assistant_msg_id = assistant.id

        return ConversationRunResponse(
            conversation_id=conversation_id,
            user_message_id=user_msg.id,
            assistant_message_id=assistant_msg_id,
            run_id=run.id,
            run_status=run.status,
        )


conversation_store = ConversationStore()
