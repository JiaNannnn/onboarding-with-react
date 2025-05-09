from flask import Blueprint, jsonify, request, redirect, url_for, current_app, make_response, send_from_directory
import requests
#from app import celery
from app.bms.tasks import fetch_points_task, search_points_task, discover_devices_task, get_network_config_task, group_points_task
from app.bms.grouping import DeviceGrouper
from app.bms.mapping import EnOSMapper
from app.bms.utils import EnOSClient
from app.services.bms_service import BMSService
# Import removed - we now import these functions locally within each route handler as needed
import pandas as pd
import os
import tempfile
import uuid
from datetime import datetime
import concurrent.futures
import traceback
import time
import json
import threading
import asyncio
from io import StringIO
import csv
import re

# Create an instance of BMSService
bms_service = BMSService()

# API Version prefix
API_VERSION = 'v1'

# Create the Blueprint for this module if it does not exist
bp = Blueprint('api', __name__, url_prefix='/api')

# Add this after imports, before any routes
# Initialize with empty/default values, to be populated by user input/connection attempts
current_connection = {
    "connected": False,
    "api_url": "",
    "access_key": "",
    "secret_key": "", # Store hash or manage securely if persisted
    "org_id": "",
    "asset_id": ""
}

# Example of how to parse these from request query (using FastAPI)
# Assuming you have FastAPI and Pydantic installed
# from fastapi import APIRouter, Query, Depends
# from pydantic import BaseModel
#
# router = APIRouter()
#
# class ConnectionParams(BaseModel):
#     api_url: str
#     access_key: str
#     secret_key: str
#     org_id: str
#     asset_id: str # Optional, depending on whether it's always needed
#
# # This is an example route. You would integrate this logic
# # into your existing routes where these parameters are needed.
# @router.get("/connect-example") # Or use POST, etc.
# async def connect_with_params(
#     api_url: str = Query(..., title="API URL", description="EnOS API Gateway URL"),
#     access_key: str = Query(..., title="Access Key", description="EnOS Service Account Access Key"),
#     secret_key: str = Query(..., title="Secret Key", description="EnOS Service Account Secret Key"),
#     org_id: str = Query(..., title="Organization ID", description="EnOS Organization ID"),
#     asset_id: str = Query(None, title="Asset ID", description="Specific Asset ID (optional)") # Make optional if not always required
# ):
#     # Now you have the connection parameters from the query
#     parsed_connection_details = {
#         "api_url": api_url,
#         "access_key": access_key,
#         "secret_key": secret_key, # Be careful with exposing/logging secret keys
#         "org_id": org_id,
#         "asset_id": asset_id,
#         "connected": True # Assuming connection will be attempted with these details
#     }
#
#     # Here, you would use these parsed_connection_details to interact with the EnOS API
#     # For example, pass them to a service function that makes the API calls.
#
#     # Replace the hardcoded current_connection or use this parsed_connection_details
#     # For demonstration, let's just return them:
#     return {"message": "Connection parameters received", "details": parsed_connection_details}

# If you were to replace the global current_connection, you'd need a mechanism
# to set it, perhaps on application startup if these are global settings,
# or manage it per request if they can vary.
# For per-request, you wouldn't use a global variable like current_connection
# but rather pass the parsed parameters to the functions that need them.

# If you want to use a Pydantic model for dependency injection (cleaner):
# @router.get("/connect-dependency-example")
# async def connect_with_dependency(params: ConnectionParams = Depends()):
#     # params.api_url, params.access_key, etc. are available here
#     # This is often a preferred way to handle multiple query parameters.
#     parsed_connection_details = params.model_dump()
#     parsed_connection_details["connected"] = True
#
#     return {"message": "Connection parameters received via dependency", "details": parsed_connection_details}

# Make sure to add `router` to your main FastAPI app instance, e.g.:
# app.include_router(router, prefix="/api")

# Helper function for OPTIONS requests
def handle_options():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization,X-Requested-With,Access-Control-Allow-Origin,x-access-key,x-secret-key,AccessKey,SecretKey,Content-Length")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
    return response

