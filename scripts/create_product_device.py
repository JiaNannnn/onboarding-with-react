#!/usr/bin/env python
"""
EnOS Product Creation Tool

This script provides a client for creating products and devices in the EnOS platform 
using the Connection Service API and the poseidon library for authentication.
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
logger = logging.getLogger('enos_product_device')

class EnOSConnectionClient:
    """
    Client for interacting with the EnOS Connection Service API
    
    This class provides methods for creating products and devices in EnOS
    using the poseidon library for authentication.
    """
    
    def __init__(self, apigw_url: str, app_key: str, app_secret: str, org_id: str):
        """
        Initialize the EnOS Connection Client
        
        Args:
            apigw_url: API Gateway URL
            app_key: Application access key
            app_secret: Application secret key 
            org_id: Organization ID
        """
        self.apigw_url = apigw_url.rstrip('/')
        self.app_key = app_key
        self.app_secret = app_secret
        self.org_id = org_id
        
    def create_product(self, product_name: str, model_id: str, 
                      product_type: str = "Device", data_format: str = "Json",
                      product_desc: str = None, tags: dict = None) -> str:
        """
        Create a product in EnOS
        
        Args:
            product_name: Product name
            model_id: Model ID
            product_type: Product type (default: Device)
            data_format: Data format (default: Json)
            product_desc: Product description (optional)
            tags: Product tags (optional)
            
        Returns:
            Product key if successful, None otherwise
        """
        # Prepare API URL
        url = f"{self.apigw_url}/connect-service/v2.1/products?action=create&orgId={self.org_id}"
        
        # Prepare product name with i18n structure
        name_data = {
            "defaultValue": product_name,
            "i18nValue": {}
        }
        
        # Build request data
        data = {
            "biDirectionalAuth": False,
            "modelId": model_id,
            "productName": name_data,
            "dataFormat": data_format,
            "productType": product_type
        }
        
        # Add optional fields if provided
        if product_desc:
            data["productDesc"] = {
                "defaultValue": product_desc,
                "i18nValue": {}
            }
            
        if tags:
            data["productTags"] = tags
            
        try:
            # Make API call
            logger.info(f"Creating product: {product_name} with model ID: {model_id}")
            response = poseidon.urlopen(
                self.app_key, 
                self.app_secret, 
                url, 
                data,
                method="POST"
            )
            
            # Parse response
            if hasattr(response, 'status_code') and response.status_code != 200:
                logger.error(f"Failed to create product. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
            response_data = response if isinstance(response, dict) else response.json()
            
            # Check for success
            if response_data.get("code") == 0:
                product_key = response_data.get("data", {}).get("productKey")
                logger.info(f"Successfully created product with key: {product_key}")
                return product_key
            else:
                error_msg = response_data.get("msg", "Unknown error")
                logger.error(f"Failed to create product: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"Exception during product creation: {str(e)}")
            return None
            
    def create_device(self, product_key: str, device_name: str, 
                     device_desc: str = None, tags: dict = None) -> dict:
        """
        Create a device in EnOS
        
        Args:
            product_key: Product key
            device_name: Device name
            device_desc: Device description (optional)
            tags: Device tags (optional)
            
        Returns:
            Device information dictionary if successful, None otherwise
        """
        # Prepare API URL
        url = f"{self.apigw_url}/connect-service/v2.1/devices?action=create&orgId={self.org_id}"
        
        # Prepare device name with i18n structure
        name_data = {
            "defaultValue": device_name,
            "i18nValue": {}
        }
        
        # Build request data
        data = {
            "productKey": product_key,
            "deviceName": name_data,
            "timezone": "+00:00"
        }
        
        # Add optional fields if provided
        if device_desc:
            data["deviceDesc"] = device_desc
            
        if tags:
            data["deviceTags"] = tags
            
        try:
            # Make API call
            logger.info(f"Creating device: {device_name} under product: {product_key}")
            response = poseidon.urlopen(
                self.app_key, 
                self.app_secret, 
                url, 
                data,
                method="POST"
            )
            
            # Parse response
            if hasattr(response, 'status_code') and response.status_code != 200:
                logger.error(f"Failed to create device. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
            response_data = response if isinstance(response, dict) else response.json()
            
            # Check for success
            if response_data.get("code") == 0:
                device_info = response_data.get("data", {})
                logger.info(f"Successfully created device with key: {device_info.get('deviceKey')}")
                return device_info
            else:
                error_msg = response_data.get("msg", "Unknown error")
                logger.error(f"Failed to create device: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"Exception during device creation: {str(e)}")
            return None
            
    def get_device_info(self, device_key: str) -> dict:
        """
        Get device information from EnOS
        
        Args:
            device_key: Device key
            
        Returns:
            Device information dictionary if successful, None otherwise
        """
        # Prepare API URL
        url = f"{self.apigw_url}/connect-service/v2.1/devices?action=get&orgId={self.org_id}&deviceKey={device_key}"
        
        try:
            # Make API call
            logger.info(f"Getting device information for: {device_key}")
            response = poseidon.urlopen(
                self.app_key, 
                self.app_secret, 
                url,
                method="GET"
            )
            
            # Parse response
            if hasattr(response, 'status_code') and response.status_code != 200:
                logger.error(f"Failed to get device info. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
            response_data = response if isinstance(response, dict) else response.json()
            
            # Check for success
            if response_data.get("code") == 0:
                device_info = response_data.get("data", {})
                logger.info(f"Successfully retrieved device information")
                return device_info
            else:
                error_msg = response_data.get("msg", "Unknown error")
                logger.error(f"Failed to get device information: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"Exception during device info retrieval: {str(e)}")
            return None

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Create EnOS products and devices')
    parser.add_argument('--apigw-url', default="https://apim-ppe1.envisioniot.com", help='API Gateway URL')
    parser.add_argument('--model-id', required=True, help='Model ID for the product')
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
    
    try:
        # Initialize client
        client = EnOSConnectionClient(
            apigw_url=args.apigw_url,
            app_key=app_key,
            app_secret=app_secret,
            org_id=org_id
        )
        
        # Create product
        product_name = f"{args.model_id}_Product"
        print(f"Creating product: {product_name}...")
        product_key = client.create_product(
            product_name=product_name,
            model_id=args.model_id
        )
        
        if not product_key:
            print("Failed to create product. See log for details.")
            return 1
            
        # Prepare result
        result = {
            "product": {
                "key": product_key,
                "name": product_name,
                "model_id": args.model_id
            }
        }
        
        # Save to file
        output_file = f"{args.model_id}_product.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
            
        print(f"Product created successfully with key: {product_key}")
        print(f"Saved product information to {output_file}")
        return 0
            
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.debug:
            import traceback
            logger.debug("Detailed error information:")
            logger.debug(traceback.format_exc())
        return 1
        
if __name__ == '__main__':
    sys.exit(main())