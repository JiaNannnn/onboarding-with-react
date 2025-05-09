#from app import celery
from app.bms.utils import EnOSClient, BMSParser
import time
from flask import current_app

# @celery.task(bind=True, max_retries=3)
def search_points_task(self, api_url, access_key, secret_key, org_id, asset_id, device_instances, protocol='bacnet'):
    """Task to search for points across multiple devices"""
    client = EnOSClient(api_url=api_url, access_key=access_key, secret_key=secret_key, org_id=org_id)
    
    try:
        # Initiate the search
        search_result = client.search_points(asset_id, device_instances, protocol)
        
        if search_result.get('code') != 0:
            return {
                "status": "failed",
                "message": search_result.get('msg', 'Unknown error'),
                "code": "API_ERROR"
            }
        
        # Now fetch points for each device
        results = {}
        
        for device_instance in device_instances:
            # Wait a bit between devices to avoid overloading the API
            time.sleep(2)
            
            # Get points for this device - pass all credentials to the task
            device_result = fetch_points_task.delay(
                api_url, 
                access_key, 
                secret_key, 
                org_id, 
                asset_id, 
                device_instance, 
                protocol=protocol
            )
            results[str(device_instance)] = {
                "task_id": device_result.id,
                "status": "processing"
            }
        
        return {
            "status": "success",
            "message": f"Points search completed for {len(device_instances)} devices",
            "device_tasks": results
        }
    
    except Exception as e:
        self.retry(exc=e, countdown=30)
        return {
            "status": "failed",
            "message": str(e),
            "code": "INTERNAL_ERROR"
        }

# @celery.task(bind=True, max_retries=3)
def fetch_points_task(self, api_url, access_key, secret_key, org_id, asset_id, device_instance, device_address="unknown-ip", protocol='bacnet'):
    """Task to fetch points for a specific device"""
    client = EnOSClient(api_url=api_url, access_key=access_key, secret_key=secret_key, org_id=org_id)
    
    try:
        result = client.fetch_points(asset_id, device_instance, device_address, protocol)
        
        if result.get('code') == 0:
            # Return only essential information to avoid large responses
            return {
                "status": "success",
                "point_count": result.get('point_count', 0),
                "file_path": result.get('file_path', ''),
                "sample_points": result.get('points', [])[:5] if result.get('points') else []
            }
        else:
            return {
                "status": "failed",
                "message": result.get('msg', 'Unknown error'),
                "code": "API_ERROR"
            }
    
    except Exception as e:
        self.retry(exc=e, countdown=30)
        return {
            "status": "failed",
            "message": str(e),
            "code": "INTERNAL_ERROR"
        }

# @celery.task(bind=True, max_retries=3)
def get_network_config_task(self, api_url, access_key, secret_key, org_id, asset_id):
    """Task to retrieve network configuration options"""
    # Check if we're in development/testing mode
    # Real implementation for production
    client = EnOSClient(api_url=api_url, access_key=access_key, secret_key=secret_key, org_id=org_id)

    try:
        result = client.get_network_config(asset_id)
        
        if result.get('code') == 0:
            # Extract network options
            networks = []
            if 'data' in result and isinstance(result['data'], list):
                networks = result['data']
            
            return {
                "status": "success",
                "networks": networks
            }
        else:
            return {
                "status": "failed",
                "message": result.get('msg', 'Unknown error'),
                "code": "API_ERROR"
            }
    
    except Exception as e:
        self.retry(exc=e, countdown=30)
        return {
            "status": "failed",
            "message": str(e),
            "code": "INTERNAL_ERROR"
        }

# @celery.task(bind=True, max_retries=3)
def discover_devices_task(self, api_url, access_key, secret_key, org_id, asset_id, networks, protocol='bacnet'):
    """Task to discover devices on networks"""
    client = EnOSClient(api_url=api_url, access_key=access_key, secret_key=secret_key, org_id=org_id)
    
    try:
        all_devices = []
        results = {}
        
        # Search on each network
        for network in networks:
            network_result = client.search_device(asset_id, network, protocol)
            results[network] = network_result
            
            # Extract devices if available
            if (network_result and 
                network_result.get('code') == 0 and 
                'result' in network_result and 
                'deviceList' in network_result['result']):
                devices = network_result['result']['deviceList']
                all_devices.extend(devices)
        
        # Save combined device list to a file
        if all_devices:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            file_name = f"devices_{asset_id}_{timestamp}.json"
            file_path = client.save_devices_to_file(all_devices, file_name)
        else:
            file_path = None
        
        return {
            "status": "success",
            "devices": all_devices,
            "count": len(all_devices),
            "file_path": file_path
        }
    
    except Exception as e:
        self.retry(exc=e, countdown=30)
        return {
            "status": "failed",
            "message": str(e),
            "code": "INTERNAL_ERROR"
        }

# @celery.task
def group_points_task(raw_points):
    """异步分组任务"""
    from app.bms.grouping import DeviceGrouper
    
    grouper = DeviceGrouper()
    return grouper.process(raw_points) 