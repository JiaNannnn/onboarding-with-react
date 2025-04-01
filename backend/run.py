#!/usr/bin/env python
"""
Run Script for BMS Points API

This script provides a command-line interface for starting the BMS Points API
server with various configuration options.
"""
import os
import sys
import argparse
from app import create_app
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
        debug=args.debug or args.env == "development"
    )

if __name__ == "__main__":
    main() 