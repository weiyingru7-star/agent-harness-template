from fastapi import APIRouter, HTTPException, status

from app.models.run import Checkpoint
from app.services.run_store import run_store


router = APIRouter(prefix="/api/checkpoints", tags=["checkpoints"])


@router.get("/{checkpoint_id}", response_model=Checkpoint)
def get_checkpoint(checkpoint_id: str) -> Checkpoint:
    checkpoint = run_store.get_checkpoint(checkpoint_id)
    if checkpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checkpoint not found",
        )
    return checkpoint
