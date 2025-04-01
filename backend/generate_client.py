#!/usr/bin/env python
"""
OpenAPI Client Generator

This script generates TypeScript client code from the OpenAPI specification
to ensure frontend code is using the correct API endpoints.

Requirements:
- openapi-generator-cli (can be installed with npm)
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def check_openapi_generator():
    """Check if openapi-generator-cli is installed."""
    try:
        result = subprocess.run(
            ["npx", "openapi-generator-cli", "version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"{YELLOW}openapi-generator-cli is not installed. Installing...{RESET}")
            install_result = subprocess.run(
                ["npm", "install", "@openapitools/openapi-generator-cli", "-g"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if install_result.returncode != 0:
                print(f"{RED}Failed to install openapi-generator-cli:{RESET}")
                print(install_result.stderr)
                return False
            
            print(f"{GREEN}openapi-generator-cli installed successfully.{RESET}")
        
        return True
    
    except Exception as e:
        print(f"{RED}Error checking for openapi-generator-cli: {e}{RESET}")
        return False

def generate_typescript_client(swagger_path, output_dir):
    """Generate TypeScript client from OpenAPI spec."""
    print(f"Generating TypeScript client from {swagger_path}")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Configure the generator
    config = {
        "npmName": "bms-api-client",
        "npmVersion": "1.0.0",
        "supportsES6": "true",
        "modelPropertyNaming": "camelCase",
        "withInterfaces": "true",
    }
    
    config_args = []
    for key, value in config.items():
        config_args.extend(["--additional-properties", f"{key}={value}"])
    
    # Run generator
    try:
        result = subprocess.run(
            [
                "npx", "openapi-generator-cli", "generate",
                "-i", str(swagger_path),
                "-g", "typescript-fetch",
                "-o", str(output_dir),
                *config_args
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        print(f"{GREEN}Successfully generated TypeScript client:{RESET}")
        print(f"Output directory: {output_dir}")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"{RED}Error generating TypeScript client:{RESET}")
        print(e.stderr)
        return False

def create_documentation(output_dir):
    """Create README.md file with usage instructions."""
    readme_path = Path(output_dir) / "README.md"
    
    readme_content = """# BMS API Client

This is an auto-generated API client for the BMS API. It provides type-safe access to all API endpoints.

## Installation

```bash
npm install --save ./bms-api-client
```

## Usage

```typescript
import { Configuration, DefaultApi } from 'bms-api-client';

// Create a new API client
const config = new Configuration({
  basePath: 'http://localhost:5000',
});

const api = new DefaultApi(config);

// Example: Get networks
api.getNetworks({
  apiGateway: 'https://ag-eu2.envisioniot.com',
  accessKey: 'your-access-key',
  secretKey: 'your-secret-key',
  orgId: 'your-org-id',
  assetId: 'your-asset-id'
})
.then(response => {
  console.log('Networks:', response.data);
})
.catch(error => {
  console.error('Error:', error);
});

// Example: Fetch points
api.searchPoints({
  apiGateway: 'https://ag-eu2.envisioniot.com',
  accessKey: 'your-access-key',
  secretKey: 'your-secret-key',
  orgId: 'your-org-id',
  assetId: 'your-asset-id',
  deviceInstances: ['12345', '67890']
})
.then(response => {
  console.log('Task ID:', response.taskId);
  console.log('Status:', response.status);
})
.catch(error => {
  console.error('Error:', error);
});
```

## Endpoints

The client includes methods for all API endpoints defined in the OpenAPI specification.
Refer to the type definitions for full documentation of parameters and return types.

## Types

All request and response types are fully typed for better IDE support and type safety.
"""
    
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print(f"{GREEN}Created README.md with usage instructions.{RESET}")
    return True

def main():
    """Main entry point."""
    # Get the base directory
    base_dir = Path(__file__).parent
    
    # Set paths
    swagger_path = base_dir / 'app' / 'api' / 'swagger.yaml'
    output_dir = base_dir / 'client'
    
    # Check if swagger.yaml exists
    if not swagger_path.exists():
        print(f"{RED}Error: {swagger_path} does not exist.{RESET}")
        return 1
    
    # Check for openapi-generator-cli
    if not check_openapi_generator():
        return 1
    
    # Remove existing output directory if it exists
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    # Generate TypeScript client
    if not generate_typescript_client(swagger_path, output_dir):
        return 1
    
    # Create documentation
    if not create_documentation(output_dir):
        return 1
    
    print(f"\n{GREEN}✓ Client generation completed successfully!{RESET}")
    print(f"You can now use the generated client code from {output_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 