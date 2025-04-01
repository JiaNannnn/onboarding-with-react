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
api_url = os.environ.get("ENOS_API_URL", "https://ag-eu2.envisioniot.com")
accessKey = os.environ.get("ENOS_ACCESS_KEY", "974a84b0-2ec1-44f7-aa3d-5fe01b55b718")
secretKey = os.environ.get("ENOS_SECRET_KEY", "04cc544f-ffcb-4b97-84fc-d7ecf8c4b8be")
orgId = os.environ.get("ENOS_ORG_ID", "o16975327606411181")
assetId = os.environ.get("ENOS_ASSET_ID", "5xkIipSH")

def fetchPoints(assetId, device_instance, device_address="unknown-ip"):
    """
    Fetch points for a specific device.
    
    Args:
        assetId: The asset ID
        device_instance: The device instance number to fetch points for
        device_address: The IP address of the device
        
    Returns:
        The API response containing points for the device
    """
    url = f"{api_url}/enos-edge/v2.4/discovery/pointResponse"
    access_key = accessKey
    secret_key = secretKey
    
    data = {
        "orgId": orgId,
        "assetId": assetId,
        "protocol": "bacnet",
        "otDeviceInst": device_instance
    }
    
    print(f"\nRetrieving points for device instance {device_instance} at address {device_address}...")
    print(f"Requesting points from: {url}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    # Set up polling parameters
    max_attempts = 30  # Maximum number of polling attempts
    poll_interval = 10
    
    try:
        # First request to initiate the points retrieval
        print(f"Points retrieval request data: {data}")
        response = poseidon.urlopen(access_key, secret_key, url, data)
        print(f"Initial points retrieval response code: {response.get('code', 'Unknown')}")
        
        # Check if we need to wait for results
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
                print(f"\nPoints retrieval complete for device {device_instance}! Found {len(points_data)} points.")
                
                # Display a sample of points (first 5)
                sample_size = min(5, len(points_data))
                print(f"\nSample of the first {sample_size} points for device {device_instance}:")
                for i in range(sample_size):
                    point = points_data[i]
                    point_name = point.get('pointName', 'Unknown')
                    point_type = point.get('pointType', 'Unknown')
                    print(f"{i+1}. {point_name} (Type: {point_type})")
                
                # Create a timestamp for the filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Sanitize the device address for filename
                sanitized_address = re.sub(r'[^\w\-\.]', '_', device_address)
                file_name = f"points_{assetId}_{device_instance}_{sanitized_address}_{timestamp}.csv"
                full_path = os.path.join(results_dir, file_name)
                
                # Pre-process the points data to ensure no null values in critical fields
                for point in points_data:
                    # Ensure description is not null
                    if 'description' not in point or point['description'] is None:
                        point['description'] = ''
                
                # Convert points data to DataFrame and save as CSV
                df = pd.DataFrame(points_data)
                
                # Add metadata as additional columns
                df['assetId'] = assetId
                df['deviceInstance'] = device_instance
                df['deviceAddress'] = device_address
                df['timestamp'] = timestamp
                
                # Add or rename columns to match what the AI engine expects
                # Map objectName to pointName if pointName doesn't exist
                if 'objectName' in df.columns and 'pointName' not in df.columns:
                    df['pointName'] = df['objectName']
                
                # Map objectType to pointType if pointType doesn't exist
                if 'objectType' in df.columns and 'pointType' not in df.columns:
                    df['pointType'] = df['objectType']
                
                # Ensure description is not null (AI engine might require this)
                if 'description' in df.columns:
                    df['description'] = df['description'].fillna('').replace({pd.NA: '', None: ''})
                    # Double-check that nulls are gone
                    remaining_nulls = df['description'].isnull().sum()
                    if remaining_nulls > 0:
                        print(f"WARNING: Still have {remaining_nulls} null values in description after filling")
                        # Try a more direct approach
                        for idx in df.index:
                            if pd.isna(df.at[idx, 'description']):
                                df.at[idx, 'description'] = ''
                
                # Add a source column (AI engine might use this for identification)
                df['source'] = 'bacnet'
                
                # Add a pointId column if it doesn't exist (combining device instance and object instance)
                if 'pointId' not in df.columns and 'objectInst' in df.columns:
                    df['pointId'] = df.apply(lambda row: f"{device_instance}:{row['objectInst']}", axis=1)
                
                # Save to CSV
                df.to_csv(full_path, index=False)
                
                print(f"Points data for device {device_instance} saved to {full_path}")
                
                # For compatibility with other functions that expect different structure
                result = {
                    "code": 0,
                    "result": {
                        "objectPropertys": points_data
                    }
                }
                
                return result
            
            # If not complete or no points found yet
            print(f"Points retrieval in progress for device {device_instance}... (Attempt {attempt}/{max_attempts})")
            attempt += 1
            
            if attempt <= max_attempts:
                time.sleep(poll_interval)
                response = poseidon.urlopen(access_key, secret_key, url, data)
        
        # If we get here, polling timed out
        print(f"Points retrieval for device {device_instance} timed out after {max_attempts * poll_interval} seconds.")
        
        # Try to extract any partial results using proper structure check
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
            print(f"Partial results for device {device_instance}: Found {len(points_data)} points before timeout.")
            
            # Create a timestamp for the filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Sanitize the device address for filename
            sanitized_address = re.sub(r'[^\w\-\.]', '_', device_address)
            file_name = f"points_partial_{assetId}_{device_instance}_{sanitized_address}_{timestamp}.csv"
            full_path = os.path.join(results_dir, file_name)
            
            # Pre-process the points data to ensure no null values in critical fields
            for point in points_data:
                # Ensure description is not null
                if 'description' not in point or point['description'] is None:
                    point['description'] = ''
            
            # Convert points data to DataFrame and save as CSV
            df = pd.DataFrame(points_data)
            
            # Add metadata as additional columns
            df['assetId'] = assetId
            df['deviceInstance'] = device_instance
            df['deviceAddress'] = device_address
            df['timestamp'] = timestamp
            df['status'] = 'partial - timed out'
            
            # Add or rename columns to match what the AI engine expects
            # Map objectName to pointName if pointName doesn't exist
            if 'objectName' in df.columns and 'pointName' not in df.columns:
                df['pointName'] = df['objectName']
            
            # Map objectType to pointType if pointType doesn't exist
            if 'objectType' in df.columns and 'pointType' not in df.columns:
                df['pointType'] = df['objectType']
            
            # Ensure description is not null (AI engine might require this)
            if 'description' in df.columns:
                df['description'] = df['description'].fillna('').replace({pd.NA: '', None: ''})
                # Double-check that nulls are gone
                remaining_nulls = df['description'].isnull().sum()
                if remaining_nulls > 0:
                    print(f"WARNING: Still have {remaining_nulls} null values in description after filling")
                    # Try a more direct approach
                    for idx in df.index:
                        if pd.isna(df.at[idx, 'description']):
                            df.at[idx, 'description'] = ''
            
            # Add a source column (AI engine might use this for identification)
            df['source'] = 'bacnet'
            
            # Add a pointId column if it doesn't exist (combining device instance and object instance)
            if 'pointId' not in df.columns and 'objectInst' in df.columns:
                df['pointId'] = df.apply(lambda row: f"{device_instance}:{row['objectInst']}", axis=1)
            
            # Save to CSV
            df.to_csv(full_path, index=False)
            
            print(f"Partial points data for device {device_instance} saved to {full_path}")
            
            # For compatibility with other functions
            result = {
                "code": 0,
                "result": {
                    "objectPropertys": points_data
                }
            }
            
            return result
        else:
            print(f"No points found for device {device_instance} before timeout.")
            return {"code": 1, "msg": "Timeout waiting for points"}
    
    except Exception as e:
        print(f"Error during points retrieval: {str(e)}")
        traceback.print_exc()
        return {"code": 1, "msg": str(e)}

def getNetConfig(asset_id=None):
    """
    Get network configuration from the EnOS API.
    
    Args:
        asset_id: Optional. Asset ID to use for the request. 
                If provided, overrides the default assetId.
    
    Returns:
        The API response containing network configuration.
    """
    # Use provided asset_id if available, otherwise use default
    target_asset_id = asset_id if asset_id else assetId
    
    # API URL with the appropriate asset ID
    url = f"{api_url}/enos-edge/v2.4/discovery/getNetConfig?orgId={orgId}&assetId={target_asset_id}"
    
    # Get access key and secret key from user
    access_key = accessKey
    secret_key = secretKey
    
    if not access_key or not secret_key:
        print("Access key and secret key are required. Exiting.")
        return {"code": 1, "msg": "Missing credentials"}
    
    try:
        # Call the API
        print(f"Fetching network configuration for asset ID: {target_asset_id}")
        print(f"Request URL: {url}")
        response = poseidon.urlopen(access_key, secret_key, url)
        
        print("Response from getNetConfig:")
        print(response)
        
        # Check if response has data field with options
        if 'data' in response and isinstance(response['data'], list) and len(response['data']) > 0:
            print(f"\nAvailable network options for asset ID {target_asset_id}:")
            
            # Display the available options
            for i, option in enumerate(response['data']):
                print(f"{i+1}. {option}")
            
            return response
        else:
            print(f"No network options found in response data for asset ID {target_asset_id}")
            return response
    except Exception as e:
        print(f"Error getting network configuration for asset ID {target_asset_id}: {str(e)}")
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
        search_result = searchDevice(assetId, net)
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

def search_points(assetId, device_instances):
    """
    Search for points on specified devices using the search API endpoint.
    
    This function initiates the points search process using the /enos-edge/v2.4/discovery/search
    endpoint with type=point and the list of device instances.
    
    Args:
        assetId: The asset ID
        device_instances: List of device instance numbers
        
    Returns:
        The API response indicating if the search was initiated successfully
    """
    url = f"{api_url}/enos-edge/v2.4/discovery/search"
    access_key = accessKey
    secret_key = secretKey
    
    data = {
        "orgId": orgId,
        "assetId": assetId,
        "protocol": "bacnet",
        "type": "point",
        "otDeviceInstList": device_instances
    }
    
    print(f"\nInitiating points search for {len(device_instances)} devices...")
    print(f"Request URL: {url}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        # Call the API to initiate the points search
        response = poseidon.urlopen(access_key, secret_key, url, data)
        print(f"Points search initiation response: {response}")
        
        # Check if the search was successfully initiated
        if 'code' in response and response['code'] == 0:
            data_value = response.get('data')
            
            if data_value is True:
                print(f"Points search initiated successfully for {len(device_instances)} devices")
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

def fetch_points_for_devices(assetId, devices):
    """
    Fetch points for specified devices.
    
    This function follows the correct API flow:
    1. First call search_points with type=point to initiate the points search
    2. Then call fetchPoints for each device to retrieve the results
    
    Args:
        assetId: The asset ID
        devices: List of device objects
        
    Returns:
        Dictionary of device_instance -> points results
    """
    if not devices:
        print("No devices specified. Exiting point fetching.")
        return {"code": 1, "msg": "No devices selected"}
    
    # Extract device instances for the search API call
    device_instances = []
    device_addresses = {}
    
    for device in devices:
        instance = device.get("otDeviceInst")
        if instance:
            device_instances.append(int(instance))
            device_addresses[str(instance)] = device.get("address", "unknown-ip")
    
    if not device_instances:
        print("No valid device instances found. Exiting point fetching.")
        return {"code": 1, "msg": "No valid device instances"}
    
    # First, initiate the points search using the search API
    search_result = search_points(assetId, device_instances)
    
    if search_result.get("code") != 0:
        print(f"Failed to initiate points search: {search_result.get('msg', 'Unknown error')}")
        return search_result
    
    # Now fetch points for each device instance
    results = {}
    
    for device_instance in device_instances:
        device_address = device_addresses.get(str(device_instance), "unknown-ip")
        device_name = next((device.get("deviceName", "Unknown") for device in devices 
                           if str(device.get("otDeviceInst")) == str(device_instance)), 
                          f"Device {device_instance}")
        
        print(f"\nFetching points for {device_name} (Instance: {device_instance})...")
        points_response = fetchPoints(assetId, device_instance, device_address)
        results[str(device_instance)] = points_response
    
    return {
        "code": 0,
        "point_results": results
    }

def searchDevice(assetId, net=None):
    """
    Initiate a device search on the specified network.
    
    Args:
        assetId: The asset ID to search
        net: The network option to use
        
    Returns:
        The API response from the search request
    """
    # API URL from user
    url = f"{api_url}/enos-edge/v2.4/discovery/search"
    
    # Get access key and secret key from user
    access_key = accessKey
    secret_key = secretKey
    
    # Use provided assetId and net if available, otherwise use defaults
    if assetId is None:
        assetId = "Device is not an Edge Device"
    
    if net is None:
        net = "No Network Card"
    
    data = {
        "orgId": orgId,
        "assetId": assetId,
        "net": net,
        "type": "device",
        "protocol": "bacnet"
    }
    
    if not access_key or not secret_key:
        print("Access key and secret key are required. Exiting.")
        return {"code": 1, "msg": "Missing credentials"}
    
    try:
        # Call the API
        print(f"Search request data: {data}")
        print(f"Initiating device discovery on network {net}...")
        
        # Initialize the search and start polling
        response = poseidon.urlopen(access_key, secret_key, url, data)
        print(f"Search response: {response}")
        
        # Check if the search request was successful
        if 'code' in response and response['code'] == 0:
            data_value = response.get('data')
            
            # Check specifically for a boolean True result
            if data_value is True:
                print("Discovery initiated successfully. Retrieving devices...")
                # Allow some time for the discovery process to start before checking devices
                time.sleep(5)
                return fetchDevice(assetId)
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

def fetchDevice(assetId):
    """
    Fetch discovered devices for a specific asset.
    
    Args:
        assetId: The asset ID to retrieve devices for
        
    Returns:
        The API response containing discovered devices
    """
    url = f"{api_url}/enos-edge/v2.4/discovery/deviceResponse"
    access_key = accessKey
    secret_key = secretKey
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
            "pageSize": 10
        },
        "assetIds": [
            assetId
        ],
        "orgId": orgId
    }
    
    print(f"Starting BACnet scan for asset {assetId}...")
    
    # Set up polling parameters
    max_attempts = 30  # Maximum number of polling attempts
    poll_interval = 10  # Time in seconds between polls
    
    # First request to initiate the scan
    response = poseidon.urlopen(access_key, secret_key, url, data)
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
                device_file = f"devices_{assetId}_{timestamp}.json"
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
                response = poseidon.urlopen(access_key, secret_key, url, data)
        else:
            # Wait for the scanning to complete
            print(f"Scanning in progress (Attempt {attempt}/{max_attempts})")
            attempt += 1
            
            if attempt <= max_attempts:
                time.sleep(poll_interval)
                response = poseidon.urlopen(access_key, secret_key, url, data)
    
    # If we get here, polling timed out
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
        asset_id = assetId
    
    if network is None:
        # Just get the network config and return it - let the UI handle selection
        return getNetConfig()
    else:
        # Use the provided network directly
        return searchDevice(asset_id, network)

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
        asset_id = assetId
    
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
        asset_id = assetId
    
    if devices is None or not devices:
        return {"code": 1, "msg": "No devices specified"}
    
    return fetch_points_for_devices(asset_id, devices)

