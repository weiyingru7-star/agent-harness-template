from uuid import uuid4

from app.models.file import UploadedFile
from core.db import session_scope
from core.db.repositories.knowledge_repository import KnowledgeRepository
from harness.rag.chunking import chunk_text
from harness.rag.models import Chunk, Citation, Document, IngestResponse, RetrieveResult


class KnowledgeStore:
    def ingest_file(self, uploaded_file: UploadedFile) -> IngestResponse:
        document = Document(
            id=self._new_id("doc"),
            file_id=uploaded_file.id,
            filename=uploaded_file.filename,
        )
        chunks = [
            Chunk(
                id=self._new_id("chunk"),
                document_id=document.id,
                file_id=uploaded_file.id,
                text=text,
                index=index,
            )
            for index, text in enumerate(chunk_text(uploaded_file.text))
        ]

        with session_scope() as session:
            repository = KnowledgeRepository(session)
            repository.create_document(
                document=document,
                collection="default",
                title=uploaded_file.filename,
                source="file",
                metadata={},
            )
            repository.create_chunks(chunks)
        return IngestResponse(document=document, chunks=chunks)

    def list_documents(self) -> list[Document]:
        with session_scope() as session:
            return KnowledgeRepository(session).list_documents()

    def retrieve(self, query: str, limit: int = 3) -> list[RetrieveResult]:
        terms = [term for term in query.lower().split() if term]
        scored: list[tuple[int, Chunk]] = []

        with session_scope() as session:
            repository = KnowledgeRepository(session)
            chunks = repository.list_chunks()
            documents = {document.id: document for document in repository.list_documents()}

        for chunk in chunks:
            haystack = chunk.text.lower()
            score = sum(haystack.count(term) for term in terms)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            RetrieveResult(
                chunk=chunk,
                score=score,
                citation=self._citation_for(chunk, documents),
            )
            for score, chunk in scored[:limit]
        ]

    def _citation_for(self, chunk: Chunk, documents: dict[str, Document]) -> Citation:
        document = documents[chunk.document_id]
        return Citation(
            document_id=document.id,
            chunk_id=chunk.id,
            file_id=document.file_id,
            filename=document.filename,
            chunk_index=chunk.index,
        )

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:12]}"


knowledge_store = KnowledgeStore()
