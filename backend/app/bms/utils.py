import os
import json
import time
from datetime import datetime
import re
import traceback
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Import poseidon if available
try:
    from poseidon import poseidon
except ImportError:
    poseidon = None
    print("Warning: Poseidon library not found. Some functions may not work correctly.")

class EnOSClient:
    """EnOS API client for fetching BMS points"""
    
    def __init__(self, api_url=None, access_key=None, secret_key=None, org_id=None):
        """Initialize EnOS client with API credentials"""
        from flask import current_app
        
        # All parameters should be explicitly provided or taken from environment variables
        # without hardcoded defaults
        self.api_url = api_url or os.environ.get("ENOS_API_URL")
        self.access_key = access_key or os.environ.get("ENOS_ACCESS_KEY")
        self.secret_key = secret_key or os.environ.get("ENOS_SECRET_KEY")
        self.org_id = org_id or os.environ.get("ENOS_ORG_ID")
        
        # Log warning if any parameter is missing
        if not self.api_url or not self.access_key or not self.secret_key or not self.org_id:
            current_app.logger.warning("Missing EnOS API credentials in EnOSClient initialization")
        
        # Create results directory
        self.results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
        os.makedirs(self.results_dir, exist_ok=True)
    
    def search_points(self, asset_id: str, device_instances: List[int], protocol: str = 'bacnet') -> Dict:
        """Initiate the BMS points search process"""
        url = f"{self.api_url}/enos-edge/v2.4/discovery/search"
        
        data = {
            "orgId": self.org_id,
            "assetId": asset_id,
            "protocol": protocol,
            "type": "point",
            "otDeviceInstList": device_instances
        }
        
        try:
            response = poseidon.urlopen(self.access_key, self.secret_key, url, data)
            
            if response.get('code') == 0 and response.get('data') is True:
                # Wait for search to start processing
                time.sleep(5)
                return {"code": 0, "msg": "Points search initiated successfully"}
            else:
                error_msg = response.get('msg', 'Unknown error')
                return {"code": 1, "msg": f"Points search initiation failed: {error_msg}"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 1, "msg": str(e)}
    
    def fetch_points(self, asset_id: str, device_instance: int, device_address: str = "unknown-ip", protocol: str = 'bacnet') -> Dict:
        """Fetch points for a specific device"""
        url = f"{self.api_url}/enos-edge/v2.4/discovery/pointResponse"
        
        data = {
            "orgId": self.org_id,
            "assetId": asset_id,
            "protocol": protocol,
            "otDeviceInst": device_instance
        }
        
        # Set up polling parameters
        max_attempts = 30
        poll_interval = 10
        
        try:
            # First request to initiate the points retrieval
            response = poseidon.urlopen(self.access_key, self.secret_key, url, data)
            
            # Poll for results
            attempt = 1
            while attempt <= max_attempts:
                # Check if points retrieval is complete with proper structure
                points_data = []
                
                # Check for two possible response structures
                if ('data' in response and
                    isinstance(response['data'], dict) and
                    'record' in response['data'] and
                    isinstance(response['data']['record'], list)):
                    points_data = response['data']['record']
                elif ('data' in response and
                    isinstance(response['data'], list)):
                    points_data = response['data']
                
                if points_data and len(points_data) > 0:
                    # Process and save results
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    sanitized_address = re.sub(r'[^\w\-\.]', '_', device_address)
                    file_name = f"points_{asset_id}_{device_instance}_{sanitized_address}_{timestamp}.csv"
                    full_path = os.path.join(self.results_dir, file_name)
                    
                    # Pre-process points data
                    for point in points_data:
                        if 'description' not in point or point['description'] is None:
                            point['description'] = ''
                    
                    # Convert to DataFrame and save
                    df = pd.DataFrame(points_data)
                    
                    # Add metadata
                    df['assetId'] = asset_id
                    df['deviceInstance'] = device_instance
                    df['deviceAddress'] = device_address
                    df['timestamp'] = timestamp
                    
                    # Map columns as needed
                    if 'objectName' in df.columns and 'pointName' not in df.columns:
                        df['pointName'] = df['objectName']
                    
                    if 'objectType' in df.columns and 'pointType' not in df.columns:
                        df['pointType'] = df['objectType']
                    
                    # Ensure description is not null
                    if 'description' in df.columns:
                        df['description'] = df['description'].fillna('')
                    
                    # Add source column
                    df['source'] = protocol
                    
                    # Add pointId column
                    if 'pointId' not in df.columns and 'objectInst' in df.columns:
                        df['pointId'] = df.apply(lambda row: f"{device_instance}:{row['objectInst']}", axis=1)
                    
                    # Save to CSV
                    df.to_csv(full_path, index=False)
                    
                    # Return results
                    return {
                        "code": 0,
                        "file_path": full_path,
                        "point_count": len(points_data),
                        "points": points_data
                    }
                
                # Not complete yet, continue polling
                attempt += 1
                
                if attempt <= max_attempts:
                    time.sleep(poll_interval)
                    response = poseidon.urlopen(self.access_key, self.secret_key, url, data)
            
            # Polling timed out
            return {"code": 1, "msg": "Points retrieval timed out", "code": "TIMEOUT"}
        
        except Exception as e:
            traceback.print_exc()
            return {"code": 1, "msg": str(e)}
    
    def get_network_config(self, asset_id: str) -> Dict:
        """Get network configuration options from EnOS API"""
        url = f"{self.api_url}/enos-edge/v2.4/discovery/getNetConfig"
        
        data = {
            "orgId": self.org_id,
            "assetId": asset_id
        }
        
        try:
            response = poseidon.urlopen(self.access_key, self.secret_key, url, data)
            
            if response.get('code') == 0:
                return response
            else:
                error_msg = response.get('msg', 'Unknown error')
                return {"code": 1, "msg": f"Failed to retrieve network config: {error_msg}"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 1, "msg": str(e)}
    
    def search_device(self, asset_id: str, network: str, protocol: str = 'bacnet') -> Dict:
        """Search for devices on a specific network"""
        # First initiate the device search
        search_url = f"{self.api_url}/enos-edge/v2.4/discovery/search"
        
        search_data = {
            "orgId": self.org_id,
            "assetId": asset_id,
            "net": network,
            "type": "device",
            "protocol": protocol
        }
        
        try:
            # Initiate the search
            search_response = poseidon.urlopen(self.access_key, self.secret_key, search_url, search_data)
            
            if search_response.get('code') == 0 and search_response.get('data') is True:
                # Search initiated successfully, wait a moment
                time.sleep(5)
                
                # Now fetch the results
                return self.fetch_devices(asset_id)
            else:
                error_msg = search_response.get('msg', 'Unknown error')
                return {"code": 1, "msg": f"Device search initiation failed: {error_msg}"}
        except Exception as e:
            traceback.print_exc()
            return {"code": 1, "msg": str(e)}
    
    def fetch_devices(self, asset_id: str, protocol: str = 'bacnet') -> Dict:
        """Fetch discovered devices for a specific asset"""
        url = f"{self.api_url}/enos-edge/v2.4/discovery/deviceResponse"
        
        data = {
            "protocol": protocol,
            "pagination": {
                "pageNo": 1,
                "sorters": [
                    {
                        "field": "deviceName",
                        "order": "DESC"
                    }
                ],
                "pageSize": 100  # Fetch more devices
            },
            "assetIds": [
                asset_id
            ],
            "orgId": self.org_id
        }
        
        # Set up polling parameters
        max_attempts = 30
        poll_interval = 10
        
        try:
            # First request to fetch devices
            response = poseidon.urlopen(self.access_key, self.secret_key, url, data)
            
            # Poll for results
            attempt = 1
            while attempt <= max_attempts:
                # Check if retrieval is complete with proper structure
                if ('data' in response and
                    isinstance(response['data'], dict) and
                    'record' in response['data'] and
                    isinstance(response['data']['record'], list)):
                    
                    devices = response['data']['record']
                    if len(devices) > 0:
                        # Return the devices
                        return {
                            "code": 0,
                            "result": {
                                "deviceList": devices
                            }
                        }
                
                # Not complete yet, continue polling
                attempt += 1
                
                if attempt <= max_attempts:
                    time.sleep(poll_interval)
                    response = poseidon.urlopen(self.access_key, self.secret_key, url, data)
            
            # Polling timed out
            return {"code": 1, "msg": "Device retrieval timed out", "code": "TIMEOUT"}
        
        except Exception as e:
            traceback.print_exc()
            return {"code": 1, "msg": str(e)}
    
    def save_devices_to_file(self, devices: List[Dict], file_name: str) -> str:
        """Save device data to a file"""
        full_path = os.path.join(self.results_dir, file_name)
        
        try:
            with open(full_path, 'w') as f:
                json.dump(devices, f, indent=2)
            return full_path
        except Exception as e:
            traceback.print_exc()
            return None

