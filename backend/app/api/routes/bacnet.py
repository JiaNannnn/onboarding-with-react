"""
BACnet API Router

This module provides RESTful endpoints for BACnet operations including
network discovery, device scanning, and point reading/writing.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field

from app.utils.bacnet_utils import (
    connect_to_bacnet,
    discover_networks,
    scan_devices,
    get_device_points,
    read_point_value,
    write_point_value
)
from ...utils.job_utils import JobManager, JobStatus

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/bacnet", tags=["bacnet"])

# Models
class NetworkResponse(BaseModel):
    """Response model for BACnet networks."""
    id: str
    name: str
    description: Optional[str] = None


class DeviceResponse(BaseModel):
    """Response model for BACnet devices."""
    id: str
    name: str
    address: str
    instance: str
    model: Optional[str] = None
    vendor: Optional[str] = None
    network: str
    asset_id: Optional[str] = None


class PointResponse(BaseModel):
    """Response model for BACnet points."""
    name: str
    description: Optional[str] = None
    object_type: str
    object_id: int
    present_value: Any
    units: Optional[str] = None
    instance: str


class WritePointRequest(BaseModel):
    """Request model for writing to a BACnet point."""
    value: Any = Field(..., description="Value to write to the point")
    priority: Optional[int] = Field(None, description="Priority level (1-16, with 1 being highest)")


class JobResponse(BaseModel):
    """Response model for asynchronous jobs."""
    id: str
    type: str
    status: str
    progress: int
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None


# Routes
@router.get("/networks", response_model=List[NetworkResponse])
async def get_networks(asset_id: Optional[str] = None):
    """Discover BACnet networks.
    
    Args:
        asset_id: Optional asset ID to filter networks.
        
    Returns:
        List of discovered networks.
    """
    try:
        networks = discover_networks(asset_id)
        return networks
    except Exception as e:
        logger.exception("Error discovering networks")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/networks/{network_id}/scan", response_model=JobResponse)
async def scan_network_devices(
    network_id: str,
    asset_id: Optional[str] = None
):
    """Scan for devices on a BACnet network (async operation).
    
    Args:
        network_id: Network ID to scan.
        asset_id: Optional asset ID to filter results.
        
    Returns:
        Job details for the scanning operation.
    """
    try:
        # Create an async job for network scanning
        job_id = JobManager.create_job(
            job_type="network_scan",
            params={
                "network_id": network_id,
                "asset_id": asset_id
            }
        )
        
        # Return the job details
        return JobManager.get_job(job_id)
    except Exception as e:
        logger.exception(f"Error scanning network {network_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices/{device_instance}/points", response_model=List[PointResponse])
async def get_points(
    device_instance: str,
    asset_id: str = Query(..., description="Asset ID associated with the device")
):
    """Get all points from a BACnet device.
    
    Args:
        device_instance: BACnet device instance.
        asset_id: Asset ID associated with the device.
        
    Returns:
        List of BACnet points for the device.
    """
    try:
        # For immediate operations, directly call the utility
        points = get_device_points(asset_id, device_instance)
        return points
    except Exception as e:
        logger.exception(f"Error getting points for device {device_instance}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/devices/{device_instance}/points/discover", response_model=JobResponse)
async def discover_device_points(
    device_instance: str,
    asset_id: str = Query(..., description="Asset ID associated with the device")
):
    """Discover points on a BACnet device (async operation).
    
    Args:
        device_instance: BACnet device instance.
        asset_id: Asset ID associated with the device.
        
    Returns:
        Job details for the point discovery operation.
    """
    try:
        # Create an async job for point discovery
        job_id = JobManager.create_job(
            job_type="point_discovery",
            params={
                "device_instance": device_instance,
                "asset_id": asset_id
            }
        )
        
        # Return the job details
        return JobManager.get_job(job_id)
    except Exception as e:
        logger.exception(f"Error discovering points for device {device_instance}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices/{device_instance}/points/{point_instance}", response_model=PointResponse)
async def get_point_value(
    device_instance: str,
    point_instance: str,
    asset_id: str = Query(..., description="Asset ID associated with the device")
):
    """Read current value of a BACnet point.
    
    Args:
        device_instance: BACnet device instance.
        point_instance: BACnet point instance.
        asset_id: Asset ID associated with the device.
        
    Returns:
        Current value and details of the BACnet point.
    """
    try:
        point_data = read_point_value(asset_id, device_instance, point_instance)
        return point_data
    except Exception as e:
        logger.exception(f"Error reading point {point_instance} on device {device_instance}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/devices/{device_instance}/points/{point_instance}", response_model=PointResponse)
async def set_point_value(
    device_instance: str,
    point_instance: str,
    request: WritePointRequest,
    asset_id: str = Query(..., description="Asset ID associated with the device")
):
    """Write a value to a BACnet point.
    
    Args:
        device_instance: BACnet device instance.
        point_instance: BACnet point instance.
        request: Write request containing value and optional priority.
        asset_id: Asset ID associated with the device.
        
    Returns:
        Updated point data after write operation.
    """
    try:
        # Extract value and priority from request
        value = request.value
        priority = request.priority
        
        # Write the value
        result = write_point_value(
            asset_id, 
            device_instance, 
            point_instance, 
            value, 
            priority
        )
        
        return result
    except Exception as e:
        logger.exception(f"Error writing to point {point_instance} on device {device_instance}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """Get status of an asynchronous job.
    
    Args:
        job_id: ID of the job to check.
        
    Returns:
        Current job status and results if completed.
    """
    try:
        return JobManager.get_job(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    except Exception as e:
        logger.exception(f"Error getting job {job_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=List[JobResponse])
async def list_jobs(
    job_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List asynchronous jobs with optional filtering.
    
    Args:
        job_type: Optional filter by job type.
        limit: Maximum number of jobs to return.
        offset: Offset for pagination.
        
    Returns:
        List of jobs matching the filter criteria.
    """
    try:
        return JobManager.list_jobs(job_type=job_type, limit=limit, offset=offset)
    except Exception as e:
        logger.exception("Error listing jobs")
        raise HTTPException(status_code=500, detail=str(e)) 