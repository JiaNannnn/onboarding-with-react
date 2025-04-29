"""
BACnet Utility Module

This module provides utility functions for BACnet communications by
interfacing with the EnOS API via the poseidon client.
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from ..core.config import settings
from .poseidon import urlopen

# Set up logging
logger = logging.getLogger(__name__)

def connect_to_bacnet(
    interface: str = "eth0", 
    ip_address: Optional[str] = None
) -> bool:
    """
    Connect to the BACnet network through the specified interface.
    
    Args:
        interface: Network interface to use for BACnet communication
        ip_address: Optional IP address for BACnet/IP
        
    Returns:
        True if connection was successful, False otherwise
    """
    logger.info(f"Connecting to BACnet network via {interface}")
    # This is a placeholder since actual BACnet connection is handled by the API
    return True


def discover_networks(asset_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Discover BACnet networks.
    
    Args:
        asset_id: Optional asset ID to filter networks
        
    Returns:
        List of discovered networks
    """
    logger.info(f"Discovering BACnet networks for asset_id={asset_id}")
    
    # Following the pattern from BMSDataPoints.py's getNetConfig function
    url = f"{settings.ENOS_API_URL}/enos-edge/v2.4/discovery/getNetConfig"
    
    data = {
        "orgId": settings.ENOS_ORG_ID
    }
    if asset_id:
        data["assetId"] = asset_id
    
    try:
        logger.info(f"Network discovery request to: {url}")
        response = urlopen(
            settings.ENOS_ACCESS_KEY, 
            settings.ENOS_SECRET_KEY, 
            url, 
            data
        )
        
        # Check for success response
        if response.get('code') == 0:
            networks = []
            # Extract networks from the response based on BMSDataPoints.py pattern
            if ('data' in response and 
                isinstance(response['data'], list)):
                for network in response['data']:
                    networks.append({
                        "id": network.get('netId', f"net-{len(networks)+1}"),
                        "name": network.get('netName', 'Unnamed Network'),
                        "description": network.get('description', 'No description')
                    })
            return networks
        else:
            logger.error(f"Error discovering networks: {response.get('msg', 'Unknown error')}")
            return []
    except Exception as e:
        logger.exception(f"Exception during network discovery: {str(e)}")
        return []


