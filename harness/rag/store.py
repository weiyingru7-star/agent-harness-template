from uuid import uuid4

from app.models.file import UploadedFile
from core.db import session_scope
from core.db.repositories.file_repository import FileRepository
from core.db.repositories.knowledge_repository import KnowledgeRepository
from harness.rag.chunking import chunk_text, chunk_text_with_strategy
from harness.rag.chunking_types import ChunkingConfig
from harness.rag.models import Chunk, Citation, Document, IngestResponse, RetrieveResult


def _compute_chunk_stats(text: str) -> tuple[int, int]:
    return len(text), len(text.split())


class KnowledgeStore:
    def ingest_file(
        self,
        uploaded_file: UploadedFile,
        collection: str = "default",
        chunking_config: ChunkingConfig | None = None,
    ) -> IngestResponse:
        document = Document(
            id=self._new_id("doc"),
            file_id=uploaded_file.id,
            filename=uploaded_file.filename,
            collection=collection,
            title=uploaded_file.filename,
            source="file",
            content_type=uploaded_file.content_type,
        )
        chunks = self._chunk_text(uploaded_file.text, document, collection, chunking_config)
        return self._ingest_document(document, chunks)

    def ingest_text(
        self,
        title: str,
        text: str,
        collection: str = "default",
        source: str = "direct",
        content_type: str = "text/plain",
        chunking_config: ChunkingConfig | None = None,
    ) -> IngestResponse:
        virtual_file = self._create_virtual_file(title, text, content_type)
        document = Document(
            id=self._new_id("doc"),
            file_id=virtual_file.id,
            filename=title,
            collection=collection,
            title=title,
            source=source,
            content_type=content_type,
        )
        chunks = self._chunk_text(text, document, collection, chunking_config)
        return self._ingest_document(document, chunks)

    def _chunk_text(
        self,
        text: str,
        document: Document,
        collection: str,
        config: ChunkingConfig | None,
    ) -> list[Chunk]:
        if config is not None:
            results = chunk_text_with_strategy(text, config)
            return [
                Chunk(
                    id=self._new_id("chunk"),
                    document_id=document.id,
                    file_id=document.file_id,
                    text=r.text,
                    index=r.chunk_index,
                    collection=collection,
                    char_count=r.char_count,
                    token_count=r.token_count,
                    chunk_metadata={
                        "start_char": r.start_char,
                        "end_char": r.end_char,
                        "split_strategy": r.split_strategy,
                        "overlap_with_previous": r.overlap_with_previous,
                        "chunk_size": config.chunk_size,
                        "chunk_overlap": config.chunk_overlap,
                    },
                )
                for r in results
            ]
        return [
            Chunk(
                id=self._new_id("chunk"),
                document_id=document.id,
                file_id=document.file_id,
                text=t,
                index=index,
                collection=collection,
                char_count=_compute_chunk_stats(t)[0],
                token_count=_compute_chunk_stats(t)[1],
            )
            for index, t in enumerate(chunk_text(text))
        ]

    def _ingest_document(self, document: Document, chunks: list[Chunk]) -> IngestResponse:
        with session_scope() as session:
            repository = KnowledgeRepository(session)
            repository.create_document(
                document=document,
                collection=document.collection or "default",
                title=document.title,
                source=document.source or "direct",
                metadata={},
            )
            repository.create_chunks(chunks)
        return IngestResponse(document=document, chunks=chunks)

    def _create_virtual_file(self, title: str, text: str, content_type: str) -> UploadedFile:
        file_id = self._new_id("file")
        uf = UploadedFile(
            id=file_id,
            filename=title,
            content_type=content_type,
            size_bytes=len(text.encode("utf-8")),
            extension=".txt",
            storage_path="direct://",
            text=text,
        )
        with session_scope() as session:
            FileRepository(session).create(uf)
        return uf

    def list_documents(self) -> list[Document]:
        with session_scope() as session:
            return KnowledgeRepository(session).list_documents()

    def get_document(self, document_id: str) -> Document | None:
        with session_scope() as session:
            return KnowledgeRepository(session).get_document(document_id)

    def get_chunks_by_collection(self, collection: str) -> list[Chunk]:
        with session_scope() as session:
            return KnowledgeRepository(session).get_chunks_by_collection(collection)

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
                citation=self._citation_for(chunk, documents, query=query, score=score),
            )
            for score, chunk in scored[:limit]
        ]

    def _citation_for(
        self, chunk: Chunk, documents: dict[str, Document],
        query: str = "", score: int = 0,
    ) -> Citation:
        document = documents[chunk.document_id]
        quote = chunk.text[:200] if query else None
        return Citation(
            document_id=document.id,
            chunk_id=chunk.id,
            file_id=document.file_id,
            filename=document.filename,
            chunk_index=chunk.index,
            title=document.title,
            source=document.source,
            quote=quote,
            score=score,
            collection=chunk.collection or document.collection,
        )

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:12]}"


knowledge_store = KnowledgeStore()
