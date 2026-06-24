from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.artifact import Artifact
from core.db.models import ArtifactRecord


class ArtifactRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        artifact_id: str,
        run_id: str,
        file_id: str,
        title: str,
        content: str,
        artifact_type: str = "text",
        metadata: dict | None = None,
    ) -> Artifact:
        record = ArtifactRecord(
            id=artifact_id,
            run_id=run_id,
            file_id=file_id,
            title=title,
            type=artifact_type,
            content=content,
            metadata_=metadata or {},
        )
        self.session.add(record)
        self.session.flush()
        return self._to_model(record)

    def list_by_run(self, run_id: str) -> list[Artifact]:
        records = self.session.scalars(
            select(ArtifactRecord)
            .where(ArtifactRecord.run_id == run_id)
            .order_by(ArtifactRecord.created_at)
        ).all()
        return [self._to_model(record) for record in records]

    def get(self, artifact_id: str) -> Artifact | None:
        record = self.session.get(ArtifactRecord, artifact_id)
        if record is None:
            return None
        return self._to_model(record)

    @staticmethod
    def _to_model(record: ArtifactRecord) -> Artifact:
        return Artifact(
            id=record.id,
            run_id=record.run_id,
            file_id=record.file_id or "",
            name=record.title,
            kind="text",
            text=record.content,
            created_at=record.created_at,
        )
