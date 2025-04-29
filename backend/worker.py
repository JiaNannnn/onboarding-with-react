#!/usr/bin/env python
import os
import argparse
from app import celery, create_app
from config import DevelopmentConfig, ProductionConfig, TestingConfig

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='BMS API Celery Worker')
    parser.add_argument(
        '--env', 
        choices=['development', 'production', 'testing'],
        default='development',
        help='Environment to run in (default: development)'
    )
    parser.add_argument(
        '--concurrency',
        type=int,
        default=4,
        help='Number of worker processes (default: 4)'
    )
    parser.add_argument(
        '--loglevel',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Log level (default: INFO)'
    )
    parser.add_argument(
        '--pool',
        choices=['prefork', 'eventlet', 'gevent', 'solo'],
        default='prefork',
        help='Worker pool implementation (default: prefork)'
    )
    return parser.parse_args()

def main():
    """Main entry point to start the Celery worker"""
    args = parse_args()
    
    # Get configuration class based on environment
    config_class = config_map.get(args.env, DevelopmentConfig)
    
    # Initialize Flask application to configure Celery
    app = create_app(config_class)
    
    # Define worker command arguments
    worker_args = [
        'worker',
        '--loglevel=' + args.loglevel,
        '--concurrency=' + str(args.concurrency),
        '--pool=' + args.pool
    ]
    
    # Special case for Windows - need to use solo pool
    if os.name == 'nt' and args.pool == 'prefork':
        print("WARNING: Using 'solo' pool instead of 'prefork' on Windows")
        worker_args = [arg.replace('prefork', 'solo') if '--pool=' in arg else arg for arg in worker_args]
    
    # Start the worker
    with app.app_context():
        celery.worker_main(worker_args)

if __name__ == '__main__':
    main() 