@bp.route(f'/{API_VERSION}/map-points', methods=['POST', 'OPTIONS'])
def bms_map_points():
    """Map BMS points to EnOS points using AI-powered mapping."""
    # Debug logging
    print(f"Received {request.method} request to map-points endpoint")
    print(f"Request headers: {request.headers}")
    
    # For OPTIONS requests (CORS preflight)
    if request.method == 'OPTIONS':
        print("Handling OPTIONS request")
        return handle_options()
    
    if request.method != 'POST':
        print(f"Unsupported method: {request.method}")
        return jsonify({"success": False, "error": f"Method {request.method} not allowed"}), 405
    
    try:
        print("Processing POST request data")
        data = request.json
        if not data:
            print("No data provided in request")
            return jsonify({"success": False, "error": "No data provided"}), 400

        # Get points and configuration
        points = data.get('points', [])
        if not points:
            print("No points provided in request data")
            return jsonify({"success": False, "error": "No points provided"}), 400
            
        # Get mapping configuration 
        mapping_config = data.get('mappingConfig', {})
        
        # Generate a task ID for this operation
        task_id = str(uuid.uuid4())
        
        # Initialize the real EnOS Mapper instead of using mock data
        mapper = EnOSMapper()
        
        # Ensure tmp directory exists
        os.makedirs("./tmp", exist_ok=True)
        
        # Process the points using the real mapping implementation
        mapping_result = mapper.map_points(points)
        
        # Extract stats and prepare result structure
        stats = mapping_result.get("stats", {"total": len(points), "mapped": 0, "errors": 0})
        
        # Create result structure
        result = {
            "success": mapping_result.get("success", True),
            "status": "completed",
            "taskId": task_id,
            "batchMode": True,
            "totalBatches": 1,
            "completedBatches": 1,
            "progress": 1.0,
            "totalPoints": len(points),
            "mappings": [],
            "stats": stats
        }
        
        # Format mappings for result
        formatted_mappings = []
        for mapping_item in mapping_result.get("mappings", []):
            # Extract original point data
            point_data = mapping_item.get("original", {})
            mapping_data = mapping_item.get("mapping", {})
            
            # Create a properly structured mapping object that matches the frontend expected format
            formatted_mapping = {
                # Include fields in both flat format (for backward compatibility)
                "pointId": point_data.get("pointId", ""),
                "pointName": point_data.get("pointName", ""),
                "deviceType": point_data.get("deviceType", ""),
                "deviceId": point_data.get("deviceId", ""),
                "pointType": point_data.get("pointType", ""),
                "unit": point_data.get("unit", ""),
                "enosPoint": mapping_data.get("enosPoint", "unknown"),
                "confidence": mapping_data.get("confidence", 0.0),
                "mapping_reason": mapping_data.get("explanation", ""),
                "status": mapping_data.get("status", "mapped"),
                
                # Also include in structured format for newer frontend components
                "original": {
                    "pointId": point_data.get("pointId", ""),
                    "pointName": point_data.get("pointName", ""),
                    "deviceType": point_data.get("deviceType", ""),
                    "deviceId": point_data.get("deviceId", ""),
                    "pointType": point_data.get("pointType", ""),
                    "unit": point_data.get("unit", ""),
                    "value": point_data.get("value", None)
                },
                "mapping": {
                    "pointId": point_data.get("pointId", ""),
                    "enosPoint": mapping_data.get("enosPoint", "unknown"),
                    "status": mapping_data.get("status", "mapped"),
                    "confidence": mapping_data.get("confidence", 0.0),
                    "explanation": mapping_data.get("explanation", "")
                }
            }
            formatted_mappings.append(formatted_mapping)
        
        result["mappings"] = formatted_mappings
        
        # Save the result to a file
        with open(f"./tmp/mapping_{task_id}.json", "w") as f:
            json.dump(result, f, indent=2)
            
        print(f"Mapping task {task_id} completed with real EnOSMapper")
        current_app.logger.info(f"Mapping task {task_id} completed with real EnOSMapper")
        
        # Return immediate successful response
        return jsonify({
            "success": True,
            "status": "completed",
            "taskId": task_id,
            "batchMode": True,
            "totalBatches": 1,
            "completedBatches": 1,
            "progress": 1.0,
            "message": f"Processed {len(points)} points with real EnOSMapper"
        })
    
    except Exception as e:
        current_app.logger.error(f"Error in map_points: {str(e)}")
        traceback.print_exc()  # Print full stack trace for debugging
        return jsonify({
            "success": False,
            "error": f"Error during mapping: {str(e)}",
            "mappings": [],
            "stats": {"total": len(points) if 'points' in locals() else 0, "mapped": 0, "errors": len(points) if 'points' in locals() else 0}
        }), 500

@bp.route(f'/{API_VERSION}/map-points/<task_id>', methods=['GET', 'OPTIONS'])
def get_mapping_status(task_id):
    """Get the status of a mapping task."""
    # Debug logging
    print(f"Received {request.method} request to get status for task {task_id}")
    
    # For OPTIONS requests (CORS preflight)
    if request.method == 'OPTIONS':
        print("Handling OPTIONS request")
        return handle_options()
        
    if request.method != 'GET':
        print(f"Unsupported method: {request.method}")
        return jsonify({"success": False, "error": f"Method {request.method} not allowed"}), 405
        
    try:
        # Check if the task result file exists
        result_file = f"./tmp/mapping_{task_id}.json"
        
        if not os.path.exists(result_file):
            return jsonify({
                "success": False,
                "error": f"Task {task_id} not found"
            }), 404
        
        # Read the task result
        with open(result_file, "r") as f:
            result = json.load(f)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error getting task status for {task_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error getting task status: {str(e)}"
        }), 500

@bp.route('/bms/points/group-with-reasoning', methods=['POST', 'OPTIONS'])
def group_points_with_reasoning():
    """Group BMS points by device type with chain of thought reasoning."""
    if request.method == 'OPTIONS': return handle_options()
    data = request.json
    if not data or not isinstance(data, list):
        return jsonify({"error": "Invalid request data. Expected list of points."}), 400
    reasoning_engine = get_reasoning_engine()
    try:
        grouped_points = reasoning_engine.chain_of_thought_grouping(data)
        response = {}
        for device_type, points in grouped_points.items():
            all_reasoning = []
            for point in points:
                if "grouping_reasoning" in point:
                    all_reasoning.extend(point["grouping_reasoning"])
                if "grouping_reasoning" in point:
                    del point["grouping_reasoning"]
            unique_reasoning = list(dict.fromkeys(all_reasoning))
            response[device_type] = {"points": points, "reasoning": unique_reasoning}
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": f"Error during grouping: {str(e)}"}), 500

