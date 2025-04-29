"""
Job management routes.

This module provides API endpoints for managing asynchronous jobs.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any, Union

from backend.app.utils.job_utils import JobManager, JobStatus

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobResponse(BaseModel):
    """Response model for job information."""
    id: str
    type: str
    status: str
    progress: int
    created_at: str
    updated_at: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CreateJobRequest(BaseModel):
    """Request model for creating a new job."""
    job_type: str
    parameters: Optional[Dict[str, Any]] = None


class EnOSApiJobRequest(BaseModel):
    """Request model for creating an EnOS API job."""
    job_type: str
    access_key: str
    secret_key: str
    url: str
    data: Dict[str, Any]
    timeout: Optional[int] = 30


@router.post("/", response_model=Dict[str, str])
async def create_job(request: CreateJobRequest):
    """Create a new job.
    
    Args:
        request: Job creation request containing job type and parameters.
        
    Returns:
        Dictionary containing the created job ID.
    """
    try:
        parameters = request.parameters or {}
        job_id = JobManager.create_job(job_type=request.job_type, **parameters)
        return {"job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.post("/enos", response_model=Dict[str, str])
async def create_enos_api_job(request: EnOSApiJobRequest):
    """Create a new EnOS API job.
    
    Args:
        request: EnOS API job creation request with API credentials and parameters.
        
    Returns:
        Dictionary containing the created job ID.
    """
    try:
        job_id = JobManager.create_enos_api_job(
            job_type=request.job_type,
            access_key=request.access_key,
            secret_key=request.secret_key,
            url=request.url,
            data=request.data,
            timeout=request.timeout
        )
        return {"job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create EnOS API job: {str(e)}")


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get job details by ID.
    
    Args:
        job_id: The unique identifier of the job.
        
    Returns:
        Job details including status, progress, and results if available.
    """
    try:
        job = JobManager.get_job(job_id)
        return job
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job: {str(e)}")


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    job_type: Optional[str] = None, 
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """List jobs with optional filtering.
    
    Args:
        job_type: Filter by job type.
        status: Filter by job status.
        limit: Maximum number of jobs to return.
        offset: Number of jobs to skip.
        
    Returns:
        List of jobs matching the filter criteria.
    """
    try:
        # Convert status string to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = JobStatus[status.upper()]
            except KeyError:
                valid_statuses = [s.name for s in JobStatus]
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid status. Valid values are: {', '.join(valid_statuses)}"
                )
                
        jobs = JobManager.list_jobs(
            job_type=job_type,
            status=status_enum,
            limit=limit,
            offset=offset
        )
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.delete("/{job_id}", response_model=Dict[str, str])
async def cancel_job(job_id: str):
    """Cancel a running job.
    
    Args:
        job_id: The unique identifier of the job to cancel.
        
    Returns:
        Confirmation message.
    """
    try:
        job = JobManager.get_job(job_id)
        
        # Can only cancel jobs that are pending or running
        if job["status"] not in ["PENDING", "RUNNING"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job with status {job['status']}"
            )
            
        JobManager.update_job_status(
            job_id, 
            JobStatus.CANCELED, 
            error="Job canceled by user"
        )
        return {"message": f"Job {job_id} has been canceled"}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


@router.delete("/", response_model=Dict[str, int])
async def cleanup_jobs(days: int = 7):
    """Clean up old jobs.
    
    Args:
        days: Remove jobs older than this many days.
        
    Returns:
        Number of jobs removed.
    """
    try:
        removed = JobManager.cleanup_old_jobs(days=days)
        return {"removed_jobs": removed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clean up jobs: {str(e)}") 