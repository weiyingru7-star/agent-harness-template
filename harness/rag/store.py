from uuid import uuid4

from app.models.file import UploadedFile
from harness.rag.chunking import chunk_text
from harness.rag.models import Chunk, Citation, Document, IngestResponse, RetrieveResult


class KnowledgeStore:
    def __init__(self) -> None:
        self._documents: dict[str, Document] = {}
        self._chunks: list[Chunk] = []

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

        self._documents[document.id] = document
        self._chunks.extend(chunks)
        return IngestResponse(document=document, chunks=chunks)

    def list_documents(self) -> list[Document]:
        return list(self._documents.values())

    def retrieve(self, query: str, limit: int = 3) -> list[RetrieveResult]:
        terms = [term for term in query.lower().split() if term]
        scored: list[tuple[int, Chunk]] = []

        for chunk in self._chunks:
            haystack = chunk.text.lower()
            score = sum(haystack.count(term) for term in terms)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            RetrieveResult(
                chunk=chunk,
                score=score,
                citation=self._citation_for(chunk),
            )
            for score, chunk in scored[:limit]
        ]

    def _citation_for(self, chunk: Chunk) -> Citation:
        document = self._documents[chunk.document_id]
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
