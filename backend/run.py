import os
import json
import logging
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv
import time
from app import create_app

# Import BMSDataPoints directly from the current directory
try:
    from BMSDataPoints import discover_devices, get_points_for_devices, getNetConfig, searchDevice, fetchPoints, search_points
except ImportError as e:
    print(f"Warning: Could not import BMSDataPoints: {str(e)}")
    # Create dummy functions to avoid import errors
    def discover_devices(*args, **kwargs): 
        return {"code": 1, "msg": "BMSDataPoints module not found"}
    def get_points_for_devices(*args, **kwargs): 
        return {"code": 1, "msg": "BMSDataPoints module not found"}
    def getNetConfig(*args, **kwargs):
        return {"code": 1, "msg": "BMSDataPoints module not found"}
    def searchDevice(*args, **kwargs):
        return {"code": 1, "msg": "BMSDataPoints module not found"}
    def fetchPoints(*args, **kwargs):
        return {"code": 1, "msg": "BMSDataPoints module not found"}
    def search_points(*args, **kwargs):
        return {"code": 1, "msg": "BMSDataPoints module not found"}

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = create_app()
CORS(app)  # Enable CORS for all routes

# EnvisionIoT API default configuration
DEFAULT_API_CONFIG = {
    "api_url": "https://ag-eu2.envisioniot.com",
    "access_key": "974a84b0-2ec1-44f7-aa3d-5fe01b55b718",
    "secret_key": "04cc544f-ffcb-4b97-84fc-d7ecf8c4b8be",
    "org_id": "o16975327606411181",
    "asset_id": "5xkIipSH"
}

# Store the current BMS connection state
current_connection = {
    "connected": False,
    "api_url": DEFAULT_API_CONFIG["api_url"],
    "access_key": DEFAULT_API_CONFIG["access_key"],
    "secret_key": DEFAULT_API_CONFIG["secret_key"],
    "org_id": DEFAULT_API_CONFIG["org_id"],
    "asset_id": DEFAULT_API_CONFIG["asset_id"]
}

# @app.route('/api/health', methods=['GET'])
# def health_check():
#     """Endpoint to check if the API is running."""
#     return jsonify({"status": "healthy"}), 200

# @app.route('/api/bms/points', methods=['GET'])
# def get_bms_points():
#     """Fetch BMS points from the EnvisionIoT API using BMSDataPoints.py."""
#     try:
#         # Use the current connection information
#         if not current_connection["connected"]:
#             return jsonify({
#                 "error": "Not connected to BMS API",
#                 "details": "Please connect to the BMS API first"
#             }), 400
        
#         asset_id = request.args.get('assetId', current_connection["asset_id"])
#         logger.info(f"Fetching BMS points for asset: {asset_id}")
        
#         try:
#             # Try to use the BMSDataPoints module to get real data
#             # First, set the environment variables expected by BMSDataPoints
#             os.environ["ENOS_API_URL"] = current_connection["api_url"]
#             os.environ["ENOS_ACCESS_KEY"] = current_connection["access_key"]
#             os.environ["ENOS_SECRET_KEY"] = current_connection["secret_key"]
#             os.environ["ENOS_ORG_ID"] = current_connection["org_id"]
#             os.environ["ENOS_ASSET_ID"] = asset_id
            
#             # First, discover some devices
#             device_result = discover_devices(asset_id)
#             logger.info(f"Device discovery result: {json.dumps(device_result)}")
            
#             # Check if we have devices to fetch points for
#             if device_result.get("code") == 0 and "all_devices" in device_result and device_result["all_devices"]:
#                 # We have devices, fetch points for them
#                 devices = device_result["all_devices"]
#                 points_result = get_points_for_devices(asset_id, devices)
#                 logger.info(f"Points result: {json.dumps(points_result)}")
                
#                 # Extract points from the result
#                 if points_result.get("code") == 0 and "point_results" in points_result:
#                     # Format all points into a flat list
#                     all_points = []
#                     for device_id, device_points in points_result["point_results"].items():
#                         if "result" in device_points and "objectPropertys" in device_points["result"]:
#                             points = device_points["result"]["objectPropertys"]
#                             # Add device ID to each point
#                             for point in points:
#                                 point["deviceId"] = device_id
#                                 point["source"] = "EnvisionIoT"
#                                 # Create a proper ID from device and point ID
#                                 if "objectInst" in point:
#                                     point["id"] = f"{device_id}:{point.get('objectInst', '')}"
#                                 # Map point fields to match our frontend expectations
#                                 if "objectName" in point and "pointName" not in point:
#                                     point["pointName"] = point["objectName"]
#                                 if "objectType" in point and "pointType" not in point:
#                                     point["pointType"] = point["objectType"]
#                             all_points.extend(points)
                    
