"""
Example of using the JobManager to make EnOS API calls asynchronously.

This example demonstrates how to:
1. Create an EnOS API job
2. Check job status
3. Handle job results
"""

import time
import logging
from typing import Dict, Any
from backend.app.utils.job_utils import JobManager, JobStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def job_completed_callback(job: Dict[str, Any]) -> None:
    """Callback function that runs when a job completes.
    
    Args:
        job: The job data dictionary
    """
    job_id = job["id"]
    status = job["status"]
    
    if status == JobStatus.COMPLETED:
        logger.info(f"Job {job_id} completed successfully!")
        logger.info(f"Result: {job['result']}")
    else:
        logger.error(f"Job {job_id} failed with error: {job['error']}")

def main():
    """Main example function showing EnOS API job usage."""
    
    # EnOS API credentials - these would typically come from environment variables
    # DO NOT hardcode these values in a real application
    ACCESS_KEY = "your_access_key"
    SECRET_KEY = "your_secret_key"
    
    # Example EnOS API call parameters
    api_url = "https://api.envisioniot.com/device-connection/v2.1/devices"
    api_data = {
        "orgId": "your_org_id",
        "modelId": "your_model_id",
        "pageSize": 10,
        "pageNo": 1
    }
    
    # Create an EnOS API job to fetch device list
    job_id = JobManager.create_enos_api_job(
        job_type="fetch_devices",
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        url=api_url,
        data=api_data,
        timeout=30,
        callback=job_completed_callback
    )
    
    logger.info(f"Created EnOS API job with ID: {job_id}")
    
    # Poll for job status
    # In a real application, you might use a notification system instead
    max_attempts = 10
    attempts = 0
    
    while attempts < max_attempts:
        try:
            job = JobManager.get_job(job_id)
            status = job["status"]
            progress = job["progress"]
            
            logger.info(f"Job status: {status}, Progress: {progress}%")
            
            if status in ["COMPLETED", "FAILED", "CANCELED"]:
                # Job has reached a terminal state
                if status == "COMPLETED":
                    logger.info(f"Job completed successfully with result: {job['result']}")
                elif status == "FAILED":
                    logger.error(f"Job failed with error: {job['error']}")
                break
                
            # Wait before checking again
            time.sleep(1)
            attempts += 1
            
        except KeyError as e:
            logger.error(f"Error retrieving job: {str(e)}")
            break
    
    if attempts >= max_attempts:
        logger.warning("Maximum polling attempts reached without job completion")
    
    # List all jobs
    all_jobs = JobManager.list_jobs()
    logger.info(f"Total jobs in system: {len(all_jobs)}")
    
    # Clean up old jobs
    removed_count = JobManager.cleanup_old_jobs(days=1)
    logger.info(f"Cleaned up {removed_count} old jobs")

if __name__ == "__main__":
    main() 