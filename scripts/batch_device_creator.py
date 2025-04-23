#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
EnOS Batch Device Creator

This script creates multiple devices in batch for an existing product on the EnOS platform.
It uses the poseidon library to make API calls to the EnOS Connection Service.

The script creates the specified number of devices and saves the details to a JSON file,
which includes the device keys and secrets (if requested).
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

try:
    import poseidon
except ImportError:
    print("Error: Required package 'poseidon' not found. Please install it.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("batch_device_creator")


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Create devices in batch for an EnOS product")
    
    # Required arguments
    parser.add_argument("--apigw-url", type=str, required=False, help="EnOS API Gateway URL")
    parser.add_argument("--org-id", type=str, required=False, help="Organization ID")
    parser.add_argument("--ak", type=str, required=False, help="Access Key")
    parser.add_argument("--sk", type=str, required=False, help="Secret Key")
    parser.add_argument("--product-key", type=str, required=True, help="Product Key for device creation")
    
    # Optional arguments
    parser.add_argument("--device-count", type=int, default=10, help="Number of devices to create (default: 10)")
    parser.add_argument("--name-prefix", type=str, default="Device", help="Prefix for device names (default: 'Device')")
    parser.add_argument("--model-id", type=str, help="Model ID (optional)")
    parser.add_argument("--timezone", type=str, default="+08:00", help="Timezone for devices (default: +08:00)")
    parser.add_argument("--require-secret", action="store_true", help="Require device secret")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--output-file", type=str, help="Custom output file path")
    
    args = parser.parse_args()
    
    # Check for environment variables if arguments not provided
    if not args.apigw_url:
        args.apigw_url = os.environ.get("ENOS_APIGW_URL")
    if not args.org_id:
        args.org_id = os.environ.get("ENOS_ORG_ID")
    if not args.ak:
        args.ak = os.environ.get("ENOS_AK")
    if not args.sk:
        args.sk = os.environ.get("ENOS_SK")
    
    # Validate required arguments
    missing_args = []
    if not args.apigw_url:
        missing_args.append("--apigw-url")
    if not args.org_id:
        missing_args.append("--org-id")
    if not args.ak:
        missing_args.append("--ak")
    if not args.sk:
        missing_args.append("--sk")
    
    if missing_args:
        parser.error(f"Missing required arguments: {', '.join(missing_args)}")
    
    return args


def setup_environment(args: argparse.Namespace) -> Tuple[Dict[str, str], str]:
    """
    Set up the environment for API calls.
    
    Args:
        args: Command line arguments
        
    Returns:
        Tuple[Dict[str, str], str]: API headers and output file path
    """
    # Set log level
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Generate output file path if not specified
    output_file = args.output_file
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = f"batch_devices_{args.product_key}_{timestamp}.json"
    
    # Prepare API headers
    headers = {
        "Content-Type": "application/json",
        "apim-accesskey": args.ak,
        "apim-signature-method": "sha1",
        "apim-signature-nonce": str(int(time.time() * 1000)),
        "apim-signature-version": "1.0",
        "apim-timestamp": str(int(time.time() * 1000)),
        "Accept": "application/json"
    }
    
    # Log execution settings
    logger.info(f"Starting batch device creation for product: {args.product_key}")
    logger.info(f"Creating {args.device_count} devices with prefix: {args.name_prefix}")
    logger.info(f"Output will be saved to: {output_file}")
    
    return headers, output_file


def create_devices(args: argparse.Namespace, headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Create devices in batch using the EnOS Connection Service API.
    
    Args:
        args: Command line arguments
        headers: API request headers
        
    Returns:
        Dict[str, Any]: API response data
    """
    logger.info("Preparing device creation payload...")
    
    # API endpoint for batch device creation
    api_url = f"{args.apigw_url}/connect-service/v2.1/device/createDeviceWithKey"
    
    # Prepare device list
    devices = []
    for i in range(1, args.device_count + 1):
        device_name = f"{args.name_prefix}_{i}"
        device = {
            "productKey": args.product_key,
            "deviceName": device_name,
            "timezone": args.timezone
        }
        
        if args.model_id:
            device["modelId"] = args.model_id
            
        devices.append(device)
    
    # Prepare request payload
    payload = {
        "orgId": args.org_id,
        "createDeviceWithKeyList": devices,
        "requiresSecret": args.require_secret
    }
    
    logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
    
    # Make API call using poseidon
    logger.info(f"Calling API to create {len(devices)} devices...")
    response_raw = poseidon.urlopen(
        url=api_url,
        data=json.dumps(payload),
        headers=headers,
        method="POST"
    )
    
    # Parse and validate response
    response = json.loads(response_raw)
    logger.debug(f"API response: {json.dumps(response, indent=2)}")
    
    if "code" in response and response["code"] == 0:
        success_count = len(response.get("data", {}).get("successList", []))
        failed_count = len(response.get("data", {}).get("failedList", []))
        logger.info(f"Device creation completed: {success_count} succeeded, {failed_count} failed")
    else:
        error_msg = response.get("msg", "Unknown error")
        error_code = response.get("code", "Unknown code")
        logger.error(f"API request failed: {error_msg} (Code: {error_code})")
    
    return response


def save_output(data: Dict[str, Any], output_file: str, args: argparse.Namespace) -> None:
    """
    Save API response to a JSON file.
    
    Args:
        data: API response data
        output_file: Output file path
        args: Command line arguments
    """
    # Add metadata to the output
    output_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "product_key": args.product_key,
            "device_count": args.device_count,
            "name_prefix": args.name_prefix,
            "require_secret": args.require_secret
        },
        "api_response": data
    }
    
    # Create summary section
    success_list = data.get("data", {}).get("successList", [])
    failed_list = data.get("data", {}).get("failedList", [])
    
    output_data["summary"] = {
        "total_requested": args.device_count,
        "total_succeeded": len(success_list),
        "total_failed": len(failed_list)
    }
    
    # Write to file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Device creation details saved to: {output_file}")
    except Exception as e:
        logger.error(f"Failed to save output file: {e}")


def main() -> None:
    """Main function to execute the batch device creation process."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Setup environment
        headers, output_file = setup_environment(args)
        
        # Create devices
        response = create_devices(args, headers)
        
        # Save output
        save_output(response, output_file, args)
        
        # Exit with appropriate status code
        if response.get("code") == 0:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 