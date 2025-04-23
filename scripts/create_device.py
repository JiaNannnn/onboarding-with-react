#!/usr/bin/env python
"""
EnOS Batch Device Creation Script

This script uses the EnOS Connection Service API to create multiple devices in a batch.
It implements authentication via the poseidon library.
"""
import json
import sys
import argparse
import logging
from poseidon import poseidon

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('enos_batch_device')

def create_batch_devices(apigw_url, app_key, app_secret, org_id, product_key, device_count, require_secret=False):
    """
    Create multiple devices in a batch
    
    Args:
        apigw_url: API Gateway URL
        app_key: Application access key
        app_secret: Application secret key
        org_id: Organization ID
        product_key: Product key under which to create devices
        device_count: Number of devices to create
        require_secret: Whether to return device secrets (requires RSA key pair)
    
    Returns:
        Response from the API
    """
    # Prepare API URL with organization ID
    url = f"{apigw_url}/connect-service/v2.4/devices?action=batchCreate&orgId={org_id}"
    
    # Prepare device list
    device_list = []
    for i in range(1, device_count + 1):
        device = {
            "productKey": product_key,
            "deviceName": {
                "defaultValue": f"Device_{i}",
                "i18nValue": {
                    "en_US": f"Device_{i}",
                    "zh_CN": f"设备_{i}"
                }
            },
            "timezone": "+08:00",
            "deviceDesc": f"Automatically created device {i}",
            "deviceTags": {
                "batch": "auto_created",
                "index": str(i)
            }
        }
        device_list.append(device)
    
    # Prepare request payload
    payload = {
        "deviceList": device_list,
        "requireSecret": require_secret
    }
    
    # Convert payload to JSON string for poseidon
    payload_str = json.dumps(payload)
    logger.info(f"Creating {device_count} devices under product '{product_key}'")
    
    try:
        # Use poseidon library for authenticated API call
        response = poseidon.urlopen(
            url, 
            payload_str, 
            app_key, 
            app_secret,
            method="POST", 
            content_type="application/json"
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to create devices. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
        
        response_json = response.json()
        return response_json
    
    except Exception as e:
        logger.error(f"Exception during batch device creation: {str(e)}")
        return None

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Create multiple EnOS devices in a batch')
    parser.add_argument('--apigw-url', default="https://apim-ppe1.envisioniot.com", help='API Gateway URL')
    parser.add_argument('--device-count', type=int, default=5, help='Number of devices to create')
    parser.add_argument('--require-secret', action='store_true', help='Return device secrets (requires RSA key pair)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Configure debug logging if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
            
    # Use fixed credentials for simplicity
    app_key = "e853e8a2-b446-4f53-9ed8-5a5e878c29e9"
    app_secret = "45502fef-857c-4838-b223-1703920c7c48" 
    org_id = "o15520323695671"
    
    # Output filename
    output_file = f"batch_devices_EJxxnMdi.json"
    
    try:
        # Create the devices
        print(f"Creating {args.device_count} devices under product 'EJxxnMdi'...")
        response = create_batch_devices(
            args.apigw_url,
            app_key,
            app_secret,
            org_id,
            "EJxxnMdi",
            args.device_count,
            args.require_secret
        )
        
        if not response:
            print("Failed to create devices. See log for details.")
            return 1
        
        if response.get("code") == 0:  # Success status
            success_count = response.get("successSize", 0)
            total_count = response.get("totalSize", 0)
            
            print(f"\nResult summary:")
            print(f"Successfully created {success_count} out of {total_count} devices")
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(response, f, indent=2)
            print(f"Saved device information to {output_file}")
            
            # Extract device keys
            if success_count > 0:
                print("\nDevice Keys:")
                for i, item in enumerate(response.get("data", [])):
                    if item.get("code") == 0:
                        device_key = item.get("data", {}).get("deviceKey")
                        if device_key:
                            print(f"  Device {i+1}: {device_key}")
            
            return 0
        else:
            error_msg = response.get("msg", "Unknown error")
            print(f"Failed to create devices: {error_msg}")
            return 1
            
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.debug:
            import traceback
            logger.debug("Detailed error information:")
            logger.debug(traceback.format_exc())
        return 1
        
if __name__ == '__main__':
    sys.exit(main())