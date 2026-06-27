from sqlalchemy import select
from sqlalchemy.orm import Session

from core.db.models import ChunkRecord, DocumentRecord
from harness.rag.models import Chunk, Document


class KnowledgeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_document(
        self,
        document: Document,
        collection: str = "default",
        title: str | None = None,
        source: str = "file",
        metadata: dict | None = None,
    ) -> Document:
        self.session.add(
            DocumentRecord(
                id=document.id,
                file_id=document.file_id,
                filename=document.filename,
                collection=collection,
                title=title or document.filename,
                source=source,
                source_type=document.source_type,
                metadata_=metadata or {},
                created_at=document.created_at,
            )
        )
        self.session.flush()
        return document

    def create_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        for chunk in chunks:
            self.session.add(
                ChunkRecord(
                    id=chunk.id,
                    document_id=chunk.document_id,
                    file_id=chunk.file_id,
                    text=chunk.text,
                    chunk_index=chunk.index,
                    collection=chunk.collection,
                    char_count=chunk.char_count,
                    token_count=chunk.token_count,
                    metadata_=chunk.chunk_metadata or {},
                    created_at=chunk.created_at,
                )
            )
        self.session.flush()
        return chunks

    def list_documents(self) -> list[Document]:
        records = self.session.scalars(
            select(DocumentRecord).order_by(DocumentRecord.created_at)
        ).all()
        return [self._document_to_model(record) for record in records]

    def list_chunks(self) -> list[Chunk]:
        records = self.session.scalars(select(ChunkRecord).order_by(ChunkRecord.created_at)).all()
        return [self._chunk_to_model(record) for record in records]

    def get_document(self, document_id: str) -> Document | None:
        record = self.session.get(DocumentRecord, document_id)
        if record is None:
            return None
        return self._document_to_model(record)

    def get_chunks_by_collection(self, collection: str) -> list[Chunk]:
        records = self.session.scalars(
            select(ChunkRecord)
            .where(ChunkRecord.collection == collection)
            .order_by(ChunkRecord.created_at, ChunkRecord.chunk_index)
        ).all()
        return [self._chunk_to_model(record) for record in records]

    @staticmethod
    def _document_to_model(record: DocumentRecord) -> Document:
        return Document(
            id=record.id,
            file_id=record.file_id,
            filename=record.filename,
            source_type=record.source_type,
            collection=record.collection,
            title=record.title,
            source=record.source,
            content_type="text",
            metadata=record.metadata_ or {},
            created_at=record.created_at,
        )

    @staticmethod
    def _chunk_to_model(record: ChunkRecord) -> Chunk:
        return Chunk(
            id=record.id,
            document_id=record.document_id,
            file_id=record.file_id,
            text=record.text,
            index=record.chunk_index,
            collection=record.collection,
            char_count=record.char_count or 0,
            token_count=record.token_count or 0,
            chunk_metadata=record.metadata_ or {},
            created_at=record.created_at,
        )
