from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.ai_runtime.client import LLMClient, LLMResponse
from app.ai_runtime.providers import ProviderConfigurationError, ProviderRequestError
from app.ai_runtime.router import ProviderRouter
from app.ai_runtime.structured_output import StructuredOutputError, parse_structured_output_or_raise
from app.core.config import settings
from app.provider_runtime.contracts import ProviderConfig
from app.provider_runtime.router import call_provider_with_fallback, call_provider_with_timeout_retry


router = APIRouter(prefix="/api/llm", tags=["llm"])


class LLMSmokeRequest(BaseModel):
    prompt: str
    provider: str | None = None
    structured: bool = False
    fallback: str = "mock"
    timeout_ms: int | None = None
    max_attempts: int = 1


class LLMStreamRequest(BaseModel):
    prompt: str
    provider: str = "mock"
    model: str = "mock"
    metadata: dict = {}


_FALLBACK_ERRORS = (
    ProviderConfigurationError,
    ProviderRequestError,
    ValueError,
)


@router.post("/smoke", response_model=LLMResponse)
def smoke(request: LLMSmokeRequest) -> LLMResponse:
    primary = request.provider or "mock"
    try:
        result = call_provider_with_timeout_retry(
            prompt=request.prompt,
            provider_name=primary,
            max_attempts=request.max_attempts,
            timeout_ms=request.timeout_ms,
            structured=request.structured,
        )
        meta = dict(result.metadata)
        meta.setdefault("provider_runtime_version", "v0.5.1")
        meta.setdefault("contract", "ProviderResponse")
        meta["configured_provider"] = settings.ai_provider or "mock"
        meta["configured_model"] = settings.ai_model
        meta["config_source"] = "env"
        if "mock" not in meta:
            meta["mock"] = result.provider == "mock"
        parsed_output = None
        if request.structured and result.output:
            parsed_output = parse_structured_output_or_raise(result.output)
        return LLMResponse(
            provider=result.provider,
            output=result.output,
            structured_output=parsed_output,
            model=result.model,
            latency_ms=result.latency_ms,
            usage=result.usage,
            finish_reason=result.finish_reason,
            metadata=meta,
        )
    except _FALLBACK_ERRORS as exc:
        provider = ProviderRouter(settings).resolve(request.fallback)
        response = LLMClient(provider).generate(
            prompt=request.prompt, structured=request.structured,
        )
        response.metadata.update({
            "fallback_used": True,
            "fallback_from": primary,
            "fallback_to": request.fallback,
            "fallback_reason": f"{type(exc).__name__}: {exc}",
            "primary_error_type": type(exc).__name__,
        })
        return response
    except StructuredOutputError as exc:
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


@router.get("/config", response_model=ProviderConfig)
def get_config() -> ProviderConfig:
    return ProviderConfig(
        provider_name=settings.ai_provider or "mock",
        base_url=settings.ai_base_url or None,
        api_key_configured=bool(settings.ai_api_key),
        model=settings.ai_model,
        timeout_ms=int(settings.ai_timeout * 1000),
        max_attempts=settings.ai_max_attempts,
        fallback_provider=settings.ai_fallback_provider,
        streaming_enabled=settings.ai_streaming_enabled,
    )