#                     logger.info(f"Returning {len(all_points)} points")
#                     return jsonify({"points": all_points}), 200
            
#             # If we didn't get points from the real API or there was an error,
#             # fall back to mock data for demonstration
#             logger.warning("Could not fetch real points, using mock data")
#             mock_points = [
#                 {"id": "1", "name": "AHU1.SAT", "description": "Supply Air Temperature", "type": "AI", "source": "EnvisionIoT"},
#                 {"id": "2", "name": "AHU1.RAT", "description": "Return Air Temperature", "type": "AI", "source": "EnvisionIoT"},
#                 {"id": "3", "name": "AHU1.MAT", "description": "Mixed Air Temperature", "type": "AI", "source": "EnvisionIoT"},
#                 {"id": "4", "name": "AHU1.Fan.Speed", "description": "Fan Speed", "type": "AO", "source": "EnvisionIoT"},
#                 {"id": "5", "name": "AHU1.Damper.Pos", "description": "Damper Position", "type": "AO", "source": "EnvisionIoT"}
#             ]
            
#             return jsonify({"points": mock_points}), 200
            
#         except Exception as module_error:
#             logger.error(f"Error using BMSDataPoints module: {str(module_error)}")
#             logger.exception(module_error)
            
#             # Fall back to mock data
#             mock_points = [
#                 {"id": "1", "name": "AHU1.SAT", "description": "Supply Air Temperature", "type": "AI", "source": "EnvisionIoT"},
#                 {"id": "2", "name": "AHU1.RAT", "description": "Return Air Temperature", "type": "AI", "source": "EnvisionIoT"},
#                 {"id": "3", "name": "AHU1.MAT", "description": "Mixed Air Temperature", "type": "AI", "source": "EnvisionIoT"},
#                 {"id": "4", "name": "AHU1.Fan.Speed", "description": "Fan Speed", "type": "AO", "source": "EnvisionIoT"},
#                 {"id": "5", "name": "AHU1.Damper.Pos", "description": "Damper Position", "type": "AO", "source": "EnvisionIoT"}
#             ]
            
#             return jsonify({
#                 "points": mock_points,
#                 "warning": "Using mock data due to BMSDataPoints module error",
#                 "error_details": str(module_error)
#             }), 200
        
#     except Exception as e:
#         logger.error(f"Error fetching BMS points: {str(e)}")
#         logger.exception(e)
#         return jsonify({"error": "Failed to fetch BMS points", "details": str(e)}), 500

# @app.route('/api/bms/connect', methods=['POST'])
# def connect_to_bms():
#     """Connect to the BMS system with provided credentials using BMSDataPoints.py."""
#     try:
#         data = request.json
        
#         # Extract connection parameters from request
#         api_url = data.get('apiUrl', DEFAULT_API_CONFIG["api_url"])
#         access_key = data.get('accessKey', DEFAULT_API_CONFIG["access_key"])
#         secret_key = data.get('secretKey', DEFAULT_API_CONFIG["secret_key"])
#         org_id = data.get('orgId', DEFAULT_API_CONFIG["org_id"])
#         asset_id = data.get('assetId', DEFAULT_API_CONFIG["asset_id"])
        
#         logger.info(f"Connecting to BMS with asset ID: {asset_id}")
        
#         # Set the environment variables for BMSDataPoints
#         os.environ["ENOS_API_URL"] = api_url
#         os.environ["ENOS_ACCESS_KEY"] = access_key
#         os.environ["ENOS_SECRET_KEY"] = secret_key
#         os.environ["ENOS_ORG_ID"] = org_id
#         os.environ["ENOS_ASSET_ID"] = asset_id
        
#         # Try to validate the connection by getting network config
#         try:
#             net_config = getNetConfig(asset_id)
#             logger.info(f"Network config result: {json.dumps(net_config)}")
            
#             # If we get a successful response, store the connection
#             if net_config.get("code") == 0 or "data" in net_config:
#                 # Connection is valid
#                 current_connection.update({
#                     "connected": True,
#                     "api_url": api_url,
#                     "access_key": access_key,
#                     "secret_key": secret_key,
#                     "org_id": org_id,
#                     "asset_id": asset_id
#                 })
                
#                 return jsonify({
#                     "status": "success",
#                     "message": "Successfully connected to BMS",
#                     "connection": {
#                         "apiUrl": api_url,
#                         "accessKey": access_key,
#                         "orgId": org_id,
#                         "assetId": asset_id
#                     },
#                     "net_config": net_config.get("data", [])
#                 }), 200
#             else:
#                 # Connection failed
#                 return jsonify({
#                     "status": "error",
#                     "message": "Failed to connect to BMS API",
#                     "details": net_config.get("msg", "Unknown error")
#                 }), 400
                