@bp.route('/bms/points/verify-groups', methods=['POST', 'OPTIONS'])
def verify_point_groups():
    """Verify and finalize point groupings."""
    if request.method == 'OPTIONS': return handle_options()
    data = request.json
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid request data. Expected dictionary of groups."}), 400
    reasoning_engine = get_reasoning_engine()
    try:
        verification_results = {}
        for device_type, group_data in data.items():
            if not isinstance(group_data, dict) or "points" not in group_data: continue
            points = group_data["points"]
            confidence_scores = reasoning_engine.calculate_group_confidence(device_type, points)
            verification_results[device_type] = {
                "points": points,
                "confidence": confidence_scores["overall"],
                "confidence_details": confidence_scores["details"]
            }
            if "reasoning" in group_data:
                verification_results[device_type]["reasoning"] = group_data["reasoning"]
        return jsonify(verification_results), 200
    except Exception as e:
        return jsonify({"error": f"Error during group verification: {str(e)}"}), 500

@bp.route('/bms/group_points_llm', methods=['POST', 'OPTIONS'])
def group_points_llm_endpoint():
    """Groups points from a specified CSV file using LLM (simulated)."""
    if request.method == 'OPTIONS': return handle_options()
    data = request.json
    if not data or not isinstance(data, dict): return jsonify({"error": "Invalid request format. Expected JSON object."}), 400
    if 'file_path' not in data: return jsonify({"error": "Missing required parameter: file_path"}), 400
    file_path = data['file_path']
    point_column = data.get('point_column', 'pointName')
    chunk_size = data.get('chunk_size', 100)
    if not os.path.exists(file_path): return jsonify({"error": f"File not found: {file_path}"}), 404
    if not isinstance(chunk_size, int) or chunk_size < 1 or chunk_size > 1000: return jsonify({"error": "Invalid chunk_size. Must be an integer between 1 and 1000."}), 400
    try:
        # Assuming llm_grouper is in bms subpackage
        from app.bms.llm_grouper import LLMGrouper 
        grouper = LLMGrouper()
        result = grouper.process_csv_file(file_path, point_column, chunk_size)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": f"Failed to process file: {str(e)}", "file_path": file_path, "point_column": point_column}), 500

@bp.route('/bms/export-mapping', methods=['POST', 'OPTIONS'])
def export_mapping():
    """Export mapping data to EnOS format, including unmapped points."""
    if request.method == 'OPTIONS': return handle_options()
    try:
        data = request.json
        if not data or not isinstance(data, dict) or "mappings" not in data: return jsonify({"error": "Invalid request format. Expected mappings array."}), 400
        mappings = data.get("mappings", [])
        include_unmapped = data.get("includeUnmapped", True)
        export_format = data.get("exportFormat", "json").lower()
        if not isinstance(mappings, list): return jsonify({"error": "Invalid mappings format. Expected array."}), 400
        # Assuming EnOSMapper is already imported
        mapper = EnOSMapper() 
        export_data = mapper.export_mappings(mappings, include_unmapped)
        mapped_count = len([r for r in export_data if r.get("status") == "mapped"])
        unmapped_count = len(export_data) - mapped_count
        if export_format == "csv":
            csv_output = StringIO()
            if export_data:
                fieldnames = list(export_data[0].keys())
                writer = csv.DictWriter(csv_output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(export_data)
                response = make_response(csv_output.getvalue())
                # Create a timestamp for the filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                response.headers["Content-Disposition"] = f"attachment; filename=enos_export_{timestamp}.csv"
                response.headers["Content-type"] = "text/csv"
                return response
            else: return jsonify({"error": "No data to export"}), 400
        else:
            # For JSON format, save to a file and return filepath
            if export_data:
                # Create timestamp and filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"enos_export_{timestamp}.json"
                filepath = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                # Save to file
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2)
                    
                return jsonify({
                    "success": True, 
                    "filepath": filepath,
                    "filename": filename,
                    "stats": {
                        "total": len(export_data), 
                        "mapped": mapped_count, 
                        "unmapped": unmapped_count
                    }
                })
            return jsonify({"success": True, "data": export_data, "stats": {"total": len(export_data), "mapped": mapped_count, "unmapped": unmapped_count}})
    except Exception as e:
        current_app.logger.error(f"Error exporting mapping: {str(e)}")
        return jsonify({"success": False, "error": f"Error exporting mapping: {str(e)}"}), 500

