#!/usr/bin/env python
"""
Backend Restart Helper

This script ensures clean restart of the backend service,
clearing any temporary cache files and reloading configurations.
"""

import os
import sys
import shutil
import subprocess
import time
import signal
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the directory of this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, 'cache')

def clear_temporary_files():
    """Clear temporary cache files"""
    logger.info("Clearing cache directory...")
    
    # Create cache directory if it doesn't exist
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        logger.info("Created cache directory")
        return
    
    # Clear existing cache files
    try:
        # Keep directory but remove all files
        for file_name in os.listdir(CACHE_DIR):
            file_path = os.path.join(CACHE_DIR, file_name)
            if os.path.isfile(file_path):
                os.unlink(file_path)
                logger.info(f"Removed cache file: {file_name}")
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")

def restart_backend():
    """Restart the backend service"""
    logger.info("Restarting backend service...")
    
    # Run the server
    try:
        # Start the server using python run.py
        server_cmd = [sys.executable, 'run.py']
        logger.info(f"Starting server with command: {' '.join(server_cmd)}")
        
        # Start the process and return it
        process = subprocess.Popen(
            server_cmd,
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Print the first few lines of output
        logger.info("Server starting...")
        for _ in range(10):
            line = process.stdout.readline()
            if line:
                logger.info(f"Server: {line.rstrip()}")
            else:
                break
            
            # Check if the server is ready
            if "Running on" in line:
                logger.info("Server is ready!")
                break
        
        return process
    
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        return None

if __name__ == "__main__":
    logger.info("=== Backend Restart Helper ===")
    
    # Clear temporary files
    clear_temporary_files()
    
    # Start the server
    server_process = restart_backend()
    
    if server_process:
        try:
            logger.info("Server is running. Press Ctrl+C to stop...")
            # Keep the script running until user interrupts
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping server...")
            # Terminate the server process
            server_process.terminate()
            server_process.wait(timeout=5)
            logger.info("Server stopped.")
    else:
        logger.error("Failed to start server.")
        sys.exit(1) 