#         except Exception as module_error:
#             logger.error(f"Error using BMSDataPoints module: {str(module_error)}")
#             logger.exception(module_error)
            
#             # For demo purposes, assume connection is successful even if there's an error
#             # In a real implementation, you would return an error
#             current_connection.update({
#                 "connected": True,
#                 "api_url": api_url,
#                 "access_key": access_key,
#                 "secret_key": secret_key,
#                 "org_id": org_id,
#                 "asset_id": asset_id
#             })
            
#             # Return sample network data for demo
#             sample_networks = ["No Network Card", "eth0(192.168.1.100)", "eth1(192.168.10.101)"]
            
#             return jsonify({
#                 "status": "success",
#                 "message": "Successfully connected to BMS (simulated)",
#                 "connection": {
#                     "apiUrl": api_url,
#                     "accessKey": access_key,
#                     "orgId": org_id,
#                     "assetId": asset_id
#                 },
#                 "net_config": sample_networks,
#                 "warning": "Using simulated connection due to BMSDataPoints module error",
#                 "error_details": str(module_error)
#             }), 200
        
#     except Exception as e:
#         logger.error(f"Error connecting to BMS: {str(e)}")
#         logger.exception(e)
#         return jsonify({"error": "Failed to connect to BMS", "details": str(e)}), 500

# @app.route('/api/bms/discover-devices', methods=['GET'])
# def discover_bms_devices():
#     """Discover BMS devices on a specific network."""
#     try:
#         # Check if connected
#         if not current_connection["connected"]:
#             return jsonify({
#                 "error": "Not connected to BMS API",
#                 "details": "Please connect to the BMS API first"
#             }), 400
        
#         # Get parameters
#         asset_id = request.args.get('assetId', current_connection["asset_id"])
#         network = request.args.get('network')
        
#         if not network:
#             return jsonify({
#                 "error": "Network parameter is required",
#                 "details": "Please specify a network to scan for devices"
#             }), 400
        
#         logger.info(f"Discovering devices on network {network} for asset {asset_id}")
        
#         # Set environment variables
#         os.environ["ENOS_API_URL"] = current_connection["api_url"]
#         os.environ["ENOS_ACCESS_KEY"] = current_connection["access_key"]
#         os.environ["ENOS_SECRET_KEY"] = current_connection["secret_key"]
#         os.environ["ENOS_ORG_ID"] = current_connection["org_id"]
#         os.environ["ENOS_ASSET_ID"] = asset_id
        
#         try:
#             # Use BMSDataPoints to search for devices
#             device_result = searchDevice(asset_id, network)
#             logger.info(f"Device search result: {json.dumps(device_result)}")
            
#             # Check for successful result
#             if device_result.get("code") == 0 and "result" in device_result and "deviceList" in device_result["result"]:
#                 devices = device_result["result"]["deviceList"]
#                 return jsonify({
#                     "status": "success",
#                     "message": f"Found {len(devices)} devices",
#                     "all_devices": devices
#                 }), 200
#             else:
#                 # Return the actual error from the API
#                 error_code = device_result.get("code", 500)
#                 error_msg = device_result.get("msg", "Unknown error from BMS API")
#                 logger.error(f"BMS API error: {error_code} - {error_msg}")
                
#                 return jsonify({
#                     "status": "error",
#                     "message": "Failed to discover devices",
#                     "error": error_msg,
#                     "code": error_code
#                 }), 400
                
#         except Exception as module_error:
#             logger.error(f"Error using BMSDataPoints module: {str(module_error)}")
#             logger.exception(module_error)
            
#             return jsonify({
#                 "status": "error",
#                 "message": "Error communicating with BMS API",
#                 "error": str(module_error)
#             }), 500
    
#     except Exception as e:
#         logger.error(f"Error discovering BMS devices: {str(e)}")
#         logger.exception(e)
#         return jsonify({"error": "Failed to discover BMS devices", "details": str(e)}), 500

# @app.route('/api/bms/fetch-points', methods=['POST'])
# def fetch_bms_points():
#     """Fetch points for specific BMS devices."""
#     try:
#         # Check if connected
#         if not current_connection["connected"]:
#             return jsonify({
#                 "error": "Not connected to BMS API",
#                 "details": "Please connect to the BMS API first"
#             }), 400
        
#         # Get parameters from request body
#         data = request.json
#         asset_id = data.get('assetId', current_connection["asset_id"])
#         device_instances = data.get('deviceInstances', [])
        
#         if not device_instances:
#             return jsonify({
#                 "error": "Device instances are required",
#                 "details": "Please specify at least one device instance"
#             }), 400
        
#         logger.info(f"Fetching points for devices {device_instances} for asset {asset_id}")
        