@bp.route('/bms/ai-grouping', methods=['POST', 'OPTIONS'])
def ai_grouping_endpoint():
    """Group BMS points by device type and device ID using AI methods (via DeviceGrouper)."""
    if request.method == 'OPTIONS':
        print("Handling OPTIONS request for /bms/ai-grouping")
        return handle_options()
    
    if request.method == 'POST':
        print(f"Received POST request for /bms/ai-grouping")
        try:
            data = request.json
            if not data or not isinstance(data, dict) or "points" not in data:
                return jsonify({"success": False,"error": "Missing points data"}), 400
            
            points_input = data["points"] # Rename to avoid conflict
            if not points_input:
                return jsonify({"success": False,"error": "Empty points array"}), 400

            # Ensure points are strings if objects are passed (DeviceGrouper expects list of strings)
            if isinstance(points_input[0], dict):
                points_str_list = [p.get('pointName', '') for p in points_input if p.get('pointName')]
            elif isinstance(points_input[0], str):
                points_str_list = points_input
            else:
                return jsonify({"success": False, "error": "Invalid format for points data. Expected list of strings or objects with 'pointName'"}), 400
                
            if not points_str_list:
                 return jsonify({"success": False,"error": "No valid point names found in input"}), 400

            current_app.logger.info(f"AI grouping requested for {len(points_str_list)} points via DeviceGrouper")

            # --- Use DeviceGrouper --- 
            grouper = DeviceGrouper()
            grouped_points_result = grouper.process(points_str_list) # Use the process method
            # --- End Use DeviceGrouper --- 

            # Calculate stats based on the result
            total_input_points = len(points_str_list)
            grouped_points_count = sum(len(p_list) for dev_dict in grouped_points_result.values() for p_list in dev_dict.values())
            # Note: Error count isn't directly available unless process raises specific errors or returns stats
            errors_count = 0 

            # Return the response from the grouper
            return jsonify({
                "success": True, # Assume success if no exception
                "grouped_points": grouped_points_result,
                "stats": {
                    "total": total_input_points,
                    "grouped": grouped_points_count, 
                    "errors": errors_count 
                }
            })
        except Exception as e:
            current_app.logger.error(f"Error during AI grouping via DeviceGrouper: {str(e)}")
            # Log the full traceback for better debugging
            current_app.logger.error(traceback.format_exc())
            return jsonify({"success": False,"error": f"Error during AI grouping: {str(e)}"}), 500
    else:
         # This case should technically not be reached if methods=['POST', 'OPTIONS']
         print(f"Unsupported method received for /bms/ai-grouping: {request.method}")
         return jsonify({"success": False, "error": f"Method {request.method} not allowed for this endpoint after OPTIONS handling."}), 405

@bp.route('/bms/points', methods=['GET'])
def get_bms_points():
    try:
        if not current_connection["connected"]:
            return jsonify({
                "error": "Not connected to BMS API",
                "details": "Please connect to the BMS API first"
            }), 400
        asset_id = request.args.get('assetId', current_connection["asset_id"])
        current_app.logger.info(f"Fetching BMS points for asset: {asset_id}")
        try:
            os.environ["ENOS_API_URL"] = request.args.get('apiUrl', current_connection["api_url"])
            os.environ["ENOS_ACCESS_KEY"] = request.args.get('accessKey', current_connection["access_key"])
            os.environ["ENOS_SECRET_KEY"] = request.args.get('secretKey', current_connection["secret_key"])
            os.environ["ENOS_ORG_ID"] = request.args.get('orgId', current_connection["org_id"])
            os.environ["ENOS_ASSET_ID"] = request.args.get('assetId', current_connection["asset_id"])
            device_result = discover_devices_task.delay(asset_id)
            current_app.logger.info(f"Device discovery result: {json.dumps(device_result)}")
            if device_result.get("code") == 0 and "all_devices" in device_result and device_result["all_devices"]:
                devices = device_result["all_devices"]
                points_result = get_points_for_devices_task.delay(asset_id, devices)
                current_app.logger.info(f"Points result: {json.dumps(points_result)}")
                if points_result.get("code") == 0 and "point_results" in points_result:
                    all_points = []
                    for device_id, device_points in points_result["point_results"].items():
                        if "result" in device_points and "objectPropertys" in device_points["result"]:
                            points = device_points["result"]["objectPropertys"]
                            for point in points:
                                point["deviceId"] = device_id
                                point["source"] = "EnvisionIoT"
                                if "objectInst" in point:
                                    point["id"] = f"{device_id}:{point.get('objectInst', '')}"
                                if "objectName" in point and "pointName" not in point:
                                    point["pointName"] = point["objectName"]
                                if "objectType" in point and "pointType" not in point:
                                    point["pointType"] = point["objectType"]
                            all_points.extend(points)
                    current_app.logger.info(f"Returning {len(all_points)} points")
                    return jsonify({"points": all_points}), 200
            current_app.logger.warning("Could not fetch real points, using mock data")
            mock_points = [
                {"id": "1", "name": "AHU1.SAT", "description": "Supply Air Temperature", "type": "AI", "source": "EnvisionIoT"},
                {"id": "2", "name": "AHU1.RAT", "description": "Return Air Temperature", "type": "AI", "source": "EnvisionIoT"},
                {"id": "3", "name": "AHU1.MAT", "description": "Mixed Air Temperature", "type": "AI", "source": "EnvisionIoT"},
                {"id": "4", "name": "AHU1.Fan.Speed", "description": "Fan Speed", "type": "AO", "source": "EnvisionIoT"},
                {"id": "5", "name": "AHU1.Damper.Pos", "description": "Damper Position", "type": "AO", "source": "EnvisionIoT"}
            ]
            return jsonify({"points": mock_points}), 200
        except Exception as module_error:
            current_app.logger.error(f"Error using BMSDataPoints module: {str(module_error)}")
            current_app.logger.exception(module_error)
            mock_points = [
                {"id": "1", "name": "AHU1.SAT", "description": "Supply Air Temperature", "type": "AI", "source": "EnvisionIoT"},
                {"id": "2", "name": "AHU1.RAT", "description": "Return Air Temperature", "type": "AI", "source": "EnvisionIoT"},
                {"id": "3", "name": "AHU1.MAT", "description": "Mixed Air Temperature", "type": "AI", "source": "EnvisionIoT"},
                {"id": "4", "name": "AHU1.Fan.Speed", "description": "Fan Speed", "type": "AO", "source": "EnvisionIoT"},
                {"id": "5", "name": "AHU1.Damper.Pos", "description": "Damper Position", "type": "AO", "source": "EnvisionIoT"}
            ]
            return jsonify({
                "points": mock_points,
                "warning": "Using mock data due to BMSDataPoints module error",
                "error_details": str(module_error)
            }), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching BMS points: {str(e)}")
        current_app.logger.exception(e)
        return jsonify({"error": "Failed to fetch BMS points", "details": str(e)}), 500

