from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.models.file import UploadedFile
from core.storage.local import LocalStorage


ALLOWED_EXTENSIONS = {".txt", ".md"}


class FileStore:
    def __init__(self) -> None:
        self._files: dict[str, UploadedFile] = {}
        self._storage = LocalStorage(settings.local_storage_dir)

    def save_file(self, filename: str, content_type: str, content: bytes) -> UploadedFile:
        extension = Path(filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError("Only .txt and .md files are supported")

        file_id = self._new_id("file")
        storage_name = f"{file_id}{extension}"
        storage_path = self._storage.write_bytes(storage_name, content)
        text = storage_path.read_text(encoding="utf-8")

        uploaded_file = UploadedFile(
            id=file_id,
            filename=Path(filename).name,
            content_type=content_type or "text/plain",
            size_bytes=len(content),
            extension=extension,
            storage_path=str(storage_path),
            text=text,
        )
        self._files[file_id] = uploaded_file
        return uploaded_file

    def get_file(self, file_id: str) -> UploadedFile | None:
        return self._files.get(file_id)

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:12]}"


file_store = FileStore()
