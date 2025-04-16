#!/usr/bin/env python
import os
import sys
import time
import argparse
import subprocess
import multiprocessing
from config import DevelopmentConfig, ProductionConfig, TestingConfig

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='BMS API Server + Worker')
    parser.add_argument(
        '--host', 
        default='0.0.0.0',
        help='Host to bind the server to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=5000,
        help='Port to bind the server to (default: 5000)'
    )
    parser.add_argument(
        '--env', 
        choices=['development', 'production', 'testing'],
        default='development',
        help='Environment to run in (default: development)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode (overrides environment setting)'
    )
    parser.add_argument(
        '--concurrency',
        type=int,
        default=4,
        help='Number of worker processes (default: 4)'
    )
    return parser.parse_args()

def run_web_server(args):
    """Run the Flask web server"""
    cmd = [
        sys.executable, 'run.py',
        '--host', args.host,
        '--port', str(args.port),
        '--env', args.env
    ]
    
    if args.debug:
        cmd.append('--debug')
    
    print(f"Starting web server: {' '.join(cmd)}")
    return subprocess.Popen(cmd)

def run_celery_worker(args):
    """Run the Celery worker"""
    # On Windows, we need to use the 'solo' pool
    pool_type = 'solo' if os.name == 'nt' else 'prefork'
    
    cmd = [
        sys.executable, 'worker.py',
        '--env', args.env,
        '--concurrency', str(args.concurrency),
        '--pool', pool_type
    ]
    
    print(f"Starting Celery worker: {' '.join(cmd)}")
    return subprocess.Popen(cmd)

def main():
    """Main entry point"""
    args = parse_args()
    
    print(f"Starting BMS API in {args.env} mode")
    
    # Start the web server and worker
    web_process = run_web_server(args)
    worker_process = run_celery_worker(args)
    
    try:
        # Monitor processes
        while True:
            time.sleep(1)
            
            # Check if either process has terminated
            if web_process.poll() is not None:
                print("Web server stopped. Shutting down...")
                if worker_process.poll() is None:
                    worker_process.terminate()
                break
                
            if worker_process.poll() is not None:
                print("Celery worker stopped. Shutting down...")
                if web_process.poll() is None:
                    web_process.terminate()
                break
    except KeyboardInterrupt:
        print("Shutting down...")
        if web_process.poll() is None:
            web_process.terminate()
        if worker_process.poll() is None:
            worker_process.terminate()
    
    # Wait for processes to terminate
    web_process.wait()
    worker_process.wait()
    
    print("Shutdown complete")

if __name__ == '__main__':
    # This check is necessary for Windows due to the multiprocessing module
    multiprocessing.freeze_support()
    main() 