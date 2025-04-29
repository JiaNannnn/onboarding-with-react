# This file is renamed from logging.py to avoid conflicts with Python's built-in logging module.

import logging
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

class ReasoningLogger:
    """Logger for reasoning chains and reflection processes."""
    
    def __init__(self, log_dir: str = 'logs'):
        """Initialize the reasoning logger."""
        self.log_dir = log_dir
        self.reasoning_dir = os.path.join(log_dir, 'reasoning', 'chains')
        self.reflection_dir = os.path.join(log_dir, 'reasoning', 'reflections')
        self.progress_dir = os.path.join(log_dir, 'progress')
        
        # Ensure log directories exist
        for dir_path in [self.reasoning_dir, self.reflection_dir, self.progress_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        # Configure standard logging
        self.logger = logging.getLogger('reasoning')
        self.logger.setLevel(logging.INFO)
        
        # Handler setup only if not already added to avoid duplicate logs
        if not self.logger.handlers:
            # File handler for reasoning logs
            handler = logging.FileHandler(os.path.join(log_dir, 'reasoning.log'))
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_reasoning_chain(self, point_id: str, reasoning_chain: Dict[str, Any]) -> None:
        """
        Log a reasoning chain for a specific point.
        
        Args:
            point_id: Unique identifier for the point
            reasoning_chain: Dictionary containing the reasoning chain
        """
        try:
            # Add timestamp
            reasoning_chain['timestamp'] = datetime.now().isoformat()
            
            # Save to file
            file_path = os.path.join(self.reasoning_dir, f"{point_id}.json")
            with open(file_path, 'w') as f:
                json.dump(reasoning_chain, f, indent=2)
            
            self.logger.info(f"Logged reasoning chain for point {point_id}")
        except Exception as e:
            self.logger.error(f"Failed to log reasoning chain for point {point_id}: {e}")
    
    def log_reflection(self, point_id: str, reflection_data: Dict[str, Any]) -> None:
        """
        Log reflection data for a specific point.
        
        Args:
            point_id: Unique identifier for the point
            reflection_data: Dictionary containing the reflection data
        """
        try:
            # Add timestamp
            reflection_data['timestamp'] = datetime.now().isoformat()
            
            # Save to file
            file_path = os.path.join(self.reflection_dir, f"{point_id}.json")
            with open(file_path, 'w') as f:
                json.dump(reflection_data, f, indent=2)
            
            self.logger.info(f"Logged reflection for point {point_id}")
        except Exception as e:
            self.logger.error(f"Failed to log reflection for point {point_id}: {e}")
    
    def log_operation_progress(self, operation_id: str, progress: Dict[str, Any]) -> None:
        """
        Log progress of an operation.
        
        Args:
            operation_id: Unique identifier for the operation
            progress: Dictionary containing progress information
        """
        try:
            # Check if progress file exists, update or create
            file_path = os.path.join(self.progress_dir, f"{operation_id}.json")
            
            # Add timestamp
            progress['last_updated'] = datetime.now().isoformat()
            
            if os.path.exists(file_path):
                # Read existing progress
                with open(file_path, 'r') as f:
                    existing_progress = json.load(f)
                
                # Update with new progress
                existing_progress.update(progress)
                
                # Save updated progress
                with open(file_path, 'w') as f:
                    json.dump(existing_progress, f, indent=2)
            else:
                # Create new progress file
                with open(file_path, 'w') as f:
                    json.dump(progress, f, indent=2)
            
            self.logger.info(f"Logged progress for operation {operation_id}: {progress.get('status', 'unknown')}")
        except Exception as e:
            self.logger.error(f"Failed to log progress for operation {operation_id}: {e}")
    
    def get_progress(self, operation_id: str) -> Dict[str, Any]:
        """
        Get progress of an operation.
        
        Args:
            operation_id: Unique identifier for the operation
            
        Returns:
            Dictionary containing progress information or error message
        """
        try:
            file_path = os.path.join(self.progress_dir, f"{operation_id}.json")
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    progress = json.load(f)
                return progress
            else:
                return {"error": f"No progress found for operation {operation_id}"}
        except Exception as e:
            self.logger.error(f"Failed to get progress for operation {operation_id}: {e}")
            return {"error": f"Failed to get progress: {str(e)}"}
    
    def list_operations(self) -> List[str]:
        """
        List all operations with progress information.
        
        Returns:
            List of operation IDs
        """
        try:
            operations = []
            for file_name in os.listdir(self.progress_dir):
                if file_name.endswith('.json'):
                    operations.append(file_name.replace('.json', ''))
            return operations
        except Exception as e:
            self.logger.error(f"Failed to list operations: {e}")
            return [] 