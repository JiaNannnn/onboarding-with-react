import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class ReasoningLogger:
    """Logger for reasoning and reflection data."""
    
    def __init__(self, log_dir: str = "logs/reasoning"):
        """Initialize the reasoning logger.
        
        Args:
            log_dir: Directory to store logs
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure standard logger
        self.logger = logging.getLogger("reasoning")
        self.logger.setLevel(logging.INFO)
        
        # File handler for all reasoning logs
        file_handler = logging.FileHandler(f"{log_dir}/reasoning_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(file_handler)
    
    def log_reasoning_chain(
        self,
        point_id: str,
        reasoning_chain: List[str],
        result: Dict[str, Any]
    ):
        """Log a reasoning chain.
        
        Args:
            point_id: ID of the point
            reasoning_chain: Chain of reasoning steps
            result: Final mapping result
        """
        # Log to standard logger
        self.logger.info(f"Reasoning for point {point_id}: {len(reasoning_chain)} steps, result: {result['mapping']['enosPoint']}")
        
        # Create detailed log file for this reasoning chain
        chain_dir = f"{self.log_dir}/chains"
        os.makedirs(chain_dir, exist_ok=True)
        
        with open(f"{chain_dir}/{point_id}.json", "w") as f:
            json.dump({
                "point_id": point_id,
                "timestamp": datetime.now().isoformat(),
                "reasoning_chain": reasoning_chain,
                "result": result
            }, f, indent=2)
    
    def log_reflection(
        self,
        point_id: str,
        reflection: Dict[str, Any],
        original_result: Dict[str, Any],
        new_result: Dict[str, Any]
    ):
        """Log a reflection.
        
        Args:
            point_id: ID of the point
            reflection: Reflection data
            original_result: Original mapping result
            new_result: New mapping result after reflection
        """
        # Log to standard logger
        self.logger.info(f"Reflection for point {point_id}: original={original_result['mapping']['enosPoint']}, new={new_result['mapping']['enosPoint']}")
        
        # Create detailed log file for this reflection
        reflection_dir = f"{self.log_dir}/reflections"
        os.makedirs(reflection_dir, exist_ok=True)
        
        with open(f"{reflection_dir}/{point_id}.json", "w") as f:
            json.dump({
                "point_id": point_id,
                "timestamp": datetime.now().isoformat(),
                "reflection": reflection,
                "original_result": original_result,
                "new_result": new_result
            }, f, indent=2)
            
    def log_progress(
        self,
        operation_id: str,
        operation_type: str,
        total: int,
        current: int,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log progress of an operation.
        
        Args:
            operation_id: ID of the operation
            operation_type: Type of operation (e.g., "mapping", "reflection")
            total: Total number of items
            current: Current item number
            status: Status of the operation
            details: Optional details about the operation
        """
        # Calculate percentage
        percentage = (current / total) * 100 if total > 0 else 0
        
        # Log to standard logger
        self.logger.info(f"Progress for {operation_type} {operation_id}: {current}/{total} ({percentage:.1f}%), status: {status}")
        
        # Create progress log file
        progress_dir = f"{self.log_dir}/progress"
        os.makedirs(progress_dir, exist_ok=True)
        
        # Read existing progress file if it exists
        progress_file = f"{progress_dir}/{operation_id}.json"
        progress_data = {}
        
        if os.path.exists(progress_file):
            try:
                with open(progress_file, "r") as f:
                    progress_data = json.load(f)
            except json.JSONDecodeError:
                progress_data = {}
        
        # Update progress data
        progress_data.update({
            "operation_id": operation_id,
            "operation_type": operation_type,
            "total": total,
            "current": current,
            "percentage": percentage,
            "status": status,
            "last_updated": datetime.now().isoformat()
        })
        
        # Add details if provided
        if details:
            if "history" not in progress_data:
                progress_data["history"] = []
            
            progress_data["history"].append({
                "timestamp": datetime.now().isoformat(),
                "current": current,
                "status": status,
                "details": details
            })
        
        # Write updated progress data
        with open(progress_file, "w") as f:
            json.dump(progress_data, f, indent=2)
            
    def get_progress(self, operation_id: str) -> Dict[str, Any]:
        """Get progress data for an operation.
        
        Args:
            operation_id: ID of the operation
            
        Returns:
            Progress data
        """
        progress_file = f"{self.log_dir}/progress/{operation_id}.json"
        
        if os.path.exists(progress_file):
            try:
                with open(progress_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"error": "Invalid progress data file"}
        
        return {"error": "Operation not found"} 