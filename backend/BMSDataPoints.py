#!/usr/bin/env python3
"""
EnOS API Client

This script provides a command-line interface to various EnOS API endpoints,
particularly focusing on device discovery and point mapping.
"""
import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import re
import shutil
import traceback
import pandas as pd
from poseidon import poseidon
# Import poseidon if available
try:
    from poseidon import poseidon
except ImportError:
    poseidon = None
    print("Warning: Poseidon library not found. Some functions may not work correctly.")

# Directory to store results
results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
if not os.path.exists(results_dir):
    os.makedirs(results_dir, exist_ok=True)

# API Configuration - Get from environment variables or use defaults
# These global variables will no longer be the primary source for API calls
# in the refactored functions, but are kept for now for any parts of the script
# not yet refactored or for default values if needed elsewhere.
global_api_url = os.environ.get("ENOS_API_URL", "https://ag-eu2.envisioniot.com")
global_accessKey = os.environ.get("ENOS_ACCESS_KEY", "974a84b0-2ec1-44f7-aa3d-5fe01b55b718")
global_secretKey = os.environ.get("ENOS_SECRET_KEY", "04cc544f-ffcb-4b97-84fc-d7ecf8c4b8be")
global_orgId = os.environ.get("ENOS_ORG_ID", "o16975327606411181")
global_assetId = os.environ.get("ENOS_ASSET_ID", "5xkIipSH")

