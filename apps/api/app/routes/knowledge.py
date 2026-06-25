from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.models.file import UploadedFile
from app.services.file_store import file_store
from harness.rag.chunking_types import ChunkingConfig
from harness.rag.models import Chunk, Document, IngestResponse, RetrieveResponse
from harness.rag.store import knowledge_store


router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class IngestRequest(BaseModel):
    file_id: str
    chunking_config: dict | None = None


class CreateDocumentRequest(BaseModel):
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    collection: str = "default"
    source: str | None = "direct"
    content_type: str = "text/plain"
    metadata: dict = Field(default_factory=dict)
    chunking_config: dict | None = None


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=3, ge=1, le=10)
    retrieval_mode: str = "keyword"
    collection: str | None = None


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
def ingest(request: IngestRequest) -> IngestResponse:
    uploaded_file: UploadedFile | None = file_store.get_file(request.file_id)
    if uploaded_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    config: ChunkingConfig | None = None
    if request.chunking_config is not None:
        config = ChunkingConfig(**request.chunking_config)
    return knowledge_store.ingest_file(uploaded_file, chunking_config=config)


@router.post("/documents", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
def create_document(request: CreateDocumentRequest) -> IngestResponse:
    config: ChunkingConfig | None = None
    if request.chunking_config is not None:
        config = ChunkingConfig(**request.chunking_config)
    return knowledge_store.ingest_text(
        title=request.title,
        text=request.text,
        collection=request.collection,
        source=request.source,
        content_type=request.content_type,
        chunking_config=config,
    )


@router.get("/documents", response_model=list[Document])
def list_documents() -> list[Document]:
    return knowledge_store.list_documents()


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(request: RetrieveRequest) -> RetrieveResponse:
    try:
        results = knowledge_store.retrieve(
            query=request.query,
            limit=request.limit,
            retrieval_mode=request.retrieval_mode,
            collection=request.collection,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    mode = request.retrieval_mode
    meta: dict[str, object] = {
        "retrieval_mode": mode,
    }
    if mode == "keyword":
        meta["score_type"] = "term_frequency"
        meta["retriever"] = "KnowledgeStore.keyword"
    elif mode == "vector":
        meta["score_type"] = "cosine"
        meta["retriever"] = "KnowledgeStore.vector"
        meta["embedding_provider"] = "mock-embedding"
        meta["vector_store"] = "InMemoryVectorStore"
    elif mode == "hybrid":
        meta["score_type"] = "cosine"
        meta["retriever"] = "KnowledgeStore.hybrid"
        meta["embedding_provider"] = "mock-embedding"
        meta["vector_store"] = "InMemoryVectorStore"

    return RetrieveResponse(
        query=request.query,
        results=results,
        metadata=meta,
    )


@router.get("/documents/{document_id}", response_model=Document)
def get_document(document_id: str) -> Document:
    document = knowledge_store.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.get("/collections/{collection}/chunks", response_model=list[Chunk])
def get_collection_chunks(collection: str) -> list[Chunk]:
    return knowledge_store.get_chunks_by_collection(collection)
