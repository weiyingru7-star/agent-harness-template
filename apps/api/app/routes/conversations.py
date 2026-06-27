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
from app.services.idempotency_guard import (
    IdempotencyContext,
    idempotency_guard,
)


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
    # Tenant consistency check (V1.3)
    conv = conversation_store.get_conversation(conversation_id, tenant_id=request.tenant_id)
    if conv is None or conv.user_id != request.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # Idempotency check (V1.7)
    ctx = IdempotencyContext(
        idempotency_key=request.idempotency_key,
        request_id=request.request_id,
        sequence_index=request.sequence_index,
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        conversation_id=conversation_id,
        action="create_message",
    )
    decision = idempotency_guard.check(ctx)

    if not decision.allowed:
        if decision.code == "DUPLICATE_IDEMPOTENCY_KEY" and decision.existing_resource_id:
            existing = conversation_store.get_message_by_id(
                message_id=decision.existing_resource_id,
                tenant_id=request.tenant_id,
                conversation_id=conversation_id,
            )
            if existing:
                return MessageResponse(**existing.model_dump())
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{decision.code}: {decision.reason}",
        )

    msg = conversation_store.add_message(
        conversation_id=conversation_id,
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        role=request.role,
        content=request.content,
        metadata=request.metadata,
    )
    idempotency_guard.record(ctx, resource_id=msg.id, resource_type="message")
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
    # Idempotency check (V1.7) — before any side effects
    ctx = IdempotencyContext(
        idempotency_key=request.idempotency_key,
        request_id=request.request_id,
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        conversation_id=conversation_id,
        action="create_conversation_run",
    )
    decision = idempotency_guard.check(ctx)

    if not decision.allowed:
        if decision.code == "DUPLICATE_IDEMPOTENCY_KEY" and decision.existing_metadata:
            meta = decision.existing_metadata
            return ConversationRunResponse(
                conversation_id=meta.get("conversation_id", conversation_id),
                user_message_id=meta.get("user_message_id", ""),
                assistant_message_id=meta.get("assistant_message_id"),
                run_id=meta.get("run_id", ""),
                run_status=meta.get("run_status", "unknown"),
                request_id=request.request_id,
                idempotency_key=request.idempotency_key,
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{decision.code}: {decision.reason}",
        )

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

    # Record with full metadata for duplicate recovery
    extra_meta = {
        "run_id": result.run_id,
        "user_message_id": result.user_message_id,
        "assistant_message_id": result.assistant_message_id,
        "conversation_id": conversation_id,
        "tenant_id": request.tenant_id,
        "user_id": request.user_id,
        "run_status": result.run_status,
    }
    idempotency_guard.record(
        ctx,
        resource_id=result.run_id,
        resource_type="conversation_run",
        extra_metadata=extra_meta,
    )

    result.request_id = request.request_id
    result.idempotency_key = request.idempotency_key
    return result
