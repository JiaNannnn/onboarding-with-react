from flask import Blueprint, jsonify, request, redirect, url_for, current_app, make_response
import requests
from app import celery
from app.bms.tasks import fetch_points_task, search_points_task, discover_devices_task, get_network_config_task
from app.bms.grouping import DeviceGrouper
from app.bms.mapping import EnOSMapper
from app.bms.utils import EnOSClient
from app.services.bms_service import bms_service
import pandas as pd
import os
import tempfile
import uuid
from datetime import datetime
from . import bp
import concurrent.futures
import traceback
import time
import json
import threading
import asyncio

# API Version prefix
API_VERSION = 'v1'

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

    # The code below seems to be part of another function but is misplaced
    # It should probably be part of another route handler
    # Let's comment it out for now until we can determine where it belongs

    '''
        # Add improvement-specific metadata
        metadata["originalMappingId"] = original_mapping_id
        metadata["filterQuality"] = filter_quality
        metadata["mappingConfig"] = mapping_config
        
        current_app.logger.info(f"Improvement mapping for task {original_mapping_id} with filter: {filter_quality}")
    else:
        # This is an initial mapping request
        if 'points' not in data:
            return jsonify({
                "success": False,
                "error": "Missing points data for initial mapping"
            }), 400
            
        points = data['points']
        mapping_config = data.get('mappingConfig', {})
        
        # Extract batch processing configuration
        batch_mode = mapping_config.get('batchMode', False)
        batch_size = mapping_config.get('batchSize', 50)
        device_types = mapping_config.get('deviceTypes', [])
        
        # Add initial mapping-specific metadata
        metadata["totalPoints"] = len(points)
        metadata["batchMode"] = batch_mode
        metadata["batchSize"] = batch_size
        metadata["deviceTypes"] = device_types
    '''