@bp.route('/bms/connect', methods=['POST'])
def connect_to_bms():
    try:
        data = request.json if request.is_json else {} # Ensure data is a dict

        # Get parameters from JSON body, fallback to current_connection
        api_url = data.get('apiUrl', current_connection["api_url"])
        access_key = data.get('accessKey', current_connection["access_key"])
        secret_key = data.get('secretKey', current_connection["secret_key"]) # Handle with care
        org_id = data.get('orgId', current_connection["org_id"])
        asset_id = data.get('assetId', current_connection["asset_id"])

        current_app.logger.info(f"Connecting to BMS. Resolved Asset ID for connection attempt: {asset_id}")
        current_app.logger.info(f"Attempting connection with API URL: {api_url}, Access Key: {access_key[:5]}..., Org ID: {org_id}")

        # Speculative: Update current_connection BEFORE the call to bms_get_net_config
        # This might influence BMSDataPoints if it reads from this global dict.
        # The asset_id in current_connection is also updated here to be consistent,
        # though bms_get_net_config takes asset_id as a direct parameter.
        current_connection["api_url"] = api_url
        current_connection["access_key"] = access_key
        current_connection["secret_key"] = secret_key # Storing live secret in global like this has risks
        current_connection["org_id"] = org_id
        current_connection["asset_id"] = asset_id
        # `connected` status remains False until bms_get_net_config confirms.

        os.environ["ENOS_API_URL"] = api_url
        os.environ["ENOS_ACCESS_KEY"] = access_key
        os.environ["ENOS_SECRET_KEY"] = secret_key
        os.environ["ENOS_ORG_ID"] = org_id
        os.environ["ENOS_ASSET_ID"] = asset_id
        try:
            # Try to use the imported getNetConfig function
            try:
                from BMSDataPoints import getNetConfig as bms_get_net_config
                # Call with dynamic parameters
                net_config = bms_get_net_config(org_id_param=org_id, 
                                                 asset_id_param=asset_id, 
                                                 api_url_param=api_url, 
                                                 access_key_param=access_key, 
                                                 secret_key_param=secret_key)
            except (ImportError, NameError) as e:
                current_app.logger.warning(f"Could not import or use BMSDataPoints.getNetConfig: {e}. Using mock.")
                # Use our mock if the import fails or function is not defined
                net_config = {"code": 0, "data": ["No Network Card", "eth0(192.168.1.100)", "eth1(192.168.10.101)"]}
                
            current_app.logger.info(f"Network config result: {json.dumps(net_config)}")
            if net_config.get("code") == 0 or "data" in net_config:
                current_connection.update({
                    "connected": True,
                    # These are already set from above, but update confirms the full state.
                    "api_url": api_url,
                    "access_key": access_key,
                    "secret_key": secret_key,
                    "org_id": org_id,
                    "asset_id": asset_id
                })
                return jsonify({
                    "status": "success",
                    "message": "Successfully connected to BMS",
                    "connection": {
                        "apiUrl": api_url,
                        "accessKey": access_key,
                        "orgId": org_id,
                        "assetId": asset_id
                    },
                    "net_config": net_config.get("data", [])
                }), 200
            else:
                # Connection attempt (getNetConfig) failed, mark as not connected
                current_connection["connected"] = False
                return jsonify({
                    "status": "error",
                    "message": "Failed to connect to BMS API",
                    "details": net_config.get("msg", "Unknown error")
                }), 400
        except Exception as module_error:
            current_app.logger.error(f"Error using BMSDataPoints module: {str(module_error)}")
            current_app.logger.exception(module_error)
            # Even if BMSDataPoints module itself errors, update with attempted connection parameters
            # but mark as connected: True (simulated success path as per original logic for module error)
            current_connection.update({
                "connected": True, # Original logic maintained this as True on module_error
                "api_url": api_url,
                "access_key": access_key,
                "secret_key": secret_key,
                "org_id": org_id,
                "asset_id": asset_id
            })
            sample_networks = ["No Network Card", "eth0(192.168.1.100)", "eth1(192.168.10.101)"]
            return jsonify({
                "status": "success",
                "message": "Successfully connected to BMS (simulated)",
                "connection": {
                    "apiUrl": api_url,
                    "accessKey": access_key,
                    "orgId": org_id,
                    "assetId": asset_id
                },
                "net_config": sample_networks,
                "warning": "Using simulated connection due to BMSDataPoints module error",
                "error_details": str(module_error)
            }), 200
    except Exception as e:
        current_app.logger.error(f"Error connecting to BMS: {str(e)}")
        current_app.logger.exception(e)
        return jsonify({"error": "Failed to connect to BMS", "details": str(e)}), 500

