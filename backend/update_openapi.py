#!/usr/bin/env python
"""
OpenAPI Update Script

This script automatically updates the OpenAPI specification in swagger.yaml
based on the actual routes defined in the Flask application.

It ensures:
1. All Flask routes have corresponding entries in the OpenAPI spec
2. Path parameters are correctly defined
3. Method definitions are accurate
"""

import os
import sys
import yaml
import re
from pathlib import Path
import inspect
import importlib.util
from flask import Flask, current_app

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def create_test_app():
    """Create a Flask app for route inspection without actually running it."""
    from app import create_app
    app = create_app("config.TestingConfig")
    
    # We need to push an app context to ensure all routes are registered
    with app.app_context():
        # Force registration of all routes
        app.url_map  # accessing this property ensures routes are registered
        
    return app

def load_openapi_spec(filepath):
    """Load OpenAPI specification from YAML file."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def save_openapi_spec(filepath, spec):
    """Save OpenAPI specification to YAML file."""
    with open(filepath, 'w') as f:
        yaml.dump(spec, f, sort_keys=False, default_flow_style=False)
    print(f"{GREEN}Saved updated OpenAPI spec to {filepath}{RESET}")

def normalize_path(path):
    """Normalize API path for comparison."""
    # Replace Flask path parameters (e.g., <param>) with OpenAPI format {param}
    path = re.sub(r'<([^>]+)>', r'{\1}', path)
    # Remove trailing slashes
    path = path.rstrip('/')
    return path

def get_flask_routes(app):
    """Extract all routes from Flask app."""
    routes = []
    # Debug info
    print(f"URL Map rules count: {len(list(app.url_map.iter_rules()))}")
    
    for rule in app.url_map.iter_rules():
        # Skip static routes and browser OPTIONS requests
        if rule.endpoint == 'static':
            continue
        
        # Debug information for each rule
        print(f"Processing rule: {rule.rule} - {rule.methods} - {rule.endpoint}")
        
        # Normalize the path
        path = normalize_path(rule.rule)
        # Extract HTTP methods
        methods = [m.lower() for m in rule.methods if m not in ('HEAD', 'OPTIONS')]
        
        if methods:  # Only include if there are remaining methods
            routes.append({
                'path': path,
                'methods': methods,
                'endpoint': rule.endpoint
            })
    
    return routes

def merge_openapi_paths(spec, routes):
    """Merge Flask routes into OpenAPI spec."""
    # Start with existing paths
    if 'paths' not in spec:
        spec['paths'] = {}
    
    # Dictionary to track new paths
    new_paths = {}
    updated_paths = {}
    
    # Process each Flask route
    for route in routes:
        path = route['path']
        endpoint = route['endpoint']
        
        # Skip specific internal paths
        if path == '/docs' or path.startswith('/static'):
            continue
            
        # For docs directory only skip the sub-paths
        if '/docs/' in path:
            continue
            
        # Skip paths without correct prefixes for OpenAPI
        valid_prefixes = ['/api/v1/', '/api/bms/', '/api/', '/bms/']
        has_valid_prefix = any(path.startswith(prefix) for prefix in valid_prefixes)
        if not has_valid_prefix and not path == '/api':
            continue
        
        # Print debug info
        print(f"Adding path to OpenAPI spec: {path}")
        
        # Check if the path already exists in the spec
        if path in spec['paths']:
            # Path exists, check methods
            for method in route['methods']:
                if method not in spec['paths'][path]:
                    # Method is missing, add it
                    spec['paths'][path][method] = create_default_operation(path, method, endpoint)
                    updated_paths[path] = method
        else:
            # Path doesn't exist, create it
            new_paths[path] = {
                method: create_default_operation(path, method, endpoint)
                for method in route['methods']
            }
    
    # Add all new paths to the spec
    for path, methods in new_paths.items():
        spec['paths'][path] = methods
    
    # Print summary
    if new_paths:
        print(f"\n{GREEN}Added {len(new_paths)} new paths to OpenAPI spec:{RESET}")
        for path in new_paths:
            print(f"  {path}")
    
    if updated_paths:
        print(f"\n{GREEN}Updated {len(updated_paths)} existing paths with new methods:{RESET}")
        for path, method in updated_paths.items():
            print(f"  {path} - Added {method.upper()} method")
    
    return spec

def create_default_operation(path, method, endpoint):
    """Create a default operation object for a path and method."""
    # Extract operation ID from endpoint
    parts = endpoint.split('.')
    operation_id = parts[-1] if len(parts) > 1 else endpoint
    
    # Extract path parameters
    path_params = re.findall(r'{([^}]+)}', path)
    parameters = []
    
    for param in path_params:
        parameters.append({
            'name': param,
            'in': 'path',
            'required': True,
            'schema': {
                'type': 'string'
            }
        })
    
    # Create a basic operation object
    operation = {
        'summary': f'{method.upper()} {path}',
        'operationId': operation_id,
        'tags': ['Auto-Generated'],
    }
    
    # Add parameters if any
    if parameters:
        operation['parameters'] = parameters
    
    # Add request body for non-GET methods
    if method in ('post', 'put', 'patch'):
        operation['requestBody'] = {
            'required': True,
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object'
                    }
                }
            }
        }
    
    # Add responses
    operation['responses'] = {
        '200': {
            'description': 'Successful operation',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object'
                    }
                }
            }
        },
        '400': {
            'description': 'Bad request',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'error': {
                                'type': 'string'
                            }
                        }
                    }
                }
            }
        }
    }
    
    return operation

def update_openapi():
    """Main update function."""
    print(f"Updating OpenAPI Specification based on Flask routes...")
    
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
    
    # Create Flask app and get routes
    try:
        app = create_test_app()
        routes = get_flask_routes(app)
        print(f"Found {len(routes)} routes in Flask app")
    except Exception as e:
        print(f"{RED}Error retrieving Flask routes: {e}{RESET}")
        return False
    
    # Make a backup of the original spec
    backup_path = swagger_path.with_suffix('.yaml.bak')
    try:
        with open(swagger_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        print(f"Created backup of OpenAPI spec at {backup_path}")
    except Exception as e:
        print(f"{YELLOW}Warning: Failed to create backup: {e}{RESET}")
    
    # Update the OpenAPI spec
    try:
        updated_spec = merge_openapi_paths(spec, routes)
        save_openapi_spec(swagger_path, updated_spec)
        print(f"{GREEN}Successfully updated OpenAPI spec with Flask routes{RESET}")
        return True
    except Exception as e:
        print(f"{RED}Error updating OpenAPI spec: {e}{RESET}")
        return False

def main():
    """Main entry point."""
    success = update_openapi()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 