def run_ai_mapping_trial(points_file):
    """
    Run a trial of AI mapping on a points file.
    
    Args:
        points_file: Path to the CSV file containing points data
    
    Returns:
        Dictionary with results of the trial
    """
    try:
        print(f"\n=== ANALYZING POINTS FILE: {points_file} ===")
        
        # Check if file exists
        if not os.path.exists(points_file):
            print(f"File not found: {points_file}")
            return {"code": 1, "msg": f"File not found: {points_file}"}
        
        # Load the CSV file
        print("Loading CSV file...")
        try:
            df = pd.read_csv(points_file)
            print(f"CSV loaded with {len(df)} rows and {len(df.columns)} columns")
            print(f"Columns: {', '.join(df.columns)}")
        except Exception as e:
            print(f"Error loading CSV file: {str(e)}")
            return {"code": 1, "msg": f"Error loading CSV file: {str(e)}"}
        
        # Check if the file has the structure expected by the AI engine
        # This is a heuristic check - we're looking for certain patterns
        required_columns = ["deviceInstance", "objectType", "objectInstance", "objectName"]
        is_points_data = all(col in df.columns for col in required_columns)
        
        if is_points_data:
            print("\nCSV appears to have a valid points data structure")
        else:
            print("\nWARNING: CSV does not appear to have a valid points data structure")
            print("The AI processing engine may not recognize this as points data")
            
            # Check for common column name mismatches
            if "objectInst" in df.columns and "objectInstance" not in df.columns:
                print("Found 'objectInst' but missing 'objectInstance' - this is a critical issue")
                print("The dashboard code specifically checks for 'objectInstance', not 'objectInst'")
                
                # Try to use the fix_csv_for_ai_engine script
                try:
                    from fix_csv_for_ai_engine import fix_csv_for_ai_engine
                    print("\nAttempting to fix CSV using fix_csv_for_ai_engine...")
                    
                    fixed_file_path = fix_csv_for_ai_engine(points_file)
                    if fixed_file_path and os.path.exists(fixed_file_path):
                        print(f"Successfully fixed CSV file: {fixed_file_path}")
                        
                        # Use the fixed file for further processing
                        points_file = fixed_file_path
                        
                        # Reload the fixed CSV
                        df = pd.read_csv(points_file)
                        print(f"Loaded fixed CSV with {len(df)} rows and {len(df.columns)} columns")
                        print(f"Fixed columns: {', '.join(df.columns)}")
                        
                        # Check if the fix worked
                        is_points_data = all(col in df.columns for col in required_columns)
                        if is_points_data:
                            print("Fixed CSV is now recognized as points data")
                        else:
                            print("Fixed CSV still not recognized as points data")
                    else:
                        print("Failed to fix CSV file using fix_csv_for_ai_engine")
                except ImportError:
                    print("fix_csv_for_ai_engine module not found, falling back to manual fixes")
                except Exception as e:
                    print(f"Error using fix_csv_for_ai_engine: {str(e)}")
                    print("Falling back to manual fixes")
        
        # If the CSV still doesn't have the right structure, apply manual fixes
        if not is_points_data:
            print("\n=== APPLYING MANUAL FIXES TO CSV FORMAT ===")
            
            # 1. Fix column name mismatches
            column_mappings = {
                'objectInst': 'objectInstance',  # This is the critical one for dashboard recognition
            }
            
            for old_col, new_col in column_mappings.items():
                if old_col in df.columns and new_col not in df.columns:
                    print(f"Renaming column: {old_col} -> {new_col}")
                    df = df.rename(columns={old_col: new_col})
            
            # 2. Add required columns for AI processing
            if 'objectName' in df.columns and 'pointName' not in df.columns:
                print("Adding pointName column (mapped from objectName)")
                df['pointName'] = df['objectName']
            
            if 'objectType' in df.columns and 'pointType' not in df.columns:
                print("Adding pointType column (mapped from objectType)")
                df['pointType'] = df['objectType']
            
            # 3. Fill null values in description field
            if 'description' in df.columns:
                null_count = df['description'].isnull().sum()
                if null_count > 0:
                    print(f"Filling {null_count} null values in description column")
                    # Create a new DataFrame to avoid null value issues
                    rows = []
                    for _, row in df.iterrows():
                        new_row = {}
                        for col in df.columns:
                            if col == 'description' and pd.isna(row[col]):
                                new_row[col] = ''  # Empty string for description
                            else:
                                new_row[col] = row[col]
                        rows.append(new_row)
                    
                    df = pd.DataFrame(rows)
            
            # 4. Add source column
            print("Adding source column")
            df['source'] = 'bacnet'
            
            # 5. Add pointId column
            print("Adding pointId column")
            if 'deviceInstance' in df.columns and 'objectInstance' in df.columns:
                df['pointId'] = df.apply(lambda row: f"{row['deviceInstance']}:{row['objectInstance']}", axis=1)
            
            # Save the converted file with a different name to avoid permission issues
            base_name = os.path.basename(points_file)
            dir_name = os.path.dirname(points_file)
            ai_file_path = os.path.join(dir_name, f"ai_ready_{base_name}")
            
            # Use na_rep to ensure null values are written as empty strings
            df.to_csv(ai_file_path, index=False, na_rep='')
            print(f"Converted file saved to: {ai_file_path}")
            
            # Update points_file to use the fixed version
            points_file = ai_file_path
        
        # Now attempt to run the actual AI mapping with the converted file
        print("\n=== ATTEMPTING AI MAPPING WITH CONVERTED FILE ===")
        print(f"Using file: {points_file}")
        
        # This is a placeholder - the actual implementation would depend on how the AI mapping is done
        # In a real implementation, you would call the AI mapping functionality here
        
        return {
            "code": 0,
            "message": "AI mapping diagnostics and conversion complete",
            "converted_file": points_file
        }
        
    except Exception as e:
        print(f"Error analyzing or converting points file: {str(e)}")
        traceback.print_exc()
        return {"code": 1, "msg": str(e)}

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