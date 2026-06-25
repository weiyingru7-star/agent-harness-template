from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.models.file import UploadedFile
from app.services.file_store import file_store
from harness.rag.models import Chunk, Document, IngestResponse, RetrieveResponse
from harness.rag.store import knowledge_store


router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class IngestRequest(BaseModel):
    file_id: str


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=3, ge=1, le=10)


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
def ingest(request: IngestRequest) -> IngestResponse:
    uploaded_file: UploadedFile | None = file_store.get_file(request.file_id)
    if uploaded_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return knowledge_store.ingest_file(uploaded_file)


@router.get("/documents", response_model=list[Document])
def list_documents() -> list[Document]:
    return knowledge_store.list_documents()


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(request: RetrieveRequest) -> RetrieveResponse:
    return RetrieveResponse(
        query=request.query,
        results=knowledge_store.retrieve(query=request.query, limit=request.limit),
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
