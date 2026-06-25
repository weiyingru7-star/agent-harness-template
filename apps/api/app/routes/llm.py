from fastapi import APIRouter, HTTPException, status
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
