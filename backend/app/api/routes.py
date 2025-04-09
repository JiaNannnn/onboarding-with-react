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
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
    return response

@bp.route(f'/{API_VERSION}/map-points', methods=['POST', 'OPTIONS'])
def bms_map_points():
    """Map BMS points to EnOS points using AI-powered mapping."""
    # For OPTIONS requests (CORS preflight)
    if request.method == 'OPTIONS':
        return handle_options()
    
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        # Get points and configuration
        points = data.get('points', [])
        if not points:
            return jsonify({"success": False, "error": "No points provided"}), 400
            
        # Log the number of points
        current_app.logger.info(f"Mapping {len(points)} points to EnOS")
            
        # Initialize the EnOS mapper without the max_retries parameter
        mapper = EnOSMapper()
        
        # Map the points
        result = mapper.map_points(points)
        
        # Return the results
        if result is None:
            # Return a safe default response if result is None
            return jsonify({
                "success": False,
                "error": "Mapping operation produced no result",
                "mappings": [],
                "stats": {"total": len(points), "mapped": 0, "errors": len(points)}
            })
        
        # Ensure the response is properly serialized  
        return jsonify(result)
            
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
    
    # Save initial metadata
    with open(os.path.join(result_dir, "metadata.json"), 'w') as f:
        json.dump(metadata, f)
    
    # Get app instance for application context
    app = current_app._get_current_object()
    
    # Start the mapping process in a background thread
    def mapping_task():
        # Set up a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create application context for this thread
        with app.app_context():
            try:
                # Prepare initial results structure
                all_results = {
                    "success": True,
                    "mappings": [],
                    "stats": {"total": 0, "mapped": 0, "errors": 0}
                }
            
                # Handle improvement mapping or initial mapping
                if is_improvement_mapping:
                    # First, load the original mapping results
                    original_mapping_dir = os.path.join(tempfile.gettempdir(), f"mapping_task_{original_mapping_id}")
                    
                    if not os.path.exists(original_mapping_dir):
                        raise FileNotFoundError(f"Original mapping task directory not found: {original_mapping_dir}")
                    
                    # Load complete results from the original mapping
                    original_results_file = os.path.join(original_mapping_dir, "complete_results.json")
                    if not os.path.exists(original_results_file):
                        # Try to compile results from batch files if complete results don't exist
                        original_results = {"mappings": [], "stats": {"total": 0, "mapped": 0, "errors": 0}}
                        batch_files = [f for f in os.listdir(original_mapping_dir) if f.startswith("batch_") and f.endswith(".json")]
                        
                        for batch_file in batch_files:
                            with open(os.path.join(original_mapping_dir, batch_file), 'r') as f:
                                batch_data = json.load(f)
                                original_results["mappings"].extend(batch_data.get("mappings", []))
                                original_results["stats"]["total"] += batch_data.get("stats", {}).get("total", 0)
                                original_results["stats"]["mapped"] += batch_data.get("stats", {}).get("mapped", 0)
                                original_results["stats"]["errors"] += batch_data.get("stats", {}).get("errors", 0)
                    else:
                        # Load the complete results file
                        with open(original_results_file, 'r') as f:
                            original_results = json.load(f)
                    
                    original_mappings = original_results.get("mappings", [])
                    if not original_mappings:
                        raise ValueError("No mappings found in the original mapping task")
                    
                    app.logger.info(f"Loaded {len(original_mappings)} mappings from original task")
                    
                    # Filter mappings based on quality if needed
                    filtered_mappings = []
                    
                    if filter_quality == 'all':
                        # Process all mappings
                        filtered_mappings = original_mappings
                        app.logger.info("Processing ALL mappings for improvement")
                    else:
                        # Filter based on quality
                        for mapping in original_mappings:
                            quality_score = 0.0
                            
                            # Extract quality score from reflection data if available
                            if "reflection" in mapping:
                                quality_score = mapping["reflection"].get("quality_score", 0.0)
                            
                            # Apply quality filter
                            if (filter_quality == 'poor' and quality_score < 0.3) or \
                               (filter_quality == 'unacceptable' and quality_score < 0.2) or \
                               (filter_quality == 'below_fair' and quality_score < 0.5):
                                filtered_mappings.append(mapping)
                    
                    if not filtered_mappings and filter_quality != 'all':
                        app.logger.info(f"No mappings match the quality filter: {filter_quality}")
                        
                        # No matching mappings - complete with a message
                        metadata["status"] = "completed"
                        metadata["message"] = f"No mappings match the quality filter: {filter_quality}"
                        metadata["endTime"] = datetime.now().isoformat()
                        with open(os.path.join(result_dir, "metadata.json"), 'w') as f:
                            json.dump(metadata, f)
                            
                        all_results["message"] = f"No mappings match the quality filter: {filter_quality}"
                        with open(os.path.join(result_dir, "complete_results.json"), 'w') as f:
                            json.dump(all_results, f)
                            
                        return
                    
                    app.logger.info(f"Processing {len(filtered_mappings)} mappings for improvement")
                    
                    # Convert mappings back to points format for remapping
                    points_to_remap = []
                    for mapping in filtered_mappings:
                        # Extract original point data
                        if "original" in mapping:
                            # New nested format
                            point = {
                                "pointId": mapping["mapping"].get("pointId", ""),
                                "pointName": mapping["original"].get("pointName", ""),
                                "deviceType": mapping["original"].get("deviceType", ""),
                                "deviceId": mapping["original"].get("deviceId", ""),
                                "pointType": mapping["original"].get("pointType", ""),
                                "unit": mapping["original"].get("unit", ""),
                                "value": mapping["original"].get("value", "N/A")
                            }
                        else:
                            # Old flat format
                            point = {
                                "pointId": mapping.get("pointId", ""),
                                "pointName": mapping.get("pointName", ""),
                                "deviceType": mapping.get("deviceType", ""),
                                "deviceId": mapping.get("deviceId", ""),
                                "pointType": mapping.get("pointType", ""),
                                "unit": mapping.get("unit", ""),
                                "value": "N/A"
                            }
                        
                        points_to_remap.append(point)
                    
                    # Update metadata with total points
                    metadata["totalPoints"] = len(points_to_remap)
                    with open(os.path.join(result_dir, "metadata.json"), 'w') as f:
                        json.dump(metadata, f)
                    
                    # Process in batches of 20 points
                    batch_size = 20
                    total_batches = (len(points_to_remap) + batch_size - 1) // batch_size  # Ceiling division
                    
                    # Update metadata with total batches
                    metadata["totalBatches"] = total_batches
                    metadata["batchMode"] = True
                    metadata["batchSize"] = batch_size
                    with open(os.path.join(result_dir, "metadata.json"), 'w') as f:
                        json.dump(metadata, f)
                    
                    # Process in batches
                    batch_counter = 0
                    for i in range(0, len(points_to_remap), batch_size):
                        batch = points_to_remap[i:i+batch_size]
                        
                        # Enhanced processing: Apply improved mapping with device context
                        enhanced_config = mapping_config.copy()
                        enhanced_config["prioritizeFailedPatterns"] = True
                        enhanced_config["includeReflectionData"] = True
                        
                        # Map points with the enhanced configuration
                        batch_result = mapper.map_points(batch)
                        
                        # Save batch result
                        batch_counter += 1
                        batch_file = os.path.join(result_dir, f"batch_{batch_counter}.json")
                        with open(batch_file, 'w') as f:
                            json.dump(batch_result, f)
                        
                        # Update overall stats
                        all_results["mappings"].extend(batch_result.get("mappings", []))
                        all_results["stats"]["total"] += batch_result.get("stats", {}).get("total", 0)
                        all_results["stats"]["mapped"] += batch_result.get("stats", {}).get("mapped", 0)
                        all_results["stats"]["errors"] += batch_result.get("stats", {}).get("errors", 0)
                        
                        # Update progress in metadata
                        metadata["completedBatches"] = batch_counter
                        metadata["progress"] = (batch_counter / total_batches) * 100
                        with open(os.path.join(result_dir, "metadata.json"), 'w') as f:
                            json.dump(metadata, f)
                
                else:
                    # Regular initial mapping process
                    if mapping_config.get('batchMode', False):
                        # Group points by device type for batch processing
                        points_by_device_type = {}
                        for point in points:
                            device_type = point.get('deviceType', 'UNKNOWN')
                            if device_type not in points_by_device_type:
                                points_by_device_type[device_type] = []
                            points_by_device_type[device_type].append(point)
                        
                        # Prioritize specified device types first if provided
                        all_device_types = list(points_by_device_type.keys())
                        if device_types:
                            # Rearrange so specified types come first
                            prioritized_types = [dt for dt in device_types if dt in all_device_types]
                            remaining_types = [dt for dt in all_device_types if dt not in device_types]
                            ordered_device_types = prioritized_types + remaining_types
                        else:
                            ordered_device_types = all_device_types
                        
                        # Calculate total batches for progress tracking
                        total_batches = sum(len(points_by_device_type[dt]) // batch_size + 
                                         (1 if len(points_by_device_type[dt]) % batch_size > 0 else 0) 
                                         for dt in ordered_device_types)
                        
                        # Update metadata with total batches
                        metadata["totalBatches"] = total_batches
                        with open(os.path.join(result_dir, "metadata.json"), 'w') as f:
                            json.dump(metadata, f)
                        
                        batch_counter = 0
                        # Process each device type in batches
                        for device_type in ordered_device_types:
                            device_points = points_by_device_type[device_type]
                            
                            # Process this device type in batches
                            for i in range(0, len(device_points), batch_size):
                                batch = device_points[i:i+batch_size]
                                batch_result = mapper.map_points(batch)
                                
                                # Save batch result
                                batch_counter += 1
                                batch_file = os.path.join(result_dir, f"batch_{batch_counter}.json")
                                with open(batch_file, 'w') as f:
                                    json.dump(batch_result, f)
                                
                                # Update overall stats
                                all_results["mappings"].extend(batch_result.get("mappings", []))
                                all_results["stats"]["total"] += batch_result.get("stats", {}).get("total", 0)
                                all_results["stats"]["mapped"] += batch_result.get("stats", {}).get("mapped", 0)
                                all_results["stats"]["errors"] += batch_result.get("stats", {}).get("errors", 0)
                                
                                # Update progress in metadata
                                metadata["completedBatches"] = batch_counter
                                metadata["progress"] = (batch_counter / total_batches) * 100
                                with open(os.path.join(result_dir, "metadata.json"), 'w') as f:
                                    json.dump(metadata, f)
                    else:
                        # Non-batch mode: Map all points at once
                        map_result = mapper.map_points(points)
                        all_results = map_result
                    
                    # Final update: Mark as completed
                    metadata["status"] = "completed"
                    metadata["endTime"] = datetime.now().isoformat()
                    with open(os.path.join(result_dir, "metadata.json"), 'w') as f:
                        json.dump(metadata, f)

                    # Save complete results
                    all_results["success"] = True
                    with open(os.path.join(result_dir, "complete_results.json"), 'w') as f:
                        json.dump(all_results, f)

            except Exception as e:
                app.logger.error(f"Error during mapping task {task_id}: {e}\n{traceback.format_exc()}")
                metadata["status"] = "failed"
                metadata["error"] = str(e)
                metadata["endTime"] = datetime.now().isoformat()
                with open(os.path.join(result_dir, "metadata.json"), 'w') as f:
                    json.dump(metadata, f)
                
                # Save partial results if any exist
                all_results["success"] = False
                all_results["error"] = str(e)
                with open(os.path.join(result_dir, "complete_results.json"), 'w') as f:
                    json.dump(all_results, f)

        # Start the mapping task in a separate thread
        task = threading.Thread(target=mapping_task)
        task.daemon = True
        task.start()
        
        # Return the task ID for polling
        return jsonify({
            "success": True,
            "taskId": task_id,
            "message": f"{'Improvement' if is_improvement_mapping else 'Initial'} mapping process started",
            "status": "processing"
        })

    except Exception as e:
        current_app.logger.error(f"Error in map_points: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
