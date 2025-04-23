#!/usr/bin/env python
"""
Example script for creating an HVAC product and devices in EnOS

This script demonstrates how to use the EnOSConnectionClient to create
a product for HVAC devices and then create multiple devices under it.
"""
import json
import os
import sys
import logging
# Make sure script can be run from the scripts directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.create_product_device import EnOSConnectionClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('enos_product_device')

# Set these values according to your environment
APIGW_URL = "https://apim-ppe1.envisioniot.com"
APP_KEY = "e853e8a2-b446-4f53-9ed8-5a5e878c29e9"  # Replace with your actual app key
APP_SECRET = "45502fef-857c-4838-b223-1703920c7c48"  # Replace with your actual app secret
ORG_ID = "o15520323695671"  # Replace with your actual org ID
MODEL_ID = "EnOS_HVAC_AHU"  # Replace with your actual model ID

# HVAC product configuration
PRODUCT_CONFIG = {
    "name": "HVAC_AHU_Product",
    "desc": "Air Handling Units for HVAC System",
    "type": "Device",
    "data_format": "Json",
    "tags": {
        "category": "HVAC",
        "subcategory": "AHU",
        "version": "1.0"
    }
}

# Device configurations
DEVICES = [
    {
        "name": "AHU_Floor1_Zone1",
        "desc": "Air Handling Unit for Floor 1, Zone 1",
        "tags": {
            "location": "Floor1",
            "zone": "Zone1"
        }
    },
    {
        "name": "AHU_Floor1_Zone2",
        "desc": "Air Handling Unit for Floor 1, Zone 2",
        "tags": {
            "location": "Floor1",
            "zone": "Zone2"
        }
    },
    {
        "name": "AHU_Floor2_Zone1",
        "desc": "Air Handling Unit for Floor 2, Zone 1",
        "tags": {
            "location": "Floor2",
            "zone": "Zone1"
        }
    }
]

def main():
    """Create HVAC product and devices"""
    try:
        # Initialize the EnOS client
        client = EnOSConnectionClient(
            apigw_url=APIGW_URL,
            app_key=APP_KEY,
            app_secret=APP_SECRET,
            org_id=ORG_ID
        )
        
        print(f"Creating product: {PRODUCT_CONFIG['name']}")
        
        # Create the product
        product_key = client.create_product(
            product_name=PRODUCT_CONFIG["name"],
            model_id=MODEL_ID,
            product_type=PRODUCT_CONFIG["type"],
            data_format=PRODUCT_CONFIG["data_format"],
            product_desc=PRODUCT_CONFIG["desc"],
            tags=PRODUCT_CONFIG["tags"]
        )
        
        print(f"Successfully created product with key: {product_key}")
        
        # Create devices under the product
        devices = []
        for device_config in DEVICES:
            print(f"Creating device: {device_config['name']}")
            
            device_info = client.create_device(
                product_key=product_key,
                device_name=device_config["name"],
                device_desc=device_config["desc"],
                tags=device_config.get("tags")
            )
            
            devices.append(device_info)
        
        # Prepare result
        result = {
            "product": {
                "key": product_key,
                "name": PRODUCT_CONFIG["name"],
                "model_id": MODEL_ID
            },
            "devices": devices
        }
        
        # Save result to file
        output_file = "hvac_product_devices.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        print(f"Saved product and device information to {output_file}")
        print(f"Created {len(devices)} devices under product {PRODUCT_CONFIG['name']}")
        
        # Also print device credentials for reference
        print("\nDevice Credentials:")
        print("-" * 80)
        print(f"{'Device Name':<30} {'Device Key':<20} {'Device Secret':<40}")
        print("-" * 80)
        for device in devices:
            print(f"{device.get('deviceName', {}).get('defaultValue', 'N/A'):<30} "
                  f"{device.get('deviceKey', 'N/A'):<20} "
                  f"{device.get('deviceSecret', 'N/A'):<40}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 