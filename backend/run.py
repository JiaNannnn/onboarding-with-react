#!/usr/bin/env python
"""
Run Script for BMS Points API

This script provides a command-line interface for starting the BMS Points API
server with various configuration options.
"""
import os
import sys
import argparse
import signal
import atexit
import threading
from app import create_app
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Track non-daemon threads for cleanup
_threads = []

def cleanup_threads():
    """Clean up any remaining threads at exit."""
    for thread in threading.enumerate():
        if thread != threading.current_thread() and not thread.daemon:
            print(f"Waiting for thread {thread.name} to complete...")
            thread.join(timeout=2.0)
            if thread.is_alive():
                print(f"Thread {thread.name} did not complete in time")

def signal_handler(sig, frame):
    """Handle termination signals."""
    print("Received shutdown signal, cleaning up...")
    cleanup_threads()
    sys.exit(0)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run BMS Points API server")
    
    parser.add_argument("--port", type=int, default=5000,
                        help="Port to run the API on (default: 5000)")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                        help="Host to run the API on (default: 0.0.0.0)")
    parser.add_argument("--env", choices=["development", "testing", "production"],
                        default="development", 
                        help="Environment to run in (default: development)")
    parser.add_argument("--debug", action="store_true",
                        help="Run in debug mode")
    
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_args()
    
    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register cleanup function to run at exit
    atexit.register(cleanup_threads)
    
    # Override thread creation to ensure daemon=False by default
    original_thread_init = threading.Thread.__init__
    def patched_thread_init(self, *args, **kwargs):
        if 'daemon' not in kwargs:
            kwargs['daemon'] = False
        original_thread_init(self, *args, **kwargs)
    threading.Thread.__init__ = patched_thread_init
    
    # Map environment to config class
    env_config_map = {
        "development": "config.DevelopmentConfig",
        "testing": "config.TestingConfig",
        "production": "config.ProductionConfig"
    }
    
    # Set Flask environment variable
    os.environ["FLASK_ENV"] = args.env
    
    # Create app with appropriate config
    app = create_app(env_config_map[args.env])
    
    # Run app
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug or args.env == "development",
        threaded=True
    )

if __name__ == "__main__":
    main() 