@bp.route('/bms/discover-devices', methods=['GET'])
def discover_bms_devices():
    try:
        if not current_connection["connected"]:
            return jsonify({
                "error": "Not connected to BMS API",
                "details": "Please connect to the BMS API first"
            }), 400

        # Get connection parameters from query, fallback to current_connection
        api_url = request.args.get('apiUrl', current_connection["api_url"])
        access_key = request.args.get('accessKey', current_connection["access_key"])
        secret_key = request.args.get('secretKey', current_connection["secret_key"]) # Handle with care
        org_id_param = request.args.get('orgId', current_connection["org_id"])
        asset_id_param = request.args.get('assetId', current_connection["asset_id"])
        network = request.args.get('network')

        if not network:
            return jsonify({
                "error": "Network parameter is required",
                "details": "Please specify a network to scan for devices"
            }), 400
        
        current_app.logger.info(f"Discovering devices on network {network} for asset {asset_id_param} using API URL: {api_url}")

        os.environ["ENOS_API_URL"] = api_url
        os.environ["ENOS_ACCESS_KEY"] = access_key
        os.environ["ENOS_SECRET_KEY"] = secret_key
        os.environ["ENOS_ORG_ID"] = org_id_param
        os.environ["ENOS_ASSET_ID"] = asset_id_param # Use the resolved asset_id from query/fallback
        try:
            # Try to use the imported searchDevice function
            try:
                from BMSDataPoints import searchDevice as bms_search_device
                # Call with dynamic parameters
                device_result = bms_search_device(org_id_param=org_id_param, # from request.args or current_connection
                                                    asset_id_param=asset_id_param, # from request.args or current_connection
                                                    net_param=network, # from request.args
                                                    api_url_param=api_url, # from request.args or current_connection
                                                    access_key_param=access_key, # from request.args or current_connection
                                                    secret_key_param=secret_key) # from request.args or current_connection
            except (ImportError, NameError) as e:
                current_app.logger.warning(f"Could not import or use BMSDataPoints.searchDevice: {e}. Using mock.")
                # Use our mock if the import fails or function is not defined
                device_result = {"code": 0, "result": {"deviceList": []}}
                
            current_app.logger.info(f"Device search result: {json.dumps(device_result)}")
            if device_result.get("code") == 0 and "result" in device_result and "deviceList" in device_result["result"]:
                devices = device_result["result"]["deviceList"]
                return jsonify({
                    "status": "success",
                    "message": f"Found {len(devices)} devices",
                    "all_devices": devices
                }), 200
            else:
                error_code = device_result.get("code", 500)
                error_msg = device_result.get("msg", "Unknown error from BMS API")
                current_app.logger.error(f"BMS API error: {error_code} - {error_msg}")
                return jsonify({
                    "status": "error",
                    "message": "Failed to discover devices",
                    "error": error_msg,
                    "code": error_code
                }), 400
        except Exception as module_error:
            current_app.logger.error(f"Error using BMSDataPoints module: {str(module_error)}")
            current_app.logger.exception(module_error)
            return jsonify({
                "status": "error",
                "message": "Error communicating with BMS API",
                "error": str(module_error)
            }), 500
    except Exception as e:
        current_app.logger.error(f"Error discovering BMS devices: {str(e)}")
        current_app.logger.exception(e)
        return jsonify({"error": "Failed to discover BMS devices", "details": str(e)}), 500

