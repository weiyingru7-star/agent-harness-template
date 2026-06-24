from uuid import uuid4

from app.models.artifact import Artifact
from app.services.file_store import file_store
from app.services.run_store import run_store


class ArtifactStore:
    def __init__(self) -> None:
        self._artifacts: dict[str, Artifact] = {}
        self._artifact_ids_by_run: dict[str, list[str]] = {}

    def create_artifact(self, run_id: str, file_id: str, name: str) -> Artifact:
        if run_store.get_run(run_id) is None:
            raise KeyError("Run not found")

        uploaded_file = file_store.get_file(file_id)
        if uploaded_file is None:
            raise KeyError("File not found")

        artifact = Artifact(
            id=self._new_id("artifact"),
            run_id=run_id,
            file_id=file_id,
            name=name,
            text=uploaded_file.text,
        )
        self._artifacts[artifact.id] = artifact
        self._artifact_ids_by_run.setdefault(run_id, []).append(artifact.id)
        return artifact

    def list_run_artifacts(self, run_id: str) -> list[Artifact] | None:
        if run_store.get_run(run_id) is None:
            return None
        return [
            self._artifacts[artifact_id]
            for artifact_id in self._artifact_ids_by_run.get(run_id, [])
        ]

    def get_artifact(self, artifact_id: str) -> Artifact | None:
        return self._artifacts.get(artifact_id)

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:12]}"


artifact_store = ArtifactStore()
