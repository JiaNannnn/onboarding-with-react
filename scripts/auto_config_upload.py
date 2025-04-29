#!/usr/bin/env python
"""
Auto Config Upload Script

This script reads point mappings from a CSV file and calls the autoConfigV2 API 
to configure the BMS points in the EnOS platform.
"""
import argparse
import csv
import json
import logging
import os
import sys
from typing import Dict, List, Any, Optional
import requests
from pathlib import Path
from poseidon import poseidon

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('auto_config_upload')

# Default API endpoint - will be configurable
DEFAULT_API_ENDPOINT = "https://apim-ppe1.envisioniot.com/enos-edge/v2.4/discovery/autoConfigV2"

class AutoConfigUploader:
    """
    Class to handle uploading point mappings to the autoConfigV2 API
    """
    def __init__(self, 
                 api_url: str, 
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 org_id: Optional[str] = None,
                 protocol: str = "bacnet"):
        """
        Initialize the uploader with API credentials and configuration
        
        Args:
            api_url: The URL for the autoConfigV2 API endpoint
            access_key: Access key for API authentication (optional)
            secret_key: Secret key for API authentication (optional)
            org_id: Organization ID for API calls (optional)
            protocol: The protocol to use (default: "bacnet")
        """
        self.api_url = api_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.org_id = org_id
        self.protocol = protocol
        self.headers = self._build_headers()
        
    def _build_headers(self) -> Dict[str, str]:
        """Build the HTTP headers for API requests"""
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add authentication headers if provided
        if self.access_key:
            headers["AccessKey"] = self.access_key
            headers["x-access-key"] = self.access_key
        if self.secret_key:
            headers["SecretKey"] = self.secret_key
            headers["x-secret-key"] = self.secret_key
            
        return headers
    
    def read_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Read point mappings from a CSV file
        
        Args:
            csv_path: Path to the CSV file containing point mappings
            
        Returns:
            List of dictionaries containing point mapping data
        """
        point_mappings = []
        
        logger.info(f"Reading point mappings from {csv_path}")
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Clean and validate row data
                    if not row.get('deviceAssetId') or not row.get('modelId'):
                        logger.warning(f"Skipping row with missing required fields: {row}")
                        continue
                    
                    # Convert numeric fields
                    if 'otDeviceInst' in row and row['otDeviceInst']:
                        try:
                            row['otDeviceInst'] = int(row['otDeviceInst'])
                        except ValueError:
                            logger.warning(f"Invalid otDeviceInst value: {row['otDeviceInst']}")
                            continue
                    
                    if 'baseValue' in row and row['baseValue']:
                        try:
                            row['baseValue'] = str(float(row['baseValue']))
                        except ValueError:
                            # Keep as string if not a valid number
                            pass
                    
                    if 'coefficient' in row and row['coefficient']:
                        try:
                            row['coefficient'] = str(float(row['coefficient']))
                        except ValueError:
                            # Keep as string if not a valid number
                            pass
                    
                    if 'interval' in row and row['interval']:
                        try:
                            row['interval'] = int(row['interval'])
                        except ValueError:
                            logger.warning(f"Invalid interval value: {row['interval']}")
                    
                    if 'controlPriority' in row and row['controlPriority']:
                        try:
                            row['controlPriority'] = int(row['controlPriority'])
                        except ValueError:
                            logger.warning(f"Invalid controlPriority value: {row['controlPriority']}")
                    
                    if 'uploadInterval' in row and row['uploadInterval']:
                        try:
                            row['uploadInterval'] = int(row['uploadInterval'])
                        except ValueError:
                            logger.warning(f"Invalid uploadInterval value: {row['uploadInterval']}")
                    
                    point_mappings.append(row)
        
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_path}")
            raise
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise
        
        logger.info(f"Successfully read {len(point_mappings)} point mappings")
        return point_mappings
    
    def group_by_asset(self, point_mappings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group point mappings by Edge gateway asset ID
        
        Args:
            point_mappings: List of point mapping dictionaries
            
        Returns:
            Dictionary with asset IDs as keys and lists of point mappings as values
        """
        grouped_mappings = {}
        
        for mapping in point_mappings:
            # Use a default asset ID if not specified in the mapping
            asset_id = mapping.get('edgeAssetId', 'default_asset')
            
            if asset_id not in grouped_mappings:
                grouped_mappings[asset_id] = []
                
            grouped_mappings[asset_id].append(mapping)
        
        return grouped_mappings
    
    def build_request_payload(self, grouped_mappings: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Build the JSON payload for the autoConfigV2 API request
        
        Args:
            grouped_mappings: Dictionary with asset IDs as keys and lists of point mappings as values
            
        Returns:
            Dictionary containing the complete API request payload
        """
        configs = []
        
        for asset_id, mappings in grouped_mappings.items():
            config = {
                "assetId": asset_id,
                "pointMappings": mappings
            }
            configs.append(config)
        
        payload = {
            "configs": configs,
            "protocol": self.protocol
        }
        
        if self.org_id:
            payload["orgId"] = self.org_id
        
        return payload
    
    def upload_config(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload the configuration to the autoConfigV2 API
        
        Args:
            payload: Dictionary containing the API request payload
            
        Returns:
            Dictionary containing the API response
        """
        logger.info(f"Uploading configuration to {self.api_url}")
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60  # Set a reasonable timeout
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            result = response.json()
            logger.info(f"API request successful: {result.get('msg', 'No message')}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Error response: {error_detail}")
                except ValueError:
                    logger.error(f"Error response text: {e.response.text}")
            raise
    
    def process_csv_file(self, csv_path: str) -> Dict[str, Any]:
        """
        Process a CSV file and upload the point mappings to the autoConfigV2 API
        
        Args:
            csv_path: Path to the CSV file containing point mappings
            
        Returns:
            Dictionary containing the API response
        """
        # Read point mappings from CSV
        point_mappings = self.read_csv(csv_path)
        
        if not point_mappings:
            logger.warning("No valid point mappings found in CSV file")
            return {"success": False, "error": "No valid point mappings found"}
        
        # Group mappings by asset ID
        grouped_mappings = self.group_by_asset(point_mappings)
        
        # Build request payload
        payload = self.build_request_payload(grouped_mappings)
        
        # Save payload to file for debugging
        debug_file = Path(csv_path).with_suffix('.json')
        with open(debug_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)
        logger.info(f"Saved request payload to {debug_file}")
        
        # Upload configuration
        result = self.upload_config(payload)
        
        return result

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Upload BMS point mappings from CSV to autoConfigV2 API')
    parser.add_argument('csv_path', help='Path to the CSV file containing point mappings')
    parser.add_argument('--api-url', default=DEFAULT_API_ENDPOINT, help='URL for the autoConfigV2 API endpoint')
    #parser.add_argument('--access-key', help='Access key for API authentication')
    #parser.add_argument('--secret-key', help='Secret key for API authentication')
    #parser.add_argument('--org-id', help='Organization ID for API calls')
    parser.add_argument('--protocol', default='bacnet', help='Protocol to use (default: bacnet)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Configure debug logging if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
    
    # Create uploader
    uploader = AutoConfigUploader(
        api_url=args.api_url,
        access_key="e853e8a2-b446-4f53-9ed8-5a5e878c29e9",
        secret_key="45502fef-857c-4838-b223-1703920c7c48",
        org_id="o15520323695671",
        protocol=args.protocol
    )
    
    # Process CSV file
    try:
        result = uploader.process_csv_file(args.csv_path)
        
        # Print result
        print(json.dumps(result, indent=2))
        
        # Return appropriate exit code
        if result.get('success', False) or result.get('code', 1) == 0:
            return 0
        else:
            return 1
            
    except Exception as e:
        logger.error(f"Error processing CSV file: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 