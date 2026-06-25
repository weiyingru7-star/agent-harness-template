from fastapi import APIRouter
from pydantic import BaseModel, Field

from harness.rag.embeddings import EmbeddingRegistry, EmbeddingRequest


router = APIRouter(prefix="/api/knowledge/embeddings", tags=["embeddings"])


class SmokeRequest(BaseModel):
    input: str = "hello"
    provider: str = "mock-embedding"


class SmokeResponse(BaseModel):
    dimensions: int
    model: str
    count: int
    usage: dict = Field(default_factory=dict)


@router.post("/smoke", response_model=SmokeResponse)
def smoke(request: SmokeRequest) -> SmokeResponse:
    provider = EmbeddingRegistry.get(request.provider)
    result = provider.embed(EmbeddingRequest(input=request.input))
    return SmokeResponse(
        dimensions=result.dimensions,
        model=result.model,
        count=len(result.embeddings),
        usage=result.usage,
    )