def fetchPoints(org_id_param: str, asset_id_param: str, device_instance_param: str, api_url_param: str, access_key_param: str, secret_key_param: str, device_address="unknown-ip"):
    """
    Fetch points for a specific device.
    
    Args:
        org_id_param: The Organization ID for the request.
        asset_id_param: The asset ID.
        device_instance_param: The device instance number to fetch points for.
        api_url_param: The base API URL for EnOS.
        access_key_param: The Access Key for API authentication.
        secret_key_param: The Secret Key for API authentication.
        device_address: The IP address of the device.
        
    Returns:
        The API response containing points for the device.
    """
    url = f"{api_url_param}/enos-edge/v2.4/discovery/pointResponse"
    
    data = {
        "orgId": org_id_param,
        "assetId": asset_id_param,
        "protocol": "bacnet",
        "otDeviceInst": device_instance_param
    }
    
    print(f"\nRetrieving points for device instance {device_instance_param} at address {device_address} (Org: {org_id_param}, Asset: {asset_id_param})...")
    print(f"Requesting points from: {url}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    max_attempts = 30
    poll_interval = 10
    
    try:
        print(f"Points retrieval request data: {data}")
        response = poseidon.urlopen(access_key_param, secret_key_param, url, data)
        print(f"Initial points retrieval response code: {response.get('code', 'Unknown')}")
        
        attempt = 1
        while attempt <= max_attempts:
            points_data = []
            if ('data' in response and
                isinstance(response['data'], dict) and
                'record' in response['data'] and
                isinstance(response['data']['record'], list)):
                points_data = response['data']['record']
            elif ('data' in response and
                isinstance(response['data'], list)):
                points_data = response['data']
            
            if points_data and len(points_data) > 0:
                print(f"\nPoints retrieval complete for device {device_instance_param}! Found {len(points_data)} points.")
                sample_size = min(5, len(points_data))
                print(f"\nSample of the first {sample_size} points for device {device_instance_param}:")
                for i in range(sample_size):
                    point = points_data[i]
                    point_name = point.get('pointName', 'Unknown')
                    point_type = point.get('pointType', 'Unknown')
                    print(f"{i+1}. {point_name} (Type: {point_type})")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                sanitized_address = re.sub(r'[^\\w\\-\.]', '_', device_address)
                file_name = f"points_{asset_id_param}_{device_instance_param}_{sanitized_address}_{timestamp}.csv"
                full_path = os.path.join(results_dir, file_name)
                
                for point in points_data:
                    if 'description' not in point or point['description'] is None:
                        point['description'] = ''
                
                df = pd.DataFrame(points_data)
                df['assetId'] = asset_id_param
                df['deviceInstance'] = device_instance_param
                df['deviceAddress'] = device_address
                df['timestamp'] = timestamp
                
                if 'objectName' in df.columns and 'pointName' not in df.columns:
                    df['pointName'] = df['objectName']
                
                if 'objectType' in df.columns and 'pointType' not in df.columns:
                    df['pointType'] = df['objectType']
                
                if 'description' in df.columns:
                    df['description'] = df['description'].fillna('').replace({pd.NA: '', None: ''})
                    remaining_nulls = df['description'].isnull().sum()
                    if remaining_nulls > 0:
                        print(f"WARNING: Still have {remaining_nulls} null values in description after filling")
                        for idx in df.index:
                            if pd.isna(df.at[idx, 'description']):
                                df.at[idx, 'description'] = ''
                
                df['source'] = 'bacnet'
                
                if 'pointId' not in df.columns and 'objectInst' in df.columns:
                    df['pointId'] = df.apply(lambda row: f"{device_instance_param}:{row['objectInst']}", axis=1)
                
                df.to_csv(full_path, index=False)
                print(f"Points data for device {device_instance_param} saved to {full_path}")
                result = {
                    "code": 0,
                    "result": {
                        "objectPropertys": points_data
                    }
                }
                return result
            
            print(f"Points retrieval in progress for device {device_instance_param}... (Attempt {attempt}/{max_attempts})")
            attempt += 1
            if attempt <= max_attempts:
                time.sleep(poll_interval)
                response = poseidon.urlopen(access_key_param, secret_key_param, url, data)
        
        print(f"Points retrieval for device {device_instance_param} timed out after {max_attempts * poll_interval} seconds.")
        points_data = []
        if ('data' in response and
            isinstance(response['data'], dict) and
            'record' in response['data'] and
            isinstance(response['data']['record'], list)):
            points_data = response['data']['record']
        elif ('data' in response and
            isinstance(response['data'], list)):
            points_data = response['data']
        
        if points_data and len(points_data) > 0:
            print(f"Partial results for device {device_instance_param}: Found {len(points_data)} points before timeout.")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sanitized_address = re.sub(r'[^\\w\\-\.]', '_', device_address)
            file_name = f"points_partial_{asset_id_param}_{device_instance_param}_{sanitized_address}_{timestamp}.csv"
            full_path = os.path.join(results_dir, file_name)
            
            for point in points_data:
                if 'description' not in point or point['description'] is None:
                    point['description'] = ''
            
            df = pd.DataFrame(points_data)
            df['assetId'] = asset_id_param
            df['deviceInstance'] = device_instance_param
            df['deviceAddress'] = device_address
            df['timestamp'] = timestamp
            df['status'] = 'partial - timed out'
            
            if 'objectName' in df.columns and 'pointName' not in df.columns:
                df['pointName'] = df['objectName']
            
            if 'objectType' in df.columns and 'pointType' not in df.columns:
                df['pointType'] = df['objectType']
            
            if 'description' in df.columns:
                df['description'] = df['description'].fillna('').replace({pd.NA: '', None: ''})
                remaining_nulls = df['description'].isnull().sum()
                if remaining_nulls > 0:
                    print(f"WARNING: Still have {remaining_nulls} null values in description after filling")
                    for idx in df.index:
                        if pd.isna(df.at[idx, 'description']):
                            df.at[idx, 'description'] = ''
            
            df['source'] = 'bacnet'
            
            if 'pointId' not in df.columns and 'objectInst' in df.columns:
                df['pointId'] = df.apply(lambda row: f"{device_instance_param}:{row['objectInst']}", axis=1)
            
            df.to_csv(full_path, index=False)
            print(f"Partial points data for device {device_instance_param} saved to {full_path}")
            
            result = {
                "code": 0,
                "result": {
                    "objectPropertys": points_data
                }
            }
            return result
        else:
            print(f"No points found for device {device_instance_param} before timeout.")
            return {"code": 1, "msg": "Timeout waiting for points"}
    
    except Exception as e:
        print(f"Error during points retrieval: {str(e)}")
        traceback.print_exc()
        return {"code": 1, "msg": str(e)}

def getNetConfig(org_id_param: str, asset_id_param: str, api_url_param: str, access_key_param: str, secret_key_param: str):
    """
    Get network configuration from the EnOS API.
    
    Args:
        org_id_param: The Organization ID for the request.
        asset_id_param: Asset ID to use for the request.
        api_url_param: The base API URL for EnOS.
        access_key_param: The Access Key for API authentication.
        secret_key_param: The Secret Key for API authentication.
    
    Returns:
        The API response containing network configuration.
    """
    # API URL with the appropriate asset ID
    url = f"{api_url_param}/enos-edge/v2.4/discovery/getNetConfig?orgId={org_id_param}&assetId={asset_id_param}"
    
    if not access_key_param or not secret_key_param:
        print("Access key and secret key are required. Exiting.")
        return {"code": 1, "msg": "Missing credentials"}
    
    try:
        # Call the API
        print(f"Fetching network configuration for asset ID: {asset_id_param} using Org ID: {org_id_param}")
        print(f"Request URL: {url}")
        response = poseidon.urlopen(access_key_param, secret_key_param, url)
        
        print("Response from getNetConfig:")
        print(response)
        
        # Add a check for None response before attempting to access it
        if response is None:
            print(f"No response received from API (likely an HTTP error like 404). URL: {url}")
            return {"code": 1, "msg": "No response from API (e.g., HTTP 404 Not Found)", "data": None}
        
        # Check if response has data field with options
        if 'data' in response and isinstance(response['data'], list) and len(response['data']) > 0:
            print(f"\nAvailable network options for asset ID {asset_id_param}:")
            
            # Display the available options
            for i, option in enumerate(response['data']):
                print(f"{i+1}. {option}")
            
            return response
        else:
            print(f"No network options found in response data for asset ID {asset_id_param}")
            return response
    except Exception as e:
        print(f"Error getting network configuration for asset ID {asset_id_param}: {str(e)}")
        traceback.print_exc()
        return {"code": 1, "msg": str(e)}

def search_devices_on_networks(assetId, networks):
    """
    Search for devices on specified networks.
    
    Args:
        assetId: The asset ID to search for devices
        networks: List of networks to search on
        
    Returns:
        Dictionary of network -> device search results
    """
    if not networks:
        print("No networks specified. Exiting device search.")
        return {"code": 1, "msg": "No networks selected"}
    
    # Search devices on each selected network
    results = {}
    all_devices = []
    
    for net in networks:
        print(f"\nSearching for devices on network: {net}")
        search_result = searchDevice(orgId, assetId, net, api_url, accessKey, secretKey)
        results[net] = search_result
        
        # Extract devices if available
        if (search_result and "result" in search_result and 
            "deviceList" in search_result["result"] and 
            isinstance(search_result["result"]["deviceList"], list)):
            devices = search_result["result"]["deviceList"]
            all_devices.extend(devices)
            print(f"Found {len(devices)} devices on network {net}")
    
    return {
        "code": 0,
        "results": results,
        "all_devices": all_devices,
        "count": len(all_devices)
    }

def search_points(org_id_param: str, asset_id_param: str, device_instances_param: List[str], api_url_param: str, access_key_param: str, secret_key_param: str):
    """
    Search for points on specified devices using the search API endpoint.
    
    Args:
        org_id_param: The Organization ID for the request.
        asset_id_param: The asset ID.
        device_instances_param: List of device instance numbers.
        api_url_param: The base API URL for EnOS.
        access_key_param: The Access Key for API authentication.
        secret_key_param: The Secret Key for API authentication.
        
    Returns:
        The API response indicating if the search was initiated successfully
    """
    url = f"{api_url_param}/enos-edge/v2.4/discovery/search"
    
    data = {
        "orgId": org_id_param,
        "assetId": asset_id_param,
        "protocol": "bacnet",
        "type": "point",
        "otDeviceInstList": device_instances_param
    }
    
    print(f"\nInitiating points search for {len(device_instances_param)} devices (Org: {org_id_param}, Asset: {asset_id_param})...")
    print(f"Request URL: {url}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        response = poseidon.urlopen(access_key_param, secret_key_param, url, data)
        print(f"Points search initiation response: {response}")
        
        if 'code' in response and response['code'] == 0:
            data_value = response.get('data')
            
            if data_value is True:
                print(f"Points search initiated successfully for {len(device_instances_param)} devices")
                # Wait a moment for the search to start processing
                time.sleep(5)
                return {"code": 0, "msg": "Points search initiated successfully"}
            else:
                print(f"Points search initiation failed with unexpected result: {data_value}")
                return {"code": 1, "msg": f"Points search initiation failed: {data_value}"}
        else:
            error_msg = response.get('msg', 'Unknown error')
            print(f"Points search initiation failed: {error_msg}")
            return {"code": 1, "msg": f"Points search initiation failed: {error_msg}"}
    except Exception as e:
        print(f"Error initiating points search: {str(e)}")
        traceback.print_exc()
        return {"code": 1, "msg": str(e)}

def fetch_points_for_devices(org_id_param: str, asset_id_param: str, devices_param: List[Dict], api_url_param: str, access_key_param: str, secret_key_param: str):
    """
    Fetch points for specified devices.
    
    Args:
        org_id_param: The Organization ID for the request.
        asset_id_param: The asset ID.
        devices_param: List of device objects.
        api_url_param: The base API URL for EnOS.
        access_key_param: The Access Key for API authentication.
        secret_key_param: The Secret Key for API authentication.
        
    Returns:
        Dictionary of device_instance -> points results
    """
    if not devices_param:
        print("No devices specified. Exiting point fetching.")
        return {"code": 1, "msg": "No devices selected"}
    
    device_instances = []
    device_addresses = {}
    
    for device in devices_param:
        instance = device.get("otDeviceInst")
        if instance:
            device_instances.append(int(instance))
            device_addresses[str(instance)] = device.get("address", "unknown-ip")
    
    if not device_instances:
        print("No valid device instances found. Exiting point fetching.")
        return {"code": 1, "msg": "No valid device instances"}
    
    search_result = search_points(org_id_param, asset_id_param, device_instances, api_url_param, access_key_param, secret_key_param)
    
    if search_result.get("code") != 0:
        print(f"Failed to initiate points search: {search_result.get('msg', 'Unknown error')}")
        return search_result
    
    results = {}
    for device_instance_str in device_instances: # Ensure we iterate over what search_points used
        device_instance = str(device_instance_str) # Make sure it's a string for dict key
        device_address = device_addresses.get(device_instance, "unknown-ip")
        device_name = next((d.get("deviceName", "Unknown") for d in devices_param 
                           if str(d.get("otDeviceInst")) == device_instance), 
                          f"Device {device_instance}")
        
        print(f"\nFetching points for {device_name} (Instance: {device_instance})...")
        # Pass all required params to fetchPoints
        points_response = fetchPoints(org_id_param, asset_id_param, device_instance, api_url_param, access_key_param, secret_key_param, device_address)
        results[device_instance] = points_response
    
    return {
        "code": 0,
        "point_results": results
    }

def searchDevice(org_id_param: str, asset_id_param: str, net_param: str, api_url_param: str, access_key_param: str, secret_key_param: str):
    """
    Initiate a device search on the specified network.
    
    Args:
        org_id_param: The Organization ID for the request.
        asset_id_param: The asset ID to search.
        net_param: The network option to use.
        api_url_param: The base API URL for EnOS.
        access_key_param: The Access Key for API authentication.
        secret_key_param: The Secret Key for API authentication.
        
    Returns:
        The API response from the search request
    """
    url = f"{api_url_param}/enos-edge/v2.4/discovery/search"
    
    data = {
        "orgId": org_id_param,
        "assetId": asset_id_param,
        "net": net_param,
        "type": "device",
        "protocol": "bacnet"
    }
    
    if not access_key_param or not secret_key_param:
        print("Access key and secret key are required. Exiting.")
        return {"code": 1, "msg": "Missing credentials"}
    
    try:
        print(f"Search request data: {data}")
        print(f"Initiating device discovery on network {net_param} for org {org_id_param} asset {asset_id_param}...")
        
        response = poseidon.urlopen(access_key_param, secret_key_param, url, data)
        print(f"Search response: {response}")
        
        if 'code' in response and response['code'] == 0:
            data_value = response.get('data')
            if data_value is True:
                print("Discovery initiated successfully. Retrieving devices...")
                time.sleep(5)
                # Pass the dynamic parameters to fetchDevice as well
                return fetchDevice(org_id_param, asset_id_param, api_url_param, access_key_param, secret_key_param)
            else:
                print(f"Discovery failed or returned unexpected result: {data_value}")
        else:
            error_msg = response.get('msg', 'Unknown error')
            print(f"Error during discovery: {error_msg}")
        
        return response
    except Exception as e:
        print(f"Error during device discovery: {str(e)}")
        traceback.print_exc()
        return {"code": 1, "msg": str(e)}

def fetchDevice(org_id_param: str, asset_id_param: str, api_url_param: str, access_key_param: str, secret_key_param: str):
    """
    Fetch discovered devices for a specific asset.
    
    Args:
        org_id_param: The Organization ID for the request.
        asset_id_param: The asset ID to retrieve devices for.
        api_url_param: The base API URL for EnOS.
        access_key_param: The Access Key for API authentication.
        secret_key_param: The Secret Key for API authentication.
        
    Returns:
        The API response containing discovered devices
    """
    url = f"{api_url_param}/enos-edge/v2.4/discovery/deviceResponse"
    data = {
        "protocol": "bacnet",
        "pagination": {
            "pageNo": 1,
            "sorters": [
                {
                    "field": "deviceName",
                    "order": "DESC"
                }
            ],
            "pageSize": 100
        },
        "assetIds": [
            asset_id_param
        ],
        "orgId": org_id_param
    }
    
    print(f"Starting BACnet scan for asset {asset_id_param} (Org: {org_id_param})...")
    
    max_attempts = 30
    poll_interval = 10
    
    response = poseidon.urlopen(access_key_param, secret_key_param, url, data)
    print(f"Initial scan response: {response}")
    
    # Check if we need to wait for results
    attempt = 1
    while attempt <= max_attempts:
        # Check if scan is complete with proper structure for device response
        if ('data' in response and
            isinstance(response['data'], dict) and
            'record' in response['data'] and
            isinstance(response['data']['record'], list)):
            
            devices = response['data']['record']
            if len(devices) > 0:
                # Save all discovered devices to a JSON file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                device_file = f"devices_{asset_id_param}_{timestamp}.json"
                device_file_path = os.path.join(results_dir, device_file)
                try:
                    with open(device_file_path, "w") as f:
                        json.dump(response, f, indent=2)
                    print(f"Saved device discovery results to {device_file_path}")
                except Exception as e:
                    print(f"Error saving device discovery results: {str(e)}")
                
                print(f"\nScan complete! Found {len(devices)} devices:")
                for i, device in enumerate(devices):
                    device_name = device.get('deviceName', 'Unknown')
                    device_instance = device.get('otDeviceInst', 'Unknown')
                    device_address = device.get('address', 'Unknown')
                    print(f"{i+1}. {device_name} (Instance: {device_instance}), IP: {device_address}")
                
                # Return the devices in a standardized format
                result = {
                    "code": 0,
                    "result": {
                        "deviceList": devices
                    }
                }
                
                return result
            
            # No devices found yet
            print(f"No devices found yet (Attempt {attempt}/{max_attempts})")
            attempt += 1
            
            if attempt <= max_attempts:
                time.sleep(poll_interval)
                response = poseidon.urlopen(access_key_param, secret_key_param, url, data)
        else:
            # Wait for the scanning to complete
            print(f"Scanning in progress (Attempt {attempt}/{max_attempts})")
            attempt += 1
            
            if attempt <= max_attempts:
                time.sleep(poll_interval)
                response = poseidon.urlopen(access_key_param, secret_key_param, url, data)
    
    print(f"Device scan timed out after {max_attempts * poll_interval} seconds")
    return {"code": 1, "msg": "Device scan timed out", "data": response.get('data', {})}

# For web app integration - these functions don't use input() prompts
def discover_devices(asset_id=None, network=None):
    """
    Wrapper function for discovering devices, suitable for web app integration.
    
    Args:
        asset_id: Optional asset ID (defaults to global assetId)
        network: Optional network to use
        
    Returns:
        Dictionary of results
    """
    if asset_id is None:
        asset_id = global_assetId
    
    if network is None:
        # Just get the network config and return it - let the UI handle selection
        return getNetConfig(global_orgId, asset_id, global_api_url, global_accessKey, global_secretKey)
    else:
        # Use the provided network directly
        return searchDevice(global_orgId, asset_id, network, global_api_url, global_accessKey, global_secretKey)

def discover_devices_on_networks(asset_id=None, networks=None):
    """
    Discover devices on multiple networks.
    
    Args:
        asset_id: Optional asset ID (defaults to global assetId)
        networks: List of networks to search
        
    Returns:
        Dictionary of results
    """
    if asset_id is None:
        asset_id = global_assetId
    
    if networks is None or not networks:
        # Default to discovering on "No Network Card"
        networks = ["No Network Card"]
    
    return search_devices_on_networks(asset_id, networks)

def get_points_for_devices(asset_id=None, devices=None):
    """
    Get points for multiple devices.
    
    Args:
        asset_id: Optional asset ID (defaults to global assetId)
        devices: List of device objects
        
    Returns:
        Dictionary of results
    """
    if asset_id is None:
        asset_id = global_assetId
    
    if devices is None or not devices:
        return {"code": 1, "msg": "No devices specified"}
    
    return fetch_points_for_devices(global_orgId, asset_id, devices, global_api_url, global_accessKey, global_secretKey)

def print_usage():
    """Print usage information for the script."""
    print("\nUsage: python BMSDataPoints.py <command> [options]")
    print("\nCommands:")
    print("  points <assetId> <deviceInstance1>[,deviceInstance2,...]")
    print("      Fetch points for one or more devices")
    print("  map [<points_file>]")
    print("      Run AI mapping on a points file (defaults to ./results/points.csv)")
    print("  ai [<points_file>]")
    print("      Alias for 'map' command")

def main():
    """Main entry point for the script."""
    # Create results directory if it doesn't exist
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        print(f"Created results directory: {results_dir}")
    
    # If no arguments provided, show usage
    if len(sys.argv) <= 1:
        print_usage()
        return
    
    # Check command line arguments for specific function to call
    command = sys.argv[1].lower()
    
    if command == "points":
        asset_id = sys.argv[2] if len(sys.argv) > 2 else None
        
        if asset_id:
            # Check if device instances are provided
            if len(sys.argv) > 3:
                # Check if multiple device instances are provided as comma-separated values
                device_input = sys.argv[3]
                if ',' in device_input:
                    # Parse comma-separated device instances
                    try:
                        device_instances = [int(d.strip()) for d in device_input.split(',') if d.strip()]
                        # Create a default mapping of instances to unknown IPs
                        device_addresses = {str(inst): "unknown-ip" for inst in device_instances}
                        print(f"Processing multiple devices: {device_instances}")
                        get_points_for_devices(asset_id, [{"otDeviceInst": inst, "address": addr} for inst, addr in device_addresses.items()])
                    except ValueError:
                        print("Error: Invalid device instance format. Use comma-separated numbers.")
                else:
                    # Single device instance
                    try:
                        device_instance = int(device_input)
                        # Create a default mapping with unknown IP
                        device_addresses = {str(device_instance): "unknown-ip"}
                        print(f"Processing single device: {device_instance}")
                        get_points_for_devices(asset_id, [{"otDeviceInst": device_instance, "address": addr} for device_instance, addr in device_addresses.items()])
                    except ValueError:
                        print("Error: Device instance must be a number")
            else:
                print("Error: At least one device instance is required for points command")
                print("Usage: python BMSDataPoints.py points <assetId> <deviceInstance1>[,deviceInstance2,...]")
        else:
            print("Error: assetId is required for points command")
            print("Usage: python BMSDataPoints.py points <assetId> <deviceInstance1>[,deviceInstance2,...]")
    elif command == "map" or command == "ai":
        # Run AI mapping on an existing points file
        points_file = sys.argv[2] if len(sys.argv) > 2 else os.path.join(results_dir, "points.csv")
        
        if os.path.exists(points_file):
            print(f"Running AI mapping with points file: {points_file}")
            run_ai_mapping_trial(points_file)
        else:
            print(f"Error: Points file '{points_file}' not found")
            
            # Search for available points files to suggest
            if os.path.exists(results_dir):
                point_files = [f for f in os.listdir(results_dir) if f.startswith("points_") and f.endswith(".csv")]
                if point_files:
                    print("\nAvailable point files:")
                    for i, file in enumerate(point_files[:10]):  # Show up to 10 files
                        print(f"  {i+1}. {file}")
                    if len(point_files) > 10:
                        print(f"  ... and {len(point_files) - 10} more")
                    print("\nTry one of these files with:")
                    print(f"  python BMSDataPoints.py map {os.path.join(results_dir, point_files[0])}")
            
            print("\nUsage: python BMSDataPoints.py map [<points_file>]")
            print("       If <points_file> is not provided, defaults to ./results/points.csv")
    else:
        print(f"Unknown command: {command}")
        print_usage()

if __name__ == "__main__":
    main()