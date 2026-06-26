from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.ai_runtime.client import LLMClient, LLMResponse
from app.ai_runtime.providers import ProviderConfigurationError, ProviderRequestError
from app.ai_runtime.router import ProviderRouter
from app.ai_runtime.structured_output import StructuredOutputError
from app.core.config import settings


router = APIRouter(prefix="/api/llm", tags=["llm"])


class LLMSmokeRequest(BaseModel):
    prompt: str
    provider: str | None = None
    structured: bool = False


class LLMStreamRequest(BaseModel):
    prompt: str
    provider: str = "mock"
    model: str = "mock"
    metadata: dict = {}


@router.post("/smoke", response_model=LLMResponse)
def smoke(request: LLMSmokeRequest) -> LLMResponse:
    try:
        provider = ProviderRouter(settings).resolve(request.provider)
        return LLMClient(provider).generate(
            prompt=request.prompt,
            structured=request.structured,
        )
    except (
        ProviderConfigurationError,
        ProviderRequestError,
        StructuredOutputError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/stream")
def stream(request: LLMStreamRequest) -> StreamingResponse:
    try:
        provider = ProviderRouter(settings).resolve(request.provider)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    client = LLMClient(provider)

    def event_stream():
        for event in client.generate_stream(request.prompt):
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
