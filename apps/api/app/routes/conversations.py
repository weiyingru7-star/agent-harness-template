from fastapi import APIRouter, HTTPException, Query, status

from app.models.conversation import (
    ConversationResponse,
    ConversationRunResponse,
    CreateConversationRequest,
    CreateConversationRunRequest,
    CreateMessageRequest,
    MessageResponse,
)
from app.services.conversation_store import conversation_store


router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(request: CreateConversationRequest) -> ConversationResponse:
    conv = conversation_store.create_conversation(
        user_id=request.user_id,
        tenant_id=request.tenant_id,
        agent_template_id=request.agent_template_id,
        metadata=request.metadata,
    )
    return ConversationResponse(**conv.model_dump())


@router.get("", response_model=list[ConversationResponse])
def list_conversations(
    tenant_id: str | None = Query(None, min_length=1, description="Tenant ID (required)"),
    user_id: str | None = Query(None, min_length=1, description="Optional user filter"),
) -> list[ConversationResponse]:
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant_id is required")
    convs = conversation_store.list_conversations(user_id=user_id, tenant_id=tenant_id)
    return [ConversationResponse(**c.model_dump()) for c in convs]


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: str,
    tenant_id: str | None = Query(None, min_length=1, description="Tenant ID (required)"),
) -> ConversationResponse:
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant_id is required")
    conv = conversation_store.get_conversation(conversation_id, tenant_id=tenant_id)
    if conv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return ConversationResponse(**conv.model_dump())


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_message(conversation_id: str, request: CreateMessageRequest) -> MessageResponse:
    # Tenant consistency check
    conv = conversation_store.get_conversation(conversation_id, tenant_id=request.tenant_id)
    if conv is None or conv.user_id != request.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    msg = conversation_store.add_message(
        conversation_id=conversation_id,
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        role=request.role,
        content=request.content,
        metadata=request.metadata,
    )
    return MessageResponse(**msg.model_dump())


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
def list_messages(
    conversation_id: str,
    tenant_id: str | None = Query(None, min_length=1, description="Tenant ID (required)"),
) -> list[MessageResponse]:
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant_id is required")
    conv = conversation_store.get_conversation(conversation_id, tenant_id=tenant_id)
    if conv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    msgs = conversation_store.list_messages(conversation_id)
    return [MessageResponse(**m.model_dump()) for m in msgs]


@router.post(
    "/{conversation_id}/runs",
    response_model=ConversationRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation_run(
    conversation_id: str,
    request: CreateConversationRunRequest,
) -> ConversationRunResponse:
    result = conversation_store.create_conversation_run(
        conversation_id=conversation_id,
        user_id=request.user_id,
        tenant_id=request.tenant_id,
        input_text=request.input,
        module_id=request.module_id,
        metadata=request.metadata,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return result
