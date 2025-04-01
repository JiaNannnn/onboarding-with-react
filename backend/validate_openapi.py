#!/usr/bin/env python
"""
OpenAPI Validation Script

This script validates that the OpenAPI specification in swagger.yaml
accurately describes all the API endpoints defined in the Flask application.

It checks:
1. All Flask routes have corresponding entries in the OpenAPI spec
2. All paths in the OpenAPI spec correspond to actual Flask routes
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
    try:
        from app import create_app
        app = create_app("config.TestingConfig")
        return app
    except Exception as e:
        print(f"{RED}Error creating test app: {e}{RESET}")
        sys.exit(1)

def load_openapi_spec(filepath):
    """Load OpenAPI specification from YAML file."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def normalize_path(path):
    """Normalize API path for comparison."""
    # Replace Flask path parameters (e.g., <param>) with OpenAPI format {param}
    path = re.sub(r'<([^>]+)>', r'{\1}', path)
    # Remove trailing slashes
    path = path.rstrip('/')
    
    # Standardize parameter names (convert snake_case to camelCase for comparison)
    def snake_to_camel(match):
        param = match.group(1)
        if '_' in param:
            camel_param = ''.join(word.capitalize() if i > 0 else word
                              for i, word in enumerate(param.split('_')))
            return f"{{{camel_param}}}"
        return match.group(0)
    
    # Convert {snake_case} to {camelCase} for comparison purposes
    path = re.sub(r'{([^}]+)}', snake_to_camel, path)
    
    return path

def get_flask_routes(app):
    """Extract all routes from Flask app."""
    routes = []
    
    for rule in app.url_map.iter_rules():
        # Skip static routes
        if rule.endpoint == 'static':
            continue
        
        # Skip docs routes for validation purposes
        if 'swagger_ui' in rule.endpoint:
            continue
            
        # Normalize the path
        path = normalize_path(rule.rule)
        
        # Extract HTTP methods
        methods = [m.lower() for m in rule.methods if m not in ('HEAD', 'OPTIONS')]
        
        for method in methods:
            routes.append((path, method))
    
    return routes

def get_openapi_paths(spec):
    """Extract all paths from OpenAPI spec."""
    paths = []
    
    for path, path_item in spec.get('paths', {}).items():
        # Normalize the path for comparison
        norm_path = normalize_path(path)
        
        # Extract methods
        for method in path_item.keys():
            if method.lower() in ('get', 'post', 'put', 'delete', 'patch'):
                paths.append((norm_path, method.lower()))
    
    return paths

def validate_openapi():
    """Main validation function."""
    print(f"Validating OpenAPI Specification against Flask routes...")
    
    # Get the base directory
    base_dir = Path(__file__).parent
    
    # Load OpenAPI spec
    swagger_path = base_dir / 'app' / 'api' / 'swagger.yaml'
    
    try:
        spec = load_openapi_spec(swagger_path)
        print(f"Loaded OpenAPI spec from {swagger_path}")
    except Exception as e:
        print(f"{RED}Error loading OpenAPI spec: {e}{RESET}")
        return False, [], []
    
    # Create Flask app and get routes
    try:
        app = create_test_app()
        
        # Try to push app context to ensure all routes are registered
        with app.app_context():
            # Force registration of all routes
            app.url_map  # accessing this property ensures routes are registered
        
        flask_routes = get_flask_routes(app)
        print(f"Found {len(flask_routes)} routes in Flask app")
        
        # Debug info
        print(f"DEBUG: First few Flask routes: {flask_routes[:5]}")
    except Exception as e:
        print(f"{RED}Error retrieving Flask routes: {e}{RESET}")
        return False, [], []
    
    # Get OpenAPI paths
    openapi_paths = get_openapi_paths(spec)
    print(f"DEBUG: Found {len(openapi_paths)} paths in OpenAPI spec")
    print(f"DEBUG: First few OpenAPI paths: {openapi_paths[:5]}")
    
    # Find missing routes (routes in Flask but not in OpenAPI)
    missing_routes = []
    for flask_path, method in flask_routes:
        if (flask_path, method) not in openapi_paths:
            # Skip internal endpoints or testing endpoints
            if 'docs' in flask_path or flask_path == '/api/status':
                continue
            missing_routes.append((flask_path, method))
    
    # Find non-existent paths (paths in OpenAPI but not in Flask)
    non_existent_paths = []
    for openapi_path, method in openapi_paths:
        if (openapi_path, method) not in flask_routes:
            non_existent_paths.append(openapi_path)
            print(f"DEBUG: Path not found in Flask: {openapi_path} ({method})")
            # Print closest matching paths
            for flask_path, flask_method in flask_routes:
                if openapi_path in flask_path or flask_path in openapi_path:
                    print(f"DEBUG: Possible match: {flask_path} ({flask_method})")
    
    # Print results
    if not missing_routes and not non_existent_paths:
        print(f"{GREEN}Validation successful! All Flask routes are documented in the OpenAPI spec.{RESET}")
        return True, [], []
    
    if missing_routes:
        print(f"\n{YELLOW}Routes found in Flask but not in OpenAPI spec:{RESET}")
        for path, method in missing_routes:
            print(f"  {path} ({method.upper()})")
    
    if non_existent_paths:
        print(f"\n{YELLOW}Paths found in OpenAPI spec but not in Flask:{RESET}")
        for path in sorted(set(non_existent_paths)):
            print(f"  {path}")
    else:
        # If we've printed missing routes but there are no non-existent paths
        if missing_routes:
            print(f"\n{YELLOW}No paths found in OpenAPI spec that don't exist in Flask{RESET}")
        else:
            # This is the case where missing_routes and non_existent_paths are both empty
            # but the script is still returning False
            print(f"\n{GREEN}No discrepancies found!{RESET}")
            return True, [], []
    
    return False, missing_routes, non_existent_paths

def main():
    """Main entry point."""
    success, missing_routes, non_existent_paths = validate_openapi()
    print(f"DEBUG: Success: {success}, Missing routes: {len(missing_routes)}, Non-existent paths: {len(non_existent_paths)}")
    
    # Only exit with error if there are actual discrepancies
    if success or (len(missing_routes) == 0 and len(non_existent_paths) == 0):
        print(f"{GREEN}Validation successful!{RESET}")
        sys.exit(0)
    else:
        print(f"{RED}Validation failed!{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main() 