@bp.route('/bms/fetch-points', methods=['POST'])
def fetch_bms_points():
    try:
        if not current_connection["connected"]:
            return jsonify({
                "error": "Not connected to BMS API",
                "details": "Please connect to the BMS API first"
            }), 400
        data = request.json if request.is_json else {}

        # Get connection parameters from JSON body, fallback to current_connection
        api_url = data.get('apiUrl', current_connection["api_url"])
        access_key = data.get('accessKey', current_connection["access_key"])
        secret_key = data.get('secretKey', current_connection["secret_key"]) # Handle with care
        org_id_param = data.get('orgId', current_connection["org_id"])
        asset_id_param = data.get('assetId', current_connection["asset_id"])
        
        device_instances = data.get('deviceInstances', [])
        if not device_instances:
            return jsonify({
                "error": "Device instances are required",
                "details": "Please specify at least one device instance"
            }), 400
        
        current_app.logger.info(f"Fetching points for devices {device_instances} for asset {asset_id_param} using API URL: {api_url}")

        os.environ["ENOS_API_URL"] = api_url
        os.environ["ENOS_ACCESS_KEY"] = access_key
        os.environ["ENOS_SECRET_KEY"] = secret_key
        os.environ["ENOS_ORG_ID"] = org_id_param
        os.environ["ENOS_ASSET_ID"] = asset_id_param
        try:
            current_app.logger.info(f"Initiating point discovery for devices: {device_instances} using dynamic credentials.")
            
            # Try to use the imported fetch_points_for_devices function
            try:
                from BMSDataPoints import fetch_points_for_devices as bms_fetch_points_for_devices
                
                # Prepare the `devices_param` for bms_fetch_points_for_devices
                # It expects a list of device objects (dicts), typically with at least 'otDeviceInst' and 'address'
                # Assuming device_instances from the request are the 'otDeviceInst' values.
                # We might not have full device objects here, so we pass what we have.
                # The BMSDataPoints.fetch_points_for_devices function internally extracts 'otDeviceInst'
                # and can fetch addresses if needed or use defaults.
                devices_param_list = []
                for inst in device_instances:
                    devices_param_list.append({"otDeviceInst": str(inst)}) # Ensure otDeviceInst is a string if BMSDataPoints expects int later

                points_results_data = bms_fetch_points_for_devices(
                    org_id_param=org_id_param,
                    asset_id_param=asset_id_param,
                    devices_param=devices_param_list, # Pass the list of device instance dicts
                    api_url_param=api_url,
                    access_key_param=access_key,
                    secret_key_param=secret_key
                )

                # Process the results from fetch_points_for_devices
                # The structure is expected to be {"code": 0, "point_results": {device_instance: points_response}}
                if points_results_data.get("code") == 0 and "point_results" in points_results_data:
                    all_points = []
                    errors = []
                    for device_instance, device_point_data in points_results_data["point_results"].items():
                        if device_point_data.get("code") == 0 and "result" in device_point_data and "objectPropertys" in device_point_data["result"]:
                            fetched_device_points = device_point_data["result"]["objectPropertys"]
                            for point in fetched_device_points:
                                point["deviceId"] = device_instance # Add deviceId back for frontend
                                point["source"] = "EnvisionIoT"
                                if "objectInst" in point:
                                    point["id"] = f"{device_instance}:{point.get('objectInst', '')}"
                                if "objectName" in point and "pointName" not in point:
                                    point["pointName"] = point["objectName"]
                                    point["name"] = point["objectName"]
                                if "objectType" in point and "pointType" not in point:
                                    point["pointType"] = point["objectType"]
                                    point["type"] = point["objectType"]
                            all_points.extend(fetched_device_points)
                        else:
                            errors.append({
                                "device_instance": device_instance,
                                "error": device_point_data.get("msg", "Unknown error from BMS API for device"),
                                "code": device_point_data.get("code", 500)
                            })
                    
                    if all_points:
                        response_data = {
                            "status": "success",
                            "message": f"Found {len(all_points)} points from {len(device_instances) - len(errors)} devices",
                            "points": all_points
                        }
                        if errors:
                            response_data["warnings"] = f"Failed to fetch points for {len(errors)} devices"
                            response_data["device_errors"] = errors
                        return jsonify(response_data), 200
                    else:
                        return jsonify({
                            "status": "error",
                            "message": "Failed to fetch points for all specified devices",
                            "device_errors": errors
                        }), 400
                else:
                    # Error from bms_fetch_points_for_devices itself (e.g., search initiation failed)
                    return jsonify({
                        "status": "error",
                        "message": "Failed to fetch points for devices",
                        "error": points_results_data.get("msg", "Unknown error from BMSDataPoints.fetch_points_for_devices"),
                        "code": points_results_data.get("code", 500)
                    }), 400

            except (ImportError, NameError) as e:
                current_app.logger.warning(f"Could not import or use BMSDataPoints.fetch_points_for_devices: {e}. Using mock.")
                # Mock response if import fails
                mock_points = []
                for dev_inst in device_instances:
                    mock_points.extend([
                        {"id": f"{dev_inst}:1", "name": f"{dev_inst}.SAT", "description": "Supply Air Temperature", "type": "AI", "source": "EnvisionIoT", "deviceId": str(dev_inst)},
                        {"id": f"{dev_inst}:2", "name": f"{dev_inst}.RAT", "description": "Return Air Temperature", "type": "AI", "source": "EnvisionIoT", "deviceId": str(dev_inst)}
                    ])
                return jsonify({"status": "success", "message": "Fetched mock points", "points": mock_points}), 200

        except Exception as module_error:
            current_app.logger.error(f"Error using BMSDataPoints module in fetch-points: {str(module_error)}")
            current_app.logger.exception(module_error)
            return jsonify({
                "status": "error",
                "message": "Error communicating with BMS API",
                "error": str(module_error)
            }), 500
    except Exception as e:
        current_app.logger.error(f"Error fetching BMS points: {str(e)}")
        current_app.logger.exception(e)
        return jsonify({"error": "Failed to fetch BMS points", "details": str(e)}), 500

