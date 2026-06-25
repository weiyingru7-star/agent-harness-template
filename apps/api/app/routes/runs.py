from fastapi import APIRouter, HTTPException, status

from app.models.run import Checkpoint, CreateRunRequest, Run, RunEvent, RunTrace
from app.services.run_store import run_store


router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.post("", response_model=Run, status_code=status.HTTP_201_CREATED)
def create_run(request: CreateRunRequest) -> Run:
    try:
        return run_store.create_run(request.input, module_id=request.module_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{run_id}/retry", response_model=Run, status_code=status.HTTP_201_CREATED)
def retry_run(run_id: str) -> Run:
    try:
        run = run_store.retry_run(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run


@router.get("/{run_id}/events", response_model=list[RunEvent])
def get_run_events(run_id: str) -> list[RunEvent]:
    events = run_store.get_events(run_id)
    if events is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return events


@router.get("/{run_id}/trace", response_model=RunTrace)
def get_run_trace(run_id: str) -> RunTrace:
    trace = run_store.get_trace(run_id)
    if trace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return trace


@router.get("/{run_id}/checkpoints", response_model=list[Checkpoint])
def get_run_checkpoints(run_id: str) -> list[Checkpoint]:
    checkpoints = run_store.get_checkpoints(run_id)
    if checkpoints is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return checkpoints


@router.get("/{run_id}", response_model=Run)
def get_run(run_id: str) -> Run:
    run = run_store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run
