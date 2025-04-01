#!/usr/bin/env python
"""
Deployment Script for BMS Points API with AI-Based Grouping and Mapping

This script sets up the environment and configuration for running the
BMS Points API with AI-based grouping and mapping capabilities.
"""
import os
import sys
import argparse
import shutil
import subprocess
import platform
from pathlib import Path

# Default values
DEFAULT_PORT = 5000
DEFAULT_ENV = "development"
DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_CONFIG_PATH = os.path.join("config.py")
DEFAULT_VENV_PATH = os.path.join(".venv")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Deploy BMS Points API with AI capabilities")
    
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Port to run the API on (default: {DEFAULT_PORT})")
    parser.add_argument("--env", choices=["development", "testing", "production"],
                        default=DEFAULT_ENV, help=f"Environment to run in (default: {DEFAULT_ENV})")
    parser.add_argument("--openai-key", type=str, 
                        help="OpenAI API key for AI-based grouping and mapping")
    parser.add_argument("--openai-model", type=str, default=DEFAULT_OPENAI_MODEL,
                        help=f"OpenAI model to use (default: {DEFAULT_OPENAI_MODEL})")
    parser.add_argument("--install", action="store_true",
                        help="Install dependencies")
    parser.add_argument("--setup-env", action="store_true",
                        help="Set up environment variables")
    parser.add_argument("--run", action="store_true",
                        help="Run the API server")
    parser.add_argument("--test", action="store_true",
                        help="Run the test suite")
    
    # If no arguments provided, show help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    return parser.parse_args()

def setup_virtualenv(venv_path):
    """Set up a virtual environment."""
    if os.path.exists(venv_path):
        print(f"Virtual environment already exists at {venv_path}")
        return
    
    print("Setting up virtual environment...")
    try:
        # Create virtual environment
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
        print(f"Virtual environment created at {venv_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        sys.exit(1)

def install_dependencies(venv_path):
    """Install dependencies in the virtual environment."""
    print("Installing dependencies...")
    
    # Determine pip path based on platform
    if platform.system() == "Windows":
        pip_path = os.path.join(venv_path, "Scripts", "pip")
    else:
        pip_path = os.path.join(venv_path, "bin", "pip")
    
    # Install dependencies from requirements.txt
    try:
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        
        # Install additional dependencies for AI features
        subprocess.run([pip_path, "install", "openai==1.7.0", "pandas==2.1.0"], check=True)
        
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def setup_env_file(args):
    """Set up environment variables in .env file."""
    print("Setting up environment variables...")
    
    # Check if .env.example exists
    env_example_path = os.path.join(".env.example")
    env_path = os.path.join(".env")
    
    if os.path.exists(env_example_path):
        # Copy .env.example to .env if .env doesn't exist
        if not os.path.exists(env_path):
            shutil.copy(env_example_path, env_path)
            print("Created .env file from .env.example")
    else:
        # Create new .env file
        with open(env_path, "w") as f:
            f.write("# Environment variables for BMS Points API\n\n")
        print("Created new .env file")
    
    # Update .env file with OpenAI API key and model if provided
    if args.openai_key:
        env_lines = []
        openai_key_found = False
        openai_model_found = False
        
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                env_lines = f.readlines()
        
        # Update existing lines or append new ones
        for i, line in enumerate(env_lines):
            if line.strip().startswith("OPENAI_API_KEY="):
                env_lines[i] = f"OPENAI_API_KEY={args.openai_key}\n"
                openai_key_found = True
            elif line.strip().startswith("OPENAI_MODEL="):
                env_lines[i] = f"OPENAI_MODEL={args.openai_model}\n"
                openai_model_found = True
        
        # Append OpenAI API key and model if not found
        if not openai_key_found:
            env_lines.append(f"OPENAI_API_KEY={args.openai_key}\n")
        if not openai_model_found:
            env_lines.append(f"OPENAI_MODEL={args.openai_model}\n")
        
        # Write updated .env file
        with open(env_path, "w") as f:
            f.writelines(env_lines)
        
        print("Updated .env file with OpenAI API key and model")
    else:
        print("OpenAI API key not provided, skipping environment setup")
        print("NOTE: AI-based grouping and mapping will fall back to rule-based methods")

def run_api_server(args):
    """Run the API server."""
    print(f"Starting API server in {args.env} mode on port {args.port}...")
    
    # Set environment variables
    env = os.environ.copy()
    env["FLASK_ENV"] = args.env
    env["FLASK_APP"] = "app:create_app()"
    
    # Run server
    cmd = [sys.executable, "run.py", "--port", str(args.port), "--env", args.env]
    try:
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("\nAPI server stopped")
    except Exception as e:
        print(f"Error running API server: {e}")
        sys.exit(1)

def run_tests():
    """Run the test suite."""
    print("Running tests...")
    
    # Run pytest
    try:
        subprocess.run([sys.executable, "-m", "pytest", "tests", "-v"])
    except subprocess.CalledProcessError as e:
        print(f"Error running tests: {e}")
        sys.exit(1)

def main():
    """Main function."""
    args = parse_args()
    
    # Virtual environment path
    venv_path = DEFAULT_VENV_PATH
    
    # Setup and installation
    if args.install:
        setup_virtualenv(venv_path)
        install_dependencies(venv_path)
    
    # Setup environment variables
    if args.setup_env:
        setup_env_file(args)
    
    # Run tests
    if args.test:
        run_tests()
    
    # Run API server
    if args.run:
        run_api_server(args)

if __name__ == "__main__":
    main() 