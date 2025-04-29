#!/usr/bin/env python
"""
OpenAPI Cleanup Script

This script removes invalid paths from the OpenAPI specification that
don't exist in the actual Flask application.
"""

import os
import sys
import yaml
import re
from pathlib import Path

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

# Paths that should be removed from the OpenAPI spec
INVALID_PATHS = [
    # Empty path
    ' ',
    
    # Paths without required prefixes
    '/networks',
    '/status',
    '/telemetry',
    '/network-config',
    
    # Paths with incorrect prefixes
    '/v1/devices/discover',
    '/v1/devices/discover/{taskId}',
    '/v1/devices/{deviceId}/points',
    '/v1/edge/discover-devices',
    '/v1/edge/network-config',
    '/v1/points/group',
    '/v1/points/map',
    '/v1/points/search',
    '/v1/tasks/{taskId}',
    
    # Duplicate alias paths that don't exist directly
    '/api/device-points',
    '/api/device-points/status/{taskId}',
    '/api/discover-devices',
    '/api/discover-devices/{taskId}',
    '/api/fetch-points',
    '/api/group-points',
    '/api/map-points',
    '/api/ping',
    '/bms/ai-group-points',
    '/fetch-points/{taskId}',
]

def load_openapi_spec(filepath):
    """Load OpenAPI specification from YAML file."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def save_openapi_spec(filepath, spec):
    """Save OpenAPI specification to YAML file."""
    with open(filepath, 'w') as f:
        yaml.dump(spec, f, sort_keys=False, default_flow_style=False)
    print(f"{GREEN}Saved cleaned OpenAPI spec to {filepath}{RESET}")

def clean_openapi_spec(spec):
    """Remove invalid paths from the OpenAPI spec."""
    if 'paths' not in spec:
        print(f"{YELLOW}No paths found in OpenAPI spec{RESET}")
        return spec
    
    # Keep track of removed paths
    removed_paths = []
    
    # Remove invalid paths
    for path in INVALID_PATHS:
        if path in spec['paths']:
            del spec['paths'][path]
            removed_paths.append(path)
    
    # Print summary
    if removed_paths:
        print(f"\n{GREEN}Removed {len(removed_paths)} invalid paths from OpenAPI spec:{RESET}")
        for path in removed_paths:
            print(f"  {path}")
    else:
        print(f"{YELLOW}No invalid paths found in OpenAPI spec{RESET}")
    
    return spec

def main():
    """Main entry point."""
    print(f"Cleaning OpenAPI Specification...")
    
    # Get the base directory
    base_dir = Path(__file__).parent
    
    # Load OpenAPI spec
    swagger_path = base_dir / 'app' / 'api' / 'swagger.yaml'
    
    try:
        spec = load_openapi_spec(swagger_path)
        print(f"Loaded OpenAPI spec from {swagger_path}")
    except Exception as e:
        print(f"{RED}Error loading OpenAPI spec: {e}{RESET}")
        return False
    
    # Make a backup of the original spec
    backup_path = swagger_path.with_suffix('.yaml.bak')
    try:
        with open(swagger_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        print(f"Created backup of OpenAPI spec at {backup_path}")
    except Exception as e:
        print(f"{YELLOW}Warning: Failed to create backup: {e}{RESET}")
    
    # Clean the OpenAPI spec
    try:
        cleaned_spec = clean_openapi_spec(spec)
        save_openapi_spec(swagger_path, cleaned_spec)
        print(f"{GREEN}Successfully cleaned OpenAPI spec{RESET}")
        return True
    except Exception as e:
        print(f"{RED}Error cleaning OpenAPI spec: {e}{RESET}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 