def scan_devices(
    network_id: str,
    asset_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Scan for devices on a BACnet network.
    
    Args:
        network_id: Network ID to scan
        asset_id: Optional asset ID to filter results
        
    Returns:
        List of discovered devices
    """
    logger.info(f"Scanning for devices on network {network_id} for asset_id={asset_id}")
    
    # Following the pattern from BMSDataPoints.py's searchDevice function
    url = f"{settings.ENOS_API_URL}/enos-edge/v2.4/discovery/search"
    
    # Prepare request data
    data = {
        "orgId": settings.ENOS_ORG_ID,
        "net": network_id,
        "type": "device",
        "protocol": "bacnet"
    }
    
    if asset_id:
        data["assetId"] = asset_id
    
    try:
        logger.info(f"Device scan request to: {url}")
        logger.info(f"Request data: {json.dumps(data, indent=2)}")
        
        response = urlopen(
            settings.ENOS_ACCESS_KEY, 
            settings.ENOS_SECRET_KEY, 
            url, 
            data
        )
        
        # Check for successful scan initiation
        if response.get('code') == 0 and response.get('data') is True:
            logger.info("Device scan initiated successfully, fetching results...")
            
            # Wait a moment for the scan to start
            time.sleep(5)
            
            # Now fetch the actual device list using deviceResponse endpoint
            deviceResponse_url = f"{settings.ENOS_API_URL}/enos-edge/v2.4/discovery/deviceResponse"
            deviceResponse_data = {
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
                    asset_id
                ],
                "orgId": settings.ENOS_ORG_ID
            }
            
            if asset_id:
                deviceResponse_data["assetIds"] = [asset_id]
                
            # Set up polling for device results
            max_attempts = 30
            poll_interval = 10
            attempt = 1
            
            while attempt <= max_attempts:
                fetch_response = urlopen(
                    settings.ENOS_ACCESS_KEY, 
                    settings.ENOS_SECRET_KEY, 
                    deviceResponse_url, 
                    deviceResponse_data
                )
                
                # Check for complete results
                if ('data' in fetch_response and
                    isinstance(fetch_response['data'], dict) and
                    'record' in fetch_response['data'] and
                    isinstance(fetch_response['data']['record'], list)):
                    
                    devices = fetch_response['data']['record']
                    if len(devices) > 0:
                        # Format the discovered devices
                        formatted_devices = []
                        for device in devices:
                            formatted_devices.append({
                                "id": device.get('deviceId', f"dev-{len(formatted_devices)+1}"),
                                "name": device.get('deviceName', 'Unnamed Device'),
                                "address": device.get('address', 'Unknown'),
                                "instance": device.get('otDeviceInst', 'Unknown'),
                                "model": device.get('modelName', None),
                                "vendor": device.get('vendorName', None),
                                "network": network_id,
                                "asset_id": asset_id
                            })
                        return formatted_devices
                
                # If not complete, wait and try again
                logger.info(f"Device scan in progress. Polling attempt {attempt}/{max_attempts}")
                time.sleep(poll_interval)
                attempt += 1
            
            # If we get here, polling timed out
            logger.error(f"Device scan timed out after {max_attempts * poll_interval} seconds")
            return []
            
        else:
            logger.error(f"Error initiating device scan: {response.get('msg', 'Unknown error')}")
            return []
    except Exception as e:
        logger.exception(f"Exception during device scan: {str(e)}")
        return []


def get_device_points(
    asset_id: str,
    device_instance: str
) -> List[Dict[str, Any]]:
    """
    Get all points from a BACnet device.
    
    Args:
        asset_id: Asset ID associated with the device
        device_instance: BACnet device instance
        
    Returns:
        List of BACnet points for the device
    """
    logger.info(f"Getting points for device {device_instance} for asset_id={asset_id}")
    
    # Following the pattern from BMSDataPoints.py's fetchPoints function
    url = f"{settings.ENOS_API_URL}/enos-edge/v2.4/discovery/pointResponse"
    
    data = {
        "orgId": settings.ENOS_ORG_ID,
        "assetId": asset_id,
        "protocol": "bacnet",
        "otDeviceInst": device_instance
    }
    
    logger.info(f"Points retrieval request to: {url}")
    logger.info(f"Request data: {json.dumps(data, indent=2)}")
    
    # Set up polling parameters (as seen in BMSDataPoints.py)
    max_attempts = 30  # Maximum number of polling attempts
    poll_interval = 10  # Seconds between polls
    
    try:
        # Initial request to retrieve points
        response = urlopen(
            settings.ENOS_ACCESS_KEY, 
            settings.ENOS_SECRET_KEY, 
            url, 
            data
        )
        logger.info(f"Initial points retrieval response code: {response.get('code', 'Unknown')}")
        
        # Check if we need to poll for results
        attempt = 1
        while attempt <= max_attempts:
            # Check for complete response
            points_data = []
            
            # Check for two possible response structures (as in BMSDataPoints.py)
            if ('data' in response and
                isinstance(response['data'], dict) and
                'record' in response['data'] and
                isinstance(response['data']['record'], list)):
                points_data = response['data']['record']
            elif ('data' in response and
                isinstance(response['data'], list)):
                points_data = response['data']
                
            if points_data and len(points_data) > 0:
                logger.info(f"Points retrieval complete for device {device_instance}! Found {len(points_data)} points.")
                
                # Format the points data according to our API structure
                formatted_points = []
                for point in points_data:
                    formatted_points.append({
                        "name": point.get('pointName', point.get('objectName', 'Unnamed Point')),
                        "description": point.get('description', None),
                        "object_type": point.get('objectType', 'unknown'),
                        "object_id": point.get('objectId', 0),
                        "present_value": point.get('presentValue', None),
                        "units": point.get('units', None),
                        "instance": f"{device_instance}:{point.get('objectType', '')}:{point.get('objectId', '')}"
                    })
                
                return formatted_points
            
            # If not complete, wait and poll again
            logger.info(f"Points retrieval not complete. Polling attempt {attempt}/{max_attempts}...")
            time.sleep(poll_interval)
            attempt += 1
            
            # Make another request
            response = urlopen(
                settings.ENOS_ACCESS_KEY, 
                settings.ENOS_SECRET_KEY, 
                url, 
                data
            )
        
        # If we got here, polling timed out
        logger.error(f"Points retrieval timed out for device {device_instance} after {max_attempts} attempts")
        return []
    
    except Exception as e:
        logger.exception(f"Exception during points retrieval: {str(e)}")
        return []


def discover_device_points(
    asset_id: str,
    device_instances: List[str]
) -> List[Dict[str, Any]]:
    """
    Discover points on BACnet devices.
    
    Args:
        asset_id: Asset ID associated with the devices
        device_instances: List of BACnet device instances
        
    Returns:
        List of discovered BACnet points
    """
    logger.info(f"Discovering points for devices {device_instances} for asset_id={asset_id}")
    
    # Following the pattern from BMSDataPoints.py's search_points function
    url = f"{settings.ENOS_API_URL}/enos-edge/v2.4/discovery/search"
    
    data = {
        "orgId": settings.ENOS_ORG_ID,
        "assetId": asset_id,
        "protocol": "bacnet",
        "type": "point",
        "otDeviceInstList": device_instances
    }
    
    logger.info(f"Point discovery request to: {url}")
    logger.info(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        response = urlopen(
            settings.ENOS_ACCESS_KEY, 
            settings.ENOS_SECRET_KEY, 
            url, 
            data
        )
        
        # Check if the search was successfully initiated
        if response.get('code') == 0 and response.get('data') is True:
            logger.info(f"Points search initiated successfully for {len(device_instances)} devices")
            
            # Wait for the search to start processing
            time.sleep(5)
            
            # Now fetch points for each device using the fetchPoints function logic
            all_points = []
            
            for device_instance in device_instances:
                device_points = get_device_points(asset_id, device_instance)
                # Add device instance to each point
                for point in device_points:
                    point["device_instance"] = device_instance
                all_points.extend(device_points)
            
            return all_points
        else:
            error_msg = response.get('msg', 'Unknown error')
            logger.error(f"Points search initiation failed: {error_msg}")
            return []
            
    except Exception as e:
        logger.exception(f"Exception during point discovery: {str(e)}")
        return []


def read_point_value(
    asset_id: str,
    device_instance: str,
    point_instance: str
) -> Dict[str, Any]:
    """
    Read current value of a BACnet point.
    
    Args:
        asset_id: Asset ID associated with the device
        device_instance: BACnet device instance
        point_instance: BACnet point instance
        
    Returns:
        Current value and details of the BACnet point
    """
    logger.info(f"Reading point {point_instance} on device {device_instance}")
    
    # Extract object type and ID from point_instance
    parts = point_instance.split(":")
    if len(parts) < 3:
        raise ValueError(f"Invalid point instance format: {point_instance}")
    
    object_type = parts[1]
    object_id = parts[2]
    
    # Following a similar pattern to fetchPoints but for a single point
    url = f"{settings.ENOS_API_URL}/enos-edge/v2.4/discovery/pointValue"
    
    data = {
        "orgId": settings.ENOS_ORG_ID,
        "assetId": asset_id,
        "otDeviceInst": device_instance,
        "objectType": object_type,
        "objectId": object_id
    }
    
    logger.info(f"Point value read request to: {url}")
    logger.info(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        response = urlopen(
            settings.ENOS_ACCESS_KEY, 
            settings.ENOS_SECRET_KEY, 
            url, 
            data
        )
        
        if response.get('code') == 0 and 'data' in response:
            point_data = response['data']
            
            # Format the point data
            return {
                "name": point_data.get('pointName', 'Unnamed Point'),
                "description": point_data.get('description', None),
                "object_type": object_type,
                "object_id": int(object_id) if object_id.isdigit() else object_id,
                "present_value": point_data.get('presentValue', None),
                "units": point_data.get('units', None),
                "instance": point_instance
            }
        else:
            logger.error(f"Error reading point value: {response.get('msg', 'Unknown error')}")
            raise ValueError(f"Failed to read point value: {response.get('msg', 'Unknown error')}")
            
    except Exception as e:
        logger.exception(f"Exception during point value read: {str(e)}")
        raise


def write_point_value(
    asset_id: str,
    device_instance: str,
    point_instance: str,
    value: Any,
    priority: Optional[int] = None
) -> Dict[str, Any]:
    """
    Write a value to a BACnet point.
    
    Args:
        asset_id: Asset ID associated with the device
        device_instance: BACnet device instance
        point_instance: BACnet point instance
        value: Value to write
        priority: Optional priority level (1-16, with 1 being highest)
        
    Returns:
        Updated point data after write operation
    """
    logger.info(f"Writing value {value} to point {point_instance} on device {device_instance}")
    
    # Extract object type and ID from point_instance
    parts = point_instance.split(":")
    if len(parts) < 3:
        raise ValueError(f"Invalid point instance format: {point_instance}")
    
    object_type = parts[1]
    object_id = parts[2]
    
    # Following the pattern of a write operation
    url = f"{settings.ENOS_API_URL}/enos-edge/v2.4/control/writePointValue"
    
    data = {
        "orgId": settings.ENOS_ORG_ID,
        "assetId": asset_id,
        "otDeviceInst": device_instance,
        "objectType": object_type,
        "objectId": object_id,
        "writeValue": value
    }
    
    # Add priority if specified
    if priority is not None:
        data["priority"] = priority
    
    logger.info(f"Point value write request to: {url}")
    logger.info(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        response = urlopen(
            settings.ENOS_ACCESS_KEY, 
            settings.ENOS_SECRET_KEY, 
            url, 
            data
        )
        
        if response.get('code') == 0:
            # After writing, read the point value to confirm and return updated data
            return read_point_value(asset_id, device_instance, point_instance)
        else:
            logger.error(f"Error writing point value: {response.get('msg', 'Unknown error')}")
            raise ValueError(f"Failed to write point value: {response.get('msg', 'Unknown error')}")
            
    except Exception as e:
        logger.exception(f"Exception during point value write: {str(e)}")
        raise 