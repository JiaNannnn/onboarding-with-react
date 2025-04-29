from flask import Blueprint, jsonify, request, redirect, url_for, current_app, make_response, send_from_directory
import requests
from app import celery
from app.bms.tasks import fetch_points_task, search_points_task, discover_devices_task, get_network_config_task, group_points_task
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
from io import StringIO
import csv
import re

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
                response.headers["Content-Disposition"] = "attachment; filename=enos_export.csv"
                response.headers["Content-type"] = "text/csv"
                return response
            else: return jsonify({"error": "No data to export"}), 400
        else:
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
