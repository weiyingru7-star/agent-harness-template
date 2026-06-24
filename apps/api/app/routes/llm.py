from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.ai_runtime.client import LLMClient, LLMResponse
from app.ai_runtime.providers import MockLLMProvider, OpenAICompatibleProvider
from app.core.config import settings


router = APIRouter(prefix="/api/llm", tags=["llm"])


class LLMSmokeRequest(BaseModel):
    prompt: str
    provider: Literal["mock", "openai_compatible"] = "mock"
    structured: bool = False


@router.post("/smoke", response_model=LLMResponse)
def smoke(request: LLMSmokeRequest) -> LLMResponse:
    if request.provider == "mock":
        provider = MockLLMProvider()
    else:
        provider = OpenAICompatibleProvider(
            base_url=settings.openai_compatible_base_url,
            api_key=settings.openai_compatible_api_key,
            model=settings.openai_compatible_model,
        )

    try:
        return LLMClient(provider).generate(
            prompt=request.prompt,
            structured=request.structured,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
