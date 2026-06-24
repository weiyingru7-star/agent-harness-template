from fastapi import APIRouter, HTTPException, status

from app.models.run import CreateRunRequest, Run, RunEvent
from app.services.run_store import run_store


router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.post("", response_model=Run, status_code=status.HTTP_201_CREATED)
def create_run(request: CreateRunRequest) -> Run:
    return run_store.create_run(request.input)


@router.get("/{run_id}", response_model=Run)
def get_run(run_id: str) -> Run:
    run = run_store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run


@router.get("/{run_id}/events", response_model=list[RunEvent])
def get_run_events(run_id: str) -> list[RunEvent]:
    events = run_store.get_events(run_id)
    if events is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return events
