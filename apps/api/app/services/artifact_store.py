from uuid import uuid4

from app.models.artifact import Artifact
from app.services.file_store import file_store
from core.db import session_scope
from core.db.repositories.artifact_repository import ArtifactRepository
from core.db.repositories.run_repository import RunRepository


class ArtifactStore:
    def create_artifact(self, run_id: str, file_id: str, name: str) -> Artifact:
        with session_scope() as session:
            if not RunRepository(session).exists(run_id):
                raise KeyError("Run not found")

        uploaded_file = file_store.get_file(file_id)
        if uploaded_file is None:
            raise KeyError("File not found")

        with session_scope() as session:
            return ArtifactRepository(session).create(
                artifact_id=self._new_id("artifact"),
                run_id=run_id,
                file_id=file_id,
                title=name,
                content=uploaded_file.text,
                artifact_type="text",
                metadata={},
            )

    def list_run_artifacts(self, run_id: str) -> list[Artifact] | None:
        with session_scope() as session:
            if not RunRepository(session).exists(run_id):
                return None
            return ArtifactRepository(session).list_by_run(run_id)

    def get_artifact(self, artifact_id: str) -> Artifact | None:
        with session_scope() as session:
            return ArtifactRepository(session).get(artifact_id)

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:12]}"


artifact_store = ArtifactStore()
