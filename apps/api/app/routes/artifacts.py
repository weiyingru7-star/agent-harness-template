from fastapi import APIRouter, HTTPException, status

from app.models.artifact import Artifact, CreateArtifactRequest
from app.services.artifact_store import artifact_store


router = APIRouter(tags=["artifacts"])


@router.post(
    "/api/runs/{run_id}/artifacts",
    response_model=Artifact,
    status_code=status.HTTP_201_CREATED,
)
def create_run_artifact(run_id: str, request: CreateArtifactRequest) -> Artifact:
    try:
        return artifact_store.create_artifact(
            run_id=run_id,
            file_id=request.file_id,
            name=request.name,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc).strip("'"),
        ) from exc


@router.get("/api/runs/{run_id}/artifacts", response_model=list[Artifact])
def get_run_artifacts(run_id: str) -> list[Artifact]:
    artifacts = artifact_store.list_run_artifacts(run_id)
    if artifacts is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return artifacts


@router.get("/api/artifacts/{artifact_id}", response_model=Artifact)
def get_artifact(artifact_id: str) -> Artifact:
    artifact = artifact_store.get_artifact(artifact_id)
    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found",
        )
    return artifact
