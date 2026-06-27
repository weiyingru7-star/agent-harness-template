from fastapi import APIRouter, HTTPException, status

from app.models.job import CreateJobRequest, Job
from app.services.job_queue import job_queue


router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", response_model=Job, status_code=status.HTTP_201_CREATED)
def create_job(request: CreateJobRequest) -> Job:
    job = job_queue.enqueue(
        job_type=request.job_type,
        payload=request.payload,
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        request_id=request.request_id,
        idempotency_key=request.idempotency_key,
        max_attempts=request.max_attempts,
    )
    return job


@router.get("", response_model=list[Job])
def list_jobs(
    tenant_id: str | None = None,
    user_id: str | None = None,
    status: str | None = None,
) -> list[Job]:
    return job_queue.list_jobs(tenant_id=tenant_id, user_id=user_id, status=status)


@router.get("/{job_id}", response_model=Job)
def get_job(job_id: str) -> Job:
    job = job_queue.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.post("/{job_id}/cancel", response_model=Job)
def cancel_job(job_id: str) -> Job:
    job = job_queue.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.status in ("succeeded", "failed", "canceled"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel job in '{job.status}' state",
        )
    if job.status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot cancel a running job",
        )
    result = job_queue.cancel(job_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot cancel job")
    return result