#         # Set environment variables
#         os.environ["ENOS_API_URL"] = current_connection["api_url"]
#         os.environ["ENOS_ACCESS_KEY"] = current_connection["access_key"]
#         os.environ["ENOS_SECRET_KEY"] = current_connection["secret_key"]
#         os.environ["ENOS_ORG_ID"] = current_connection["org_id"]
#         os.environ["ENOS_ASSET_ID"] = asset_id
        
#         try:
#             # 1. Initiate point discovery for all devices (search API)
#             logger.info(f"Initiating point discovery for devices: {device_instances}")
#             search_result = search_points(asset_id, device_instances)
#             logger.info(f"Point discovery initiation result: {json.dumps(search_result)}")
#             if search_result.get("code") != 0:
#                 return jsonify({
#                     "status": "error",
#                     "message": "Failed to initiate point discovery",
#                     "error": search_result.get("msg", "Unknown error from BMS API"),
#                     "code": search_result.get("code", 500)
#                 }), 400
#             # Wait a few seconds for discovery to start
#             time.sleep(5)
#             # 2. Now fetch points for each device
#             all_points = []
#             errors = []
#             for device_instance in device_instances:
#                 points_result = fetchPoints(asset_id, device_instance)
#                 logger.info(f"Points result for device {device_instance}: {json.dumps(points_result)}")
#                 if points_result.get("code") == 0 and "result" in points_result and "objectPropertys" in points_result["result"]:
#                     device_points = points_result["result"]["objectPropertys"]
#                     for point in device_points:
#                         point["deviceId"] = device_instance
#                         point["source"] = "EnvisionIoT"
#                         if "objectInst" in point:
#                             point["id"] = f"{device_instance}:{point.get('objectInst', '')}"
#                         if "objectName" in point and "pointName" not in point:
#                             point["pointName"] = point["objectName"]
#                             point["name"] = point["objectName"]
#                         if "objectType" in point and "pointType" not in point:
#                             point["pointType"] = point["objectType"]
#                             point["type"] = point["objectType"]
#                     all_points.extend(device_points)
#                 else:
#                     error_code = points_result.get("code", 500)
#                     error_msg = points_result.get("msg", "Unknown error from BMS API")
#                     errors.append({
#                         "device_instance": device_instance,
#                         "error": error_msg,
#                         "code": error_code
#                     })
#             if all_points:
#                 response_data = {
#                     "status": "success",
#                     "message": f"Found {len(all_points)} points from {len(device_instances) - len(errors)} devices",
#                     "points": all_points
#                 }
#                 if errors:
#                     response_data["warnings"] = f"Failed to fetch points for {len(errors)} devices"
#                     response_data["device_errors"] = errors
#                 return jsonify(response_data), 200
#             else:
#                 return jsonify({
#                     "status": "error",
#                     "message": "Failed to fetch points for all devices",
#                     "device_errors": errors
#                 }), 400
#         except Exception as module_error:
#             logger.error(f"Error using BMSDataPoints module: {str(module_error)}")
#             logger.exception(module_error)
#             return jsonify({
#                 "status": "error",
#                 "message": "Error communicating with BMS API",
#                 "error": str(module_error)
#             }), 500
#     except Exception as e:
#         logger.error(f"Error fetching BMS points: {str(e)}")
#         logger.exception(e)
#         return jsonify({"error": "Failed to fetch BMS points", "details": str(e)}), 500

# @app.route('/api/bms/upload', methods=['POST'])
# def upload_bms_points():
    # """Upload BMS points from a CSV file."""
    # try:
    #     if 'file' not in request.files:
    #         return jsonify({"error": "No file provided"}), 400
            
    #     file = request.files['file']
        
    #     if file.filename == '':
    #         return jsonify({"error": "No file selected"}), 400
            
    #     if not file.filename.endswith('.csv'):
    #         return jsonify({"error": "File must be a CSV"}), 400
        
    #     # Process the CSV file (in a real implementation)
    #     # For demo purposes, return mock data
        
    #     mock_points = [
    #         {"id": "1", "name": "AHU1.SAT", "description": "Supply Air Temperature", "type": "AI", "source": "CSV"},
    #         {"id": "2", "name": "AHU1.RAT", "description": "Return Air Temperature", "type": "AI", "source": "CSV"},
    #         {"id": "3", "name": "AHU1.MAT", "description": "Mixed Air Temperature", "type": "AI", "source": "CSV"}
    #     ]
        
    #     return jsonify({"points": mock_points}), 200
        
    # except Exception as e:
    #     logger.error(f"Error processing CSV file: {str(e)}")
    #     logger.exception(e)
    #     return jsonify({"error": "Failed to process CSV file", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting BMS backend on port {port}, debug mode: {debug}")
    app.run(host='0.0.0.0', port=port, debug=debug)
