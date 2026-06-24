from sqlalchemy.orm import Session

from app.models.file import UploadedFile
from core.db.models import FileRecord


class FileRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, uploaded_file: UploadedFile, metadata: dict | None = None) -> UploadedFile:
        self.session.add(
            FileRecord(
                id=uploaded_file.id,
                filename=uploaded_file.filename,
                content_type=uploaded_file.content_type,
                size_bytes=uploaded_file.size_bytes,
                extension=uploaded_file.extension,
                storage_path=uploaded_file.storage_path,
                text=uploaded_file.text,
                metadata_=metadata or {},
                created_at=uploaded_file.created_at,
            )
        )
        self.session.flush()
        return uploaded_file

    def get(self, file_id: str) -> UploadedFile | None:
        record = self.session.get(FileRecord, file_id)
        if record is None:
            return None
        return UploadedFile(
            id=record.id,
            filename=record.filename,
            content_type=record.content_type,
            size_bytes=record.size_bytes,
            extension=record.extension,
            storage_path=record.storage_path,
            text=record.text,
            created_at=record.created_at,
        )
