"""
BMS Service

This module provides a service layer for BMS operations by wrapping the
EnOS API calls and providing a clean interface for the controllers.
"""

import os
import json
import time
import uuid
from datetime import datetime
import re
import pandas as pd
from flask import current_app
import traceback

# Import poseidon if available
try:
    from poseidon import poseidon
except ImportError:
    poseidon = None
    current_app.logger.warning("Poseidon library not found. Using mock data for BMS operations.")

class BMSService:
    """Service for BMS operations"""
    
    def __init__(self):
        """Initialize the service"""
        # Create results directory if needed
        self.results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                       "bms", "results")
        os.makedirs(self.results_dir, exist_ok=True)
    
    def get_network_config(self, api_url, access_key, secret_key, org_id, asset_id):
        """
        Get network configuration from the EnOS API.
        
        Args:
            api_url: The EnOS API URL
            access_key: EnOS access key
            secret_key: EnOS secret key
            org_id: Organization ID
            asset_id: Asset ID
        
        Returns:
            The API response containing network configuration.
        """
        # Verify poseidon library is available for API calls
        if poseidon is None:
            current_app.logger.error("Poseidon library not available")
            return {"status": "error", "message": "EnOS API client not available"}
        
        # API URL with the appropriate asset ID
        url = f"{api_url}/enos-edge/v2.4/discovery/getNetConfig?orgId={org_id}&assetId={asset_id}"
        
        try:
            # Call the API
            current_app.logger.info(f"Fetching network configuration for asset ID: {asset_id}")
            current_app.logger.debug(f"Request URL: {url}")
            response = poseidon.urlopen(access_key, secret_key, url)
            
            # Check if response has data field with options
            if 'data' in response and isinstance(response['data'], list) and len(response['data']) > 0:
                current_app.logger.info(f"Found {len(response['data'])} network options for asset ID {asset_id}")
                
                return {
                    "status": "success",
                    "networks": response['data']
                }
            else:
                current_app.logger.warning(f"No network options found for asset ID {asset_id}")
                return {
                    "status": "success", 
                    "networks": [],
                    "message": f"No network options found for asset ID {asset_id}"
                }
        except Exception as e:
            current_app.logger.error(f"Error getting network configuration: {str(e)}")
            traceback.print_exc()
            return {
                "status": "error",
                "message": str(e)
            }
    
    def discover_devices(self, api_url, access_key, secret_key, org_id, asset_id, networks, protocol='bacnet'):
        """
        Discover devices on the specified networks.
        
        Args:
            api_url: The EnOS API URL
            access_key: EnOS access key
            secret_key: EnOS secret key
            org_id: Organization ID
            asset_id: Asset ID
            networks: List of networks to search on
            protocol: Protocol to use (default: bacnet)
            
        Returns:
            Dictionary with task ID and results when completed
        """
        if current_app.config.get('TESTING', False) or current_app.config.get('DEBUG', False):
            # Return mock data for testing/development
            task_id = f"discovery-{str(uuid.uuid4())[:8]}"
            return {
                "status": "processing",
                "taskId": task_id,
                "message": "Device discovery initiated on mock networks"
            }
        
        # Verify poseidon library is available for API calls    
        if poseidon is None:
            current_app.logger.error("Poseidon library not available")
            return {"status": "error", "message": "EnOS API client not available"}
            
        if not networks:
            current_app.logger.error("No networks specified for device discovery")
            return {"status": "error", "message": "No networks specified"}
        
        # Search for devices on each network
        results = {}
        all_devices = []
        task_id = f"discovery-{str(uuid.uuid4())[:8]}"
        
        for net in networks:
            current_app.logger.info(f"Searching for devices on network: {net}")
            search_result = self._search_device(api_url, access_key, secret_key, org_id, asset_id, net, protocol)
            results[net] = search_result
            
            # Extract devices if available
            if (search_result and "result" in search_result and 
                "deviceList" in search_result["result"] and 
                isinstance(search_result["result"]["deviceList"], list)):
                devices = search_result["result"]["deviceList"]
                all_devices.extend(devices)
                current_app.logger.info(f"Found {len(devices)} devices on network {net}")
        
        # Save results to a file for later reference
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"devices_{asset_id}_{timestamp}.json"
        filepath = os.path.join(self.results_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "taskId": task_id,
                    "timestamp": timestamp,
                    "results": results,
                    "all_devices": all_devices,
                    "count": len(all_devices)
                }, f, indent=2)
            current_app.logger.info(f"Saved device discovery results to {filepath}")
        except Exception as e:
            current_app.logger.error(f"Error saving discovery results: {str(e)}")
        
        return {
            "status": "success",
            "taskId": task_id,
            "message": f"Device discovery completed. Found {len(all_devices)} devices across {len(networks)} networks."
        }
    
    def get_device_discovery_status(self, task_id):
        """
        Get the status of a device discovery task.
        
        Args:
            task_id: The task ID from a previous discover_devices call
            
        Returns:
            Dictionary with status and device information
        """
        if current_app.config.get('TESTING', False) or current_app.config.get('DEBUG', False):
            # Return mock data for testing/development
            return {
                "status": "completed",
                "result": {
                    "devices": [
                        {
                            "instanceNumber": 1001,
                            "name": "Device 1001",
                            "address": "192.168.1.101",
                            "model": "Virtual BACnet Device",
                            "vendor": "ACME Controls"
                        },
                        {
                            "instanceNumber": 1002,
                            "name": "Device 1002",
                            "address": "192.168.1.102",
                            "model": "Virtual BACnet Device",
                            "vendor": "ACME Controls"
                        }
                    ],
                    "count": 2
                }
            }
        
        # Look for file containing task results
        files = os.listdir(self.results_dir)
        for file in files:
            if file.startswith("devices_") and file.endswith(".json"):
                try:
                    with open(os.path.join(self.results_dir, file), 'r') as f:
                        data = json.load(f)
                        if data.get("taskId") == task_id:
                            # Found the task results
                            devices = []
                            for device in data.get("all_devices", []):
                                devices.append({
                                    "instanceNumber": device.get("otDeviceInst"),
                                    "name": device.get("deviceName", f"Device {device.get('otDeviceInst')}"),
                                    "address": device.get("address", "unknown"),
                                    "model": device.get("model", "unknown"),
                                    "vendor": device.get("vendor", "unknown")
                                })
                            
                            return {
                                "status": "completed",
                                "result": {
                                    "devices": devices,
                                    "count": len(devices)
                                }
                            }
                except Exception as e:
                    current_app.logger.error(f"Error reading discovery results: {str(e)}")
        
        # If task not found, return pending status
        return {
            "status": "pending",
            "message": f"Task {task_id} is still in progress or not found"
        }
    
    def get_device_points(self, api_url, access_key, secret_key, org_id, asset_id, 
                          device_instance, device_address="unknown-ip", protocol="bacnet"):
        """
        Fetch points for a specific device.
        
        Args:
            api_url: The EnOS API URL
            access_key: EnOS access key
            secret_key: EnOS secret key
            org_id: Organization ID
            asset_id: Asset ID
            device_instance: The device instance number
            device_address: Device IP address (optional)
            protocol: Protocol to use (default: bacnet)
            
        Returns:
            Dictionary with task ID and status
        """
        if current_app.config.get('TESTING', False) or current_app.config.get('DEBUG', False):
            # Return mock data for testing/development
            task_id = f"points-{str(uuid.uuid4())[:8]}"
            return {
                "status": "processing",
                "taskId": task_id,
                "message": f"Fetching points for device {device_instance}"
            }
        
        # Verify poseidon library is available for API calls
        if poseidon is None:
            current_app.logger.error("Poseidon library not available")
            return {"status": "error", "message": "EnOS API client not available"}
            
        task_id = f"points-{device_instance}-{str(uuid.uuid4())[:8]}"
        
        # Initiate the search in a background process (would normally use Celery)
        # For now we'll just start the process and return a task ID
        
        try:
            # Log the request
            current_app.logger.info(f"Initiating points search for device {device_instance}")
            
            # Initialize the points search
            search_result = self._search_points(api_url, access_key, secret_key, org_id, 
                                              asset_id, [device_instance], protocol)
            
            if search_result.get("status") == "error":
                return search_result
            
            return {
                "status": "processing",
                "taskId": task_id,
                "message": f"Fetching points for device {device_instance}"
            }
            
        except Exception as e:
            current_app.logger.error(f"Error initiating points search: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_device_points_status(self, task_id):
        """
        Get status of a device points task.
        
        Args:
            task_id: The task ID
            
        Returns:
            Dictionary with status and points information
        """
        if current_app.config.get('TESTING', False) or current_app.config.get('DEBUG', False):
            # Return mock data for testing/development
            return {
                "status": "success",
                "pointCount": 15,
                "samplePoints": [
                    {"name": "AnalogInput1", "value": 72.5, "units": "degF"},
                    {"name": "AnalogOutput1", "value": 50.0, "units": "%"},
                    {"name": "BinaryInput1", "value": "On", "units": None},
                    {"name": "BinaryOutput1", "value": "Off", "units": None},
                    {"name": "MultiStateInput1", "value": "Stage 2", "units": None}
                ]
            }
        
        # In a real implementation, we would check a database or task queue
        # For now, return mock data
        return {
            "status": "success",
            "pointCount": 15,
            "samplePoints": [
                {"name": "AnalogInput1", "value": 72.5, "units": "degF"},
                {"name": "AnalogOutput1", "value": 50.0, "units": "%"},
                {"name": "BinaryInput1", "value": "On", "units": None},
                {"name": "BinaryOutput1", "value": "Off", "units": None},
                {"name": "MultiStateInput1", "value": "Stage 2", "units": None}
            ]
        }
    
    def search_points(self, api_url, access_key, secret_key, org_id, asset_id, device_ids, protocol="bacnet"):
        """
        Search for points across multiple devices.
        
        Args:
            api_url: The EnOS API URL
            access_key: EnOS access key
            secret_key: EnOS secret key
            org_id: Organization ID
            asset_id: Asset ID
            device_ids: List of device IDs to search
            protocol: Protocol to use (default: bacnet)
            
        Returns:
            Dictionary with task ID and status
        """
        if current_app.config.get('TESTING', False) or current_app.config.get('DEBUG', False):
            # Return mock data for testing/development
            task_id = f"search-{str(uuid.uuid4())[:8]}"
            return {
                "status": "processing",
                "taskId": task_id,
                "message": "Points search initiated"
            }
        
        # Verify poseidon library is available for API calls
        if poseidon is None:
            current_app.logger.error("Poseidon library not available")
            return {"status": "error", "message": "EnOS API client not available"}
            
        if not device_ids:
            current_app.logger.error("No device IDs specified for points search")
            return {"status": "error", "message": "No device IDs specified"}
            
        task_id = f"search-{str(uuid.uuid4())[:8]}"
        
        try:
            # Initialize the points search
            search_result = self._search_points(api_url, access_key, secret_key, org_id, 
                                             asset_id, device_ids, protocol)
            
            if search_result.get("status") == "error":
                return search_result
            
            return {
                "status": "processing",
                "taskId": task_id,
                "message": f"Points search initiated for {len(device_ids)} devices"
            }
            
        except Exception as e:
            current_app.logger.error(f"Error initiating points search: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def group_points_with_strategy(self, points, strategy="ai", model=None):
        """
        Group points using the specified strategy.
        
        Args:
            points: List of point objects with pointName, pointType, etc.
            strategy: Grouping strategy ('default', 'ai', or 'ontology')
            model: Optional AI model name to use (for 'ai' strategy)
            
        Returns:
            Dictionary with grouped points
        """
        current_app.logger.info(f"Grouping {len(points)} points using '{strategy}' strategy")
        
        # Extract point names for grouping
        point_names = [p.get('pointName', '') for p in points if p.get('pointName')]
        if not point_names:
            current_app.logger.warning("No valid point names found for grouping")
            return {
                "success": False,
                "error": "No valid point names found for grouping"
            }
            
        try:
            # Initialize the DeviceGrouper
            from app.bms.grouping import DeviceGrouper
            grouper = DeviceGrouper()
            
            # Override model if provided and we're using AI strategy
            if strategy == 'ai' and model:
                grouper.model = model
                current_app.logger.info(f"Using custom model for AI grouping: {model}")
            
            # Use appropriate grouping strategy
            if strategy == 'default':
                current_app.logger.info("Using default grouping strategy")
                grouped_points = grouper._fallback_grouping(point_names, use_ontology=False)
            elif strategy == 'ontology':
                current_app.logger.info("Using ontology-based grouping strategy")
                grouped_points = grouper._fallback_grouping(point_names, use_ontology=True)
            else:
                # Default to AI grouping
                current_app.logger.info("Using AI-assisted grouping strategy")
                grouped_points = grouper.process(point_names)
            
            # Convert grouped points to the expected response format
            result_groups = {}
            equipment_types = 0
            equipment_instances = 0
            
            for device_type, devices in grouped_points.items():
                equipment_types += 1
                equipment_instances += len(devices)
                
                for device_id, device_points in devices.items():
                    group_id = f"{device_type}_{device_id}"
                    
                    # Find the full point objects for each point name
                    group_points = []
                    for point_name in device_points:
                        matching_points = [p for p in points if p.get('pointName') == point_name]
                        if matching_points:
                            group_points.extend(matching_points)
                    
                    result_groups[group_id] = {
                        "id": group_id,
                        "name": f"{device_type} {device_id}",
                        "description": f"Auto-generated group for {device_type} {device_id}",
                        "points": group_points,
                        "subgroups": {}
                    }
            
            # Return the success response
            return {
                "success": True,
                "grouped_points": result_groups,
                "stats": {
                    "total_points": len(points),
                    "equipment_types": equipment_types,
                    "equipment_instances": equipment_instances
                },
                "method": strategy
            }
            
        except Exception as e:
            current_app.logger.error(f"Error in grouping points: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Failed to group points: {str(e)}"
            }
    
    # Private methods for internal use
    
    def _search_device(self, api_url, access_key, secret_key, org_id, asset_id, network, protocol="bacnet"):
        """
        Private method to search for devices on a network.
        
        Args:
            api_url: The EnOS API URL
            access_key: EnOS access key
            secret_key: EnOS secret key
            org_id: Organization ID
            asset_id: Asset ID
            network: Network to search
            protocol: Protocol to use (default: bacnet)
            
        Returns:
            The API response from the search request
        """
        # API URL for device search
        url = f"{api_url}/enos-edge/v2.4/discovery/search"
        
        data = {
            "orgId": org_id,
            "assetId": asset_id,
            "net": network,
            "type": "device",
            "protocol": protocol
        }
        
        try:
            # Call the API
            current_app.logger.info(f"Initiating device discovery on network {network}")
            current_app.logger.debug(f"Search request data: {data}")
            
            # Initialize the search
            response = poseidon.urlopen(access_key, secret_key, url, data)
            
            # Check if the search request was successful
            if 'code' in response and response['code'] == 0:
                data_value = response.get('data')
                
                # Check for success response
                if data_value is True:
                    current_app.logger.info("Discovery initiated successfully. Retrieving devices...")
                    # Allow time for the discovery process
                    time.sleep(5)
                    return self._fetch_device(api_url, access_key, secret_key, org_id, asset_id)
                else:
                    current_app.logger.warning(f"Discovery failed or returned unexpected result: {data_value}")
            else:
                error_msg = response.get('msg', 'Unknown error')
                current_app.logger.error(f"Error during discovery: {error_msg}")
            
            return response
        except Exception as e:
            current_app.logger.error(f"Error during device discovery: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
    
    def _fetch_device(self, api_url, access_key, secret_key, org_id, asset_id):
        """
        Private method to fetch discovered devices.
        
        Args:
            api_url: The EnOS API URL
            access_key: EnOS access key
            secret_key: EnOS secret key
            org_id: Organization ID
            asset_id: Asset ID
            
        Returns:
            The API response containing discovered devices
        """
        url = f"{api_url}/enos-edge/v2.4/discovery/deviceResponse"
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
                "pageSize": 100  # increased for better results
            },
            "assetIds": [
                asset_id
            ],
            "orgId": org_id
        }
        
        current_app.logger.info(f"Fetching discovered devices for asset {asset_id}")
        
        # Set up polling parameters
        max_attempts = 30
        poll_interval = 10
        
        # First request to get the scan results
        response = poseidon.urlopen(access_key, secret_key, url, data)
        
        # Check if we need to wait for results
        attempt = 1
        while attempt <= max_attempts:
            # Check if scan is complete with proper structure
            if ('data' in response and
                isinstance(response['data'], dict) and
                'record' in response['data'] and
                isinstance(response['data']['record'], list)):
                
                devices = response['data']['record']
                if len(devices) > 0:
                    current_app.logger.info(f"Scan complete! Found {len(devices)} devices")
                    
                    # Return the devices in a standardized format
                    result = {
                        "status": "success",
                        "result": {
                            "deviceList": devices
                        }
                    }
                    
                    return result
                
                # No devices found yet
                current_app.logger.info(f"No devices found yet (Attempt {attempt}/{max_attempts})")
                attempt += 1
                
                if attempt <= max_attempts:
                    time.sleep(poll_interval)
                    response = poseidon.urlopen(access_key, secret_key, url, data)
            else:
                # Wait for the scanning to complete
                current_app.logger.info(f"Scanning in progress (Attempt {attempt}/{max_attempts})")
                attempt += 1
                
                if attempt <= max_attempts:
                    time.sleep(poll_interval)
                    response = poseidon.urlopen(access_key, secret_key, url, data)
        
        # If we get here, polling timed out
        current_app.logger.warning(f"Device scan timed out after {max_attempts * poll_interval} seconds")
        return {"status": "error", "message": "Device scan timed out"}
    
    def _search_points(self, api_url, access_key, secret_key, org_id, asset_id, device_instances, protocol="bacnet"):
        """
        Private method to search for points on devices.
        
        Args:
            api_url: The EnOS API URL
            access_key: EnOS access key
            secret_key: EnOS secret key
            org_id: Organization ID
            asset_id: Asset ID
            device_instances: List of device instance numbers
            protocol: Protocol to use (default: bacnet)
            
        Returns:
            Status of the points search initiation
        """
        url = f"{api_url}/enos-edge/v2.4/discovery/search"
        
        data = {
            "orgId": org_id,
            "assetId": asset_id,
            "protocol": protocol,
            "type": "point",
            "otDeviceInstList": device_instances
        }
        
        current_app.logger.info(f"Initiating points search for {len(device_instances)} devices")
        
        try:
            # Call the API to start the points search
            response = poseidon.urlopen(access_key, secret_key, url, data)
            
            # Check if the search was successfully initiated
            if 'code' in response and response['code'] == 0:
                data_value = response.get('data')
                
                if data_value is True:
                    current_app.logger.info(f"Points search initiated successfully for {len(device_instances)} devices")
                    return {"status": "success", "message": "Points search initiated successfully"}
                else:
                    current_app.logger.warning(f"Points search initiation failed with unexpected result: {data_value}")
                    return {"status": "error", "message": f"Points search initiation failed: {data_value}"}
            else:
                error_msg = response.get('msg', 'Unknown error')
                current_app.logger.error(f"Points search initiation failed: {error_msg}")
                return {"status": "error", "message": f"Points search initiation failed: {error_msg}"}
        except Exception as e:
            current_app.logger.error(f"Error initiating points search: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
    
    def _fetch_points(self, api_url, access_key, secret_key, org_id, asset_id, device_instance, 
                     device_address="unknown-ip", protocol="bacnet"):
        """
        Private method to fetch points for a device.
        
        Args:
            api_url: The EnOS API URL
            access_key: EnOS access key
            secret_key: EnOS secret key
            org_id: Organization ID
            asset_id: Asset ID
            device_instance: Device instance number
            device_address: Device IP address (optional)
            protocol: Protocol to use (default: bacnet)
            
        Returns:
            The points data for the device
        """
        url = f"{api_url}/enos-edge/v2.4/discovery/pointResponse"
        
        data = {
            "orgId": org_id,
            "assetId": asset_id,
            "protocol": protocol,
            "otDeviceInst": device_instance
        }
        
        current_app.logger.info(f"Retrieving points for device instance {device_instance} at {device_address}")
        
        # Set up polling parameters
        max_attempts = 30
        poll_interval = 10
        
        try:
            # First request to initiate points retrieval
            response = poseidon.urlopen(access_key, secret_key, url, data)
            
            # Check if we need to wait for results
            attempt = 1
            while attempt <= max_attempts:
                # Check if points retrieval is complete
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
                    current_app.logger.info(f"Points retrieval complete for device {device_instance}! Found {len(points_data)} points")
                    
                    # Create a timestamp for the filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # Sanitize the device address for filename
                    sanitized_address = re.sub(r'[^\w\-\.]', '_', device_address)
                    file_name = f"points_{asset_id}_{device_instance}_{sanitized_address}_{timestamp}.json"
                    full_path = os.path.join(self.results_dir, file_name)
                    
                    try:
                        with open(full_path, 'w') as f:
                            json.dump(points_data, f, indent=2)
                        current_app.logger.info(f"Points data saved to {full_path}")
                    except Exception as e:
                        current_app.logger.error(f"Error saving points data: {str(e)}")
                    
                    return {
                        "status": "success",
                        "point_count": len(points_data),
                        "file_path": full_path,
                        "sample_points": points_data[:5] if len(points_data) > 5 else points_data
                    }
                
                # If not complete or no points found yet
                current_app.logger.info(f"Points retrieval in progress for device {device_instance} (Attempt {attempt}/{max_attempts})")
                attempt += 1
                
                if attempt <= max_attempts:
                    time.sleep(poll_interval)
                    response = poseidon.urlopen(access_key, secret_key, url, data)
            
            # If we get here, polling timed out
            current_app.logger.warning(f"Points retrieval timed out for device {device_instance}")
            return {"status": "error", "message": "Points retrieval timed out"}
            
        except Exception as e:
            current_app.logger.error(f"Error during points retrieval: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
        
    def map_bms_points(self, points, target_schema='default', matching_strategy='ai', confidence_threshold=0.7):
        """
        Map BMS points to EnOS equipment models following specified schema.
        
        Args:
            points: List of BMS points to map
            target_schema: The target schema/model to map to (default or custom)
            matching_strategy: Strategy for mapping ('ai', 'rule', 'hybrid')
            confidence_threshold: Minimum confidence threshold for mappings
            
        Returns:
            Dictionary with mapping results
        """
        current_app.logger.info(f"Mapping {len(points)} points to EnOS models using '{matching_strategy}' strategy")
        
        # Validate input points
        if not points:
            current_app.logger.warning("No points provided for mapping")
            return {
                "mappings": [],
                "stats": {
                    "total": 0,
                    "mapped": 0,
                    "errors": 0
                }
            }
            
        # Ensure we have valid data
        if not isinstance(points, list):
            current_app.logger.warning(f"Expected points to be a list, got {type(points)}")
            return {
                "mappings": [],
                "stats": {
                    "total": 1,
                    "mapped": 0,
                    "errors": 1
                }
            }
            
        # Log input structure info
        current_app.logger.info(f"Points type: {type(points)}, count: {len(points)}")
        current_app.logger.info(f"Target schema: {target_schema}, Strategy: {matching_strategy}, Confidence: {confidence_threshold}")
        
        try:
            # Log a sample of the points for debugging
            if points and len(points) > 0:
                current_app.logger.info(f"Sample point data: {points[0]}")
            
            # First group points by deviceId/type
            device_groups = {}
            
            # Enhanced HVAC equipment type mapping templates
            hvac_equipment_types = {
                "ahu": "AHU",
                "vav": "VAV",
                "fcu": "FCU",
                "pump": "PUMP",
                "fan": "FAN", 
                "damper": "DAMPER",
                "valve": "VALVE",
                "chiller": "CHILLER",
                "boiler": "BOILER",
                "rtu": "RTU",
                "ctu": "CTU",
                "controller": "CONTROLLER"
            }
            
            # Map point types to likely equipment type when not specified
            point_type_to_equipment_map = {
                "temperature": "AHU",
                "temp": "AHU",
                "humidity": "AHU",
                "pressure": "AHU",
                "flow": "VAV",
                "speed": "FCU",
                "status": "CONTROLLER",
                "setpoint": "CONTROLLER",
                "sp": "CONTROLLER",
                "cooling": "CHILLER",
                "heating": "BOILER"
            }
            
            # Process each point to extract/infer deviceId and deviceType
            for point in points:
                point_name = point.get('pointName', '')
                if not point_name:
                    continue
                    
                point_name_lower = point_name.lower()
                
                # Try to extract deviceId from point name using common patterns
                device_id = point.get('deviceId', '')
                if not device_id:
                    # Look for common patterns like AHU-01, FCU_02, etc.
                    device_patterns = [
                        r'([A-Za-z]+)[-_]?(\d+)',         # Match AHU-01, VAV_23, etc.
                        r'([A-Za-z]+)(\d+)',              # Match AHU01, FCU2, etc.
                        r'([A-Za-z]+)[-_]?(\d+)[-_]?(\d+)'  # Match AHU-01-02, FCU_01_23, etc.
                    ]
                    
                    for pattern in device_patterns:
                        match = re.search(pattern, point_name_lower)
                        if match:
                            # Use the full match as deviceId
                            prefix = match.group(1).upper()  # e.g., "AHU"
                            number = match.group(2)  # e.g., "01"
                            device_id = f"{prefix}-{number}"
                            break
                
                # If still no deviceId, use a fallback
                if not device_id:
                    device_id = "UNKNOWN"
                
                # Determine HVAC equipment type
                equipment_type = point.get('deviceType', '')
                
                # If equipment type is provided, normalize it
                if equipment_type:
                    equip_type_lower = equipment_type.lower()
                    for key, value in hvac_equipment_types.items():
                        if key in equip_type_lower:
                            equipment_type = value
                            break
                # If not provided, try to infer from deviceId
                elif device_id != "UNKNOWN":
                    device_id_prefix = device_id.split('-')[0].lower() if '-' in device_id else device_id.lower()
                    for key, value in hvac_equipment_types.items():
                        if key in device_id_prefix:
                            equipment_type = value
                            break
                
                # If still no equipment type, try to infer from point properties
                if not equipment_type:
                    point_type = point.get('pointType', '').lower()
                    
                    # Check point type
                    for key, value in point_type_to_equipment_map.items():
                        if (point_type and key in point_type) or key in point_name_lower:
                            equipment_type = value
                            break
                
                # Last resort fallback
                if not equipment_type:
                    equipment_type = "UNKNOWN"
                
                # Create device group key
                device_key = f"{equipment_type}-{device_id}"
                
                # Add to device groups
                if device_key not in device_groups:
                    device_groups[device_key] = {
                        "deviceId": device_id,
                        "equipmentType": equipment_type,
                        "points": []
                    }
                
                device_groups[device_key]["points"].append(point)
            
            # Now map each point with its device context
            mappings = []
            
            # Map points for each device group
            for device_key, group in device_groups.items():
                device_id = group["deviceId"]
                equipment_type = group["equipmentType"]
                device_points = group["points"]
                
                # Create EnOS model base path for this device
                enos_base_path = f"{equipment_type}/{device_id}"
                
                # Map each point in this device group
                for point in device_points:
                    point_id = point.get('id', '')
                    point_name = point.get('pointName', '')
                    point_type = point.get('pointType', '')
                    unit = point.get('unit', '')
                    
                    # Determine point category and subpath based on point name/type
                    point_name_lower = point_name.lower()
                    point_category = 'generic'
                    mapping_confidence = 0.75
                    
                    # Temperature patterns
                    if ("temp" in point_name_lower or "tmp" in point_name_lower or 
                            (point_type and "temp" in point_type.lower())):
                        mapping_confidence = 0.9
                        if ("supply" in point_name_lower or "sa" in point_name_lower or 
                                "sat" in point_name_lower or "discharge" in point_name_lower):
                            point_category = 'supplyTemperature'
                            mapping_confidence = 0.95
                        elif ("return" in point_name_lower or "ra" in point_name_lower or 
                                "rat" in point_name_lower):
                            point_category = 'returnTemperature'
                            mapping_confidence = 0.95
                        elif ("out" in point_name_lower or "oa" in point_name_lower or 
                                "oat" in point_name_lower or "ambient" in point_name_lower):
                            point_category = 'outdoorTemperature'
                            mapping_confidence = 0.93
                        elif ("zone" in point_name_lower or "room" in point_name_lower or 
                                "space" in point_name_lower):
                            point_category = 'zoneTemperature'
                            mapping_confidence = 0.94
                        else:
                            point_category = 'temperature'
                    # Humidity patterns
                    elif ("hum" in point_name_lower or "rh" in point_name_lower or 
                            (point_type and "humid" in point_type.lower())):
                        point_category = 'humidity'
                        mapping_confidence = 0.92
                    # Pressure patterns
                    elif ("press" in point_name_lower or "pres" in point_name_lower or 
                            (point_type and "press" in point_type.lower())):
                        point_category = 'pressure'
                        mapping_confidence = 0.88
                    # Flow patterns
                    elif ("flow" in point_name_lower or "cfm" in point_name_lower or 
                            (point_type and "flow" in point_type.lower())):
                        point_category = 'airflow'
                        mapping_confidence = 0.87
                    # Fan patterns
                    elif ("fan" in point_name_lower or 
                            (point_type and "fan" in point_type.lower())):
                        if ("status" in point_name_lower or "state" in point_name_lower or 
                                "on" in point_name_lower or "off" in point_name_lower):
                            point_category = 'fanStatus'
                            mapping_confidence = 0.93
                        elif ("speed" in point_name_lower or "freq" in point_name_lower):
                            point_category = 'fanSpeed'
                            mapping_confidence = 0.92
                        else:
                            point_category = 'fan'
                            mapping_confidence = 0.85
                    # Damper patterns
                    elif ("damp" in point_name_lower or 
                            (point_type and "damper" in point_type.lower())):
                        point_category = 'damperPosition'
                        mapping_confidence = 0.91
                    # Valve patterns
                    elif ("valve" in point_name_lower or 
                            (point_type and "valve" in point_type.lower())):
                        point_category = 'valvePosition'
                        mapping_confidence = 0.90
                    # Status patterns
                    elif ("status" in point_name_lower or "state" in point_name_lower or 
                            "on" in point_name_lower or "off" in point_name_lower or
                            (point_type and "status" in point_type.lower())):
                        point_category = 'status'
                        mapping_confidence = 0.84
                    # Setpoint patterns
                    elif ("set" in point_name_lower or "sp" in point_name_lower or 
                            (point_type and "setpoint" in point_type.lower())):
                        point_category = 'setpoint'
                        if "temp" in point_name_lower:
                            point_category = 'temperatureSetpoint'
                            mapping_confidence = 0.92
                        elif "flow" in point_name_lower:
                            point_category = 'flowSetpoint'
                            mapping_confidence = 0.91
                        elif "press" in point_name_lower:
                            point_category = 'pressureSetpoint'
                            mapping_confidence = 0.91
                        else:
                            mapping_confidence = 0.89
                    
                    # Import the EnOSMapper to get proper point mapping
                    from app.bms.mapping import EnOSMapper
                    
                    # Try to map the point to the actual EnOS point from enos.json
                    try:
                        mapper = EnOSMapper()
                        # Map point directly - this will return just the point name from enos.json
                        enos_point_name = mapper.map_point(point_name, equipment_type)
                        
                        # If we got a valid mapping, use it
                        if enos_point_name:
                            enos_path = enos_point_name
                        else:
                            # Fallback to the previous structure
                            enos_path = point_category
                    except Exception as mapping_error:
                        current_app.logger.warning(f"Error mapping point {point_name}: {str(mapping_error)}")
                        # Fallback to previous structure
                        enos_path = point_category
                    
                    # Apply confidence threshold
                    if mapping_confidence >= confidence_threshold:
                        # Create the mapping result
                        mapping_result = {
                            "pointId": point_id,
                            "pointName": point_name,
                            "pointType": point_type,
                            "unit": unit,
                            "deviceId": device_id,
                            "deviceType": equipment_type,
                            "pointCategory": point_category,
                            "enosPoints": enos_path.split('/')[-1] if enos_path else None,
                            "confidence": mapping_confidence,
                            "mappingSource": matching_strategy,
                            "status": "mapped"
                        }
                        
                        mappings.append(mapping_result)
            
            # Gather statistics
            total_points = len(points)
            mapped_points = len(mappings)
            device_count = len(device_groups)
            device_types = len(set(group["equipmentType"] for group in device_groups.values()))
            
            # Log results
            current_app.logger.info(f"Mapping complete: {mapped_points}/{total_points} points mapped across {device_count} devices")
            
            # Return the mapping results
            return {
                "mappings": mappings,
                "stats": {
                    "total": total_points,
                    "mapped": mapped_points,
                    "errors": 0,
                    "deviceCount": device_count,
                    "deviceTypes": device_types
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Error in map_bms_points: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "mappings": [],
                "stats": {
                    "total": len(points),
                    "mapped": 0,
                    "errors": 1
                },
                "error": str(e)
            }

# Create a singleton instance of the service
bms_service = BMSService() 