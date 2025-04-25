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
from poseidon import poseidon

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("batch_device_creator")

# Device attribute schemas for different device types
DEVICE_ATTRIBUTE_SCHEMAS = {
    'AHU': {
        'AHU_supply_air_fan_norminal_power': 1,
        'AHU_static_pressure_design': '',
        'AHU_operation_mode_mapping': {
            'ventilation': 2,
            'cooling': 0,
            'heating': 1
        },
        'AHU_static_pressure_initial': '',
        'AHU_static_pressure_baseline': '',
        'AHU_design_air_flow': '',
        'AHU_return_air_temp_baseline': '',
        'AHU_supply_air_temp_baseline': '',
        'EQUIP_equip_type': '31: AHU',
        'Equipment Type': '31: AHU',
        'Attribute Point Identifier': '',
        'Attribute Point Name': '',
        'Description': '',
        'Data Type': '',
        'Unit': '',
        'Input Value': '',
        'Comment': ''
    },
    'CHPL': {
        '_EnOS_HVAC_CHPL': '',
        'Device Asset': '',
        'Equipment Type': '11: CHPL',
        'CHPL_building_type': '1: Office',
        'CHPL_location': '',
        'Attribute Point Identifier': '',
        'Attribute Point Name': '',
        'Description': '',
        'Data Type': '',
        'Unit': '',
        'Input Value': '',
        'Comment': '',
        'EQUIP_equip_type': '11: CHPL',
        'BCA_Platinum_Efficiency': 0.65,
        'CHPL_ct_type': '',
        'CHPL_power_vfd_chwp_total': 0.0,
        'CHPL_power_ct_total': 0.0,
        'CHPL_chiller_opt_method': '',
        'CHPL_ct_opt_method': '',
        'CHPL_ct_chiller_connection_type': '',
        'CHPL_temp_chws_baseline': 7.0,
        'CHPL_temp_cws_baseline': 28.0,
        'CHPL_delta_pressure_chw_baseline': 200.0,
        'CHPL_delta_temp_cw_baseline': 5.0,
        'CHPL_number_chiller': 1,
        'CHPL_number_chwp': 1,
        'CHPL_number_cwp': 1,
        'CHPL_number_ct': 1,
        'CHPL_design_chpl_power': 0.0,
        'CHPL_delta_pressure_chw_initial': 0.0
    },
    'CH': {
        'EQUIP_equip_type': '12: CH',
        'Equipment Type': '12: CH',
        'CH_chiller_designed_capacity': 1000.0,
        'CH_chiller_type': '',
        'CH_chiller_designed_power': 0.0,
        'CH_chiller_designed_CHWST': 0.0,
        'CH_chiller_designed_CWST': 0.0
    },
    'CHWP': {
        'EQUIP_equip_type': '13: CHWP',
        'Equipment Type': '13: CHWP',
        'Attribute Point Identifier': '',
        'Attribute Point Name': '',
        'Description': '',
        'Data Type': '',
        'Unit': '',
        'Input Value': '',
        'Comment': '',
        'PUMP_driver_type': ''
    },
    'CWP': {
        'EQUIP_equip_type': '14: CWP',
        'Equipment Type': '14: CWP',
        'Attribute Point Identifier': '',
        'Attribute Point Name': '',
        'Description': '',
        'Data Type': '',
        'Unit': '',
        'Input Value': '',
        'Comment': '',
        'PUMP_driver_type': ''
    },
    'CT': {
        'EQUIP_equip_type': '15: CT',
        'Equipment Type': '15: CT',
        'Attribute Point Identifier': '',
        'Attribute Point Name': '',
        'Description': '',
        'Data Type': '',
        'Unit': '',
        'Input Value': '',
        'Comment': '',
        'CT_number_fan': ''
    },
    'FAN': {
        'EQUIP_equip_type': '16: CT_FAN',
        'Equipment Type': '16: CT_FAN',
        'Attribute Point Identifier': '',
        'Attribute Point Name': '',
        'Description': '',
        'Data Type': '',
        'Unit': '',
        'Input Value': '',
        'Comment': '',
        'FAN_frequency_low_limit': 30.0,
        'FAN_frequency_high_limit': 45.0
    },
    'VAV': {
        'EQUIP_equip_type': '34: VAV',
        'Equipment Type': '34: VAV',
        'Attribute Point Identifier': '',
        'Attribute Point Name': '',
        'Description': '',
        'Data Type': '',
        'Unit': '',
        'Input Value': '',
        'Comment': '',
        'VAV_ahu_ref': ''
    },
    'PMT': {
        'EQUIP_equip_type': '1: PMT',
        'Equipment Type': '1: PMT',
        'Attribute Point Identifier': '',
        'Attribute Point Name': '',
        'Description': '',
        'Data Type': '',
        'Unit': '',
        'Input Value': '',
        'Comment': '',
        'PMT_system_measured': '',
        'PMT_equip_measured': ''
    },
    'IAQ': {
        'EQUIP_equip_type': '81: SS_IEQ',
        'Equipment Type': '81: SS_IEQ',
        'Attribute Point Identifier': '',
        'Attribute Point Name': '',
        'Description': '',
        'Data Type': '',
        'Unit': '',
        'Input Value': '',
        'Comment': ''
    },
    'FCU': {
        'EQUIP_equip_type': '33: FCU',
        'Equipment Type': '33: FCU',
        'Attribute Point Identifier': '',
        'Attribute Point Name': '',
        'Description': '',
        'Data Type': '',
        'Unit': '',
        'Input Value': '',
        'Comment': ''
    },
    'PAU': {
        'EQUIP_equip_type': '32: PAU',
        'Equipment Type': '32: PAU',
        'Attribute Point Identifier': '',
        'Attribute Point Name': '',
        'Description': '',
        'Data Type': '',
        'Unit': '',
        'Input Value': '',
        'Comment': ''
    }
}

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
    
    # API endpoint for batch device creation (v2.4)
    api_url = f"{args.apigw_url}/connect-service/v2.4/devices?action=batchCreate&orgId={args.org_id}"
    
    # Prepare device list
    devices = []
    for i in range(1, args.device_count + 1):
        device_name = f"{args.name_prefix}_{i}"
        
        # Create device name with i18n support as required by the API
        device_name_obj = {
            "defaultValue": device_name,
            "i18nValue": {
                "en_US": device_name
            }
        }
        
        # Create device object
        device = {
            "productKey": args.product_key,
            "deviceName": device_name_obj,
            "timezone": args.timezone
        }
        
        # Add optional device key if prefix is provided
        if args.device_key_prefix:
            device["deviceKey"] = f"{args.device_key_prefix}_{i}"
        
        # Add optional device description
        if args.device_desc:
            device["deviceDesc"] = args.device_desc
        
        # Add optional device attributes
        if args.device_attributes:
            device["deviceAttributes"] = args.device_attributes
        
        # Add device-specific attributes based on product key
        product_key_upper = args.product_key.upper()
        for device_type, schema in DEVICE_ATTRIBUTE_SCHEMAS.items():
            if device_type in product_key_upper:
                device.setdefault("deviceAttributes", {}).update(schema)
                logger.info(f"Added {device_type} specific attributes to device {device_name}")
        
        # Add optional device tags
        if args.device_tags:
            device["deviceTags"] = args.device_tags
            
        devices.append(device)
    
    # Prepare request payload according to v2.4 API
    payload = {
        "deviceList": devices,
        "requireSecret": args.require_secret
    }
    
    logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
    
    # Make API call using poseidon
    logger.info(f"Calling API to create {len(devices)} devices...")
    
    # Use hardcoded credentials directly instead of from args
    apigw_url = args.apigw_url
    app_key = args.ak
    app_secret = args.sk
    
    response_raw = poseidon.urlopen(app_key, app_secret, apigw_url, payload, headers, "POST")
    
    # Parse and validate response
    response = json.loads(response_raw)
    logger.debug(f"API response: {json.dumps(response, indent=2)}")
    
    if "code" in response and response["code"] == 0:
        success_count = response.get("successSize", 0)
        total_count = response.get("totalSize", 0)
        logger.info(f"Device creation completed: {success_count} succeeded, {total_count - success_count} failed")
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
    
    # Create summary section based on v2.4 API response format
    success_size = data.get("successSize", 0)
    total_size = data.get("totalSize", 0)
    
    output_data["summary"] = {
        "total_requested": args.device_count,
        "total_succeeded": success_size,
        "total_failed": total_size - success_size
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
        # Create an argparse.Namespace object directly with your desired values
        # This replaces command line argument parsing with direct assignment
        class Args:
            pass
        
        args = Args()
        
        # Set required parameters - REPLACE THESE WITH YOUR ACTUAL VALUES
        args.apigw_url = "https://apim-ppe1.envisioniot.com"  # Your API Gateway URL
        args.org_id = "your-org-id"  # Your organization ID
        args.ak = "e853e8a2-b446-4f53-9ed8-5a5e878c29e9"  # Your access key
        args.sk = "45502fef-857c-4838-b223-1703920c7c48"  # Your secret key
        args.product_key = "your-product-key"  # Your product key
        
        # Set optional parameters with defaults
        args.device_count = 10  # Number of devices to create
        args.name_prefix = "Device"  # Prefix for device names
        args.timezone = "+08:00"  # Timezone for devices
        args.require_secret = True  # Whether to require device secret
        args.debug = True  # Enable debug logging
        args.output_file = None  # Will use default generated filename
        
        # Additional device attributes
        args.device_key_prefix = "dev"  # Prefix for device keys
        args.device_desc = "Automatically created device"  # Device description
        args.device_attributes = {}  # Device attributes (empty dict)
        args.device_tags = {"location": "building1"}  # Device tags
        
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