class BMSParser:
    """Parser for BMS points data"""
    
    @staticmethod
    def preprocess_points(raw_points):
        """Preprocess the raw points data"""
        if not raw_points:
            return []
            
        # Extract point IDs
        point_ids = [point.get('pointId') for point in raw_points if point.get('pointId')]
        
        # Normalize point IDs
        return [BMSParser.normalize_point_id(pid) for pid in point_ids]
    
    @staticmethod
    def normalize_point_id(point_id):
        """Normalize a point ID by removing special characters"""
        return re.sub(r'[^\w\d-]', '', point_id.upper())

def export_mapped_data_to_csv(mapped_data: Dict, filename: Optional[str] = None) -> Optional[str]:
    """
    Exports the mapped point data to a CSV file.

    Args:
        mapped_data: The dictionary returned by EnOSMapper.map_points.
        filename: Optional filename for the CSV. If None, a default name is generated.

    Returns:
        The absolute path to the saved CSV file, or None if an error occurred.
    """
    if not mapped_data or "mappings" not in mapped_data:
        logger.error("Invalid or empty mapped data provided for export.")
        return None

    mappings = mapped_data.get("mappings", [])
    if not mappings:
        logger.warning("No mappings found in the data to export.")
        # Return None or path to an empty file? Returning None for now.
        return None

    # Define the directory to save the export file
    try:
        # Assumes utils.py is in backend/app/bms
        base_dir = Path(__file__).parent.parent.parent # Should point to backend/
        export_dir = base_dir / 'tmp' / 'exports' / 'mappings'
        export_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Export directory determined: {export_dir.resolve()}")
    except Exception as e:
        logger.error(f"Error creating export directory: {e}")
        return None

    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mapping_export_{timestamp}.csv"

    # Ensure filename has .csv extension
    if not filename.lower().endswith(".csv"):
        filename += ".csv"

    output_path = export_dir / filename

    # Flatten the data structure
    flat_data = []
    for item in mappings:
        original = item.get("original", {})
        mapping = item.get("mapping", {})
        reflection = item.get("reflection", {}) # Include reflection data

        flat_item = {
            "BMS_Point_ID": original.get("pointId"),
            "BMS_Point_Name": original.get("pointName"),
            "Device_Type": original.get("deviceType"),
            "Device_ID": original.get("deviceId"),
            "BMS_Point_Type": original.get("pointType"),
            "BMS_Unit": original.get("unit"),
            "EnOS_Point": mapping.get("enosPoint"),
            "Mapping_Status": mapping.get("status"),
            "Mapping_Confidence": mapping.get("confidence"), # Use confidence from mapping dict
            "Mapping_Source": mapping.get("source"),
            "Mapping_Error": mapping.get("error"),
            "Quality_Score": reflection.get("quality_score"), # From reflection
            "Mapping_Reason": reflection.get("reason"),
            "Mapping_Explanation": reflection.get("explanation"),
            "Mapping_Success": reflection.get("success")
        }
        flat_data.append(flat_item)

    if not flat_data:
         logger.warning("No data could be flattened for export.")
         return None

    # Create DataFrame
    try:
        df = pd.DataFrame(flat_data)

        # Select and order columns for clarity
        columns_order = [
            "BMS_Point_ID", "BMS_Point_Name", "Device_Type", "Device_ID",
            "BMS_Point_Type", "BMS_Unit", "EnOS_Point", "Mapping_Status",
            "Mapping_Confidence", "Mapping_Source", "Mapping_Error",
            "Quality_Score", "Mapping_Reason", "Mapping_Explanation", "Mapping_Success"
        ]
        # Ensure only existing columns are selected and handle potential missing columns
        df = df[[col for col in columns_order if col in df.columns]]

        # Save to CSV
        df.to_csv(output_path, index=False, encoding='utf-8-sig') # Use utf-8-sig for Excel compatibility
        logger.info(f"Successfully exported {len(df)} mapped points to: {output_path.resolve()}")
        return str(output_path.resolve()) # Return absolute path

    except Exception as e:
        logger.error(f"Failed to export mapped data to CSV at {output_path}: {str(e)}")
        logger.error(traceback.format_exc())
        return None 