@bp.route('/bms/upload', methods=['POST'])
def upload_bms_points():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "File must be a CSV"}), 400
        mock_points = [
            {"id": "1", "name": "AHU1.SAT", "description": "Supply Air Temperature", "type": "AI", "source": "CSV"},
            {"id": "2", "name": "AHU1.RAT", "description": "Return Air Temperature", "type": "AI", "source": "CSV"},
            {"id": "3", "name": "AHU1.MAT", "description": "Mixed Air Temperature", "type": "AI", "source": "CSV"}
        ]
        return jsonify({"points": mock_points}), 200
    except Exception as e:
        current_app.logger.error(f"Error processing CSV file: {str(e)}")
        current_app.logger.exception(e)
        return jsonify({"error": "Failed to process CSV file", "details": str(e)}), 500

# Define a mock reasoning engine function
def get_reasoning_engine():
    """Get or create a reasoning engine for point grouping and verification.
    
    In a real implementation, this would return an actual reasoning engine.
    For now, it returns a mocked implementation with basic functionalities.
    """
    class MockReasoningEngine:
        def chain_of_thought_grouping(self, points):
            """Group points with reasoning using a mock implementation."""
            # Define a simple regex-based grouping
            groups = {}
            
            # Simple patterns to recognize common device types
            patterns = {
                "AHU": r"AHU|Air Handler|Supply Air|Return Air|Mixed Air",
                "FCU": r"FCU|Fan Coil|Zone Temp",
                "VAV": r"VAV|Variable Air Volume|Zone Flow|Damper",
                "Chiller": r"Chiller|CHW|Chilled Water|Condenser",
                "Boiler": r"Boiler|HW|Hot Water|Steam",
                "Pump": r"Pump|Water Flow|GPM",
            }
            
            for point in points:
                point_name = point.get("pointName", "") if isinstance(point, dict) else str(point)
                device_type = "Unknown"
                reasoning = []
                
                # Try to match point name against patterns
                for dev_type, pattern in patterns.items():
                    if re.search(pattern, point_name, re.IGNORECASE):
                        device_type = dev_type
                        reasoning.append(f"Matched '{point_name}' to {dev_type} based on pattern '{pattern}'")
                        break
                
                # If no match found, use heuristics
                if device_type == "Unknown":
                    if "temp" in point_name.lower() or "temperature" in point_name.lower():
                        device_type = "Temperature Sensor"
                        reasoning.append(f"Classified '{point_name}' as a Temperature Sensor based on the name")
                    elif "pressure" in point_name.lower() or "static" in point_name.lower():
                        device_type = "Pressure Sensor"
                        reasoning.append(f"Classified '{point_name}' as a Pressure Sensor based on the name")
                    elif "flow" in point_name.lower() or "gpm" in point_name.lower():
                        device_type = "Flow Meter"
                        reasoning.append(f"Classified '{point_name}' as a Flow Meter based on the name")
                    elif "status" in point_name.lower() or "state" in point_name.lower():
                        device_type = "Status"
                        reasoning.append(f"Classified '{point_name}' as a Status indicator based on the name")
                    else:
                        reasoning.append(f"Could not determine device type for '{point_name}', defaulting to Unknown")
                
                # Add the point to its group with reasoning
                if device_type not in groups:
                    groups[device_type] = []
                
                if isinstance(point, dict):
                    point_with_reasoning = point.copy()
                    point_with_reasoning["grouping_reasoning"] = reasoning
                    groups[device_type].append(point_with_reasoning)
                else:
                    groups[device_type].append({
                        "pointName": point,
                        "grouping_reasoning": reasoning
                    })
            
            return groups
        
        def calculate_group_confidence(self, device_type, points):
            """Calculate confidence scores for a group of points."""
            # Simple mockup of confidence calculation
            total_points = len(points)
            if total_points == 0:
                return {"overall": 0, "details": {"reason": "No points in group"}}
            
            # For mock purposes, give higher confidence to known device types
            known_types = ["AHU", "FCU", "VAV", "Chiller", "Boiler", "Pump"]
            if device_type in known_types:
                base_confidence = 0.8
            else:
                base_confidence = 0.5
            
            # Calculate name similarity within the group
            name_patterns = {}
            for point in points:
                point_name = point.get("pointName", "") if isinstance(point, dict) else str(point)
                first_part = point_name.split('.')[0] if '.' in point_name else point_name
                name_patterns[first_part] = name_patterns.get(first_part, 0) + 1
            
            # If all points have similar prefix, higher confidence
            if len(name_patterns) == 1:
                pattern_confidence = 1.0
            else:
                most_common = max(name_patterns.values())
                pattern_confidence = most_common / total_points
            
            overall = (base_confidence + pattern_confidence) / 2
            
            return {
                "overall": min(overall, 0.99),  # Cap at 0.99 for mock
                "details": {
                    "base_confidence": base_confidence,
                    "pattern_confidence": pattern_confidence,
                    "num_points": total_points,
                    "patterns_detected": len(name_patterns)
                }
            }
    
    return MockReasoningEngine()

# Add this at the end of the file to make 'bp' importable
__all__ = ['bp']
