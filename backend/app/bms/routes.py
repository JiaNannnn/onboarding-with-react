from flask import Blueprint, request, jsonify, current_app
from app.bms.utils import EnOSClient
from app.bms.tasks import fetch_points_task, search_points_task, discover_devices_task, get_network_config_task
from app.bms.mapping import EnOSMapper
from app.bms.reflection import ReflectionSystem, MappingMemorySystem, PatternAnalysisEngine, QualityAssessmentFramework
from app.bms.reasoning import ReasoningEngine
from app.bms.logging import ReasoningLogger
from app.bms.grouping import DeviceGrouper
from typing import List, Dict, Any, Optional
import uuid
import logging
from . import bp

# Initialize reflection system
reflection_system = ReflectionSystem()

# Initialize reasoning logger
reasoning_logger = ReasoningLogger()

# Function to get or create mapper
def get_mapper():
    """Get or create EnOSMapper instance."""
    if not hasattr(current_app, "enos_mapper"):
        current_app.enos_mapper = EnOSMapper()
    return current_app.enos_mapper

# Function to get or create reasoning engine
def get_reasoning_engine():
    """Get or create ReasoningEngine instance."""
    if not hasattr(current_app, "reasoning_engine"):
        mapper = get_mapper()
        current_app.reasoning_engine = ReasoningEngine(
            mapper.enos_schema,
            reasoning_logger,
            mapper.mapping_agent
        )
    return current_app.reasoning_engine

# Function to get or create grouper
def get_grouper():
    """Get or create DeviceGrouper instance."""
    if not hasattr(current_app, "device_grouper"):
        current_app.device_grouper = DeviceGrouper()
    return current_app.device_grouper

@bp.route('/fetch-points', methods=['POST'])
def fetch_points():
    """Endpoint to fetch BMS points"""
    # Get request parameters
    data = request.json
    asset_id = data.get('asset_id')
    device_instances = data.get('device_instances', [])
    protocol = data.get('protocol', 'bacnet')
    
    # Validation
    if not asset_id:
        return jsonify({"error": "Missing asset_id parameter", "code": "MISSING_PARAMS"}), 400
    
    if not device_instances:
        return jsonify({"error": "Missing device_instances parameter", "code": "MISSING_PARAMS"}), 400
    
    # Convert to integers if they're strings
    device_instances = [int(d) if isinstance(d, str) else d for d in device_instances]
    
    # Start search task
    task = search_points_task.delay(asset_id, device_instances, protocol)
    
    return jsonify({
        "message": "Points search initiated",
        "task_id": task.id,
        "status": "processing"
    }), 202

@bp.route('/fetch-points/<task_id>', methods=['GET'])
def get_points_status(task_id):
    """Check status of a points search task"""
    # Get task status
    task = search_points_task.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'status': 'pending',
            'message': 'Task is pending'
        }
    elif task.state == 'FAILURE':
        response = {
            'status': 'failed',
            'message': str(task.info)
        }
    elif task.state == 'SUCCESS':
        response = {
            'status': 'completed',
            'result': task.result
        }
    else:
        response = {
            'status': 'processing',
            'message': 'Task is still processing'
        }
    
    return jsonify(response)

@bp.route('/device-points/<asset_id>/<device_instance>', methods=['GET'])
def get_device_points(asset_id, device_instance):
    """Fetch points for a specific device"""
    # Optional parameters
    device_address = request.args.get('address', 'unknown-ip')
    protocol = request.args.get('protocol', 'bacnet')
    
    # Convert device_instance to integer
    try:
        device_instance = int(device_instance)
    except ValueError:
        return jsonify({"error": "Invalid device_instance, must be an integer", "code": "INVALID_DEVICE"}), 400
    
    # Start fetch task
    task = fetch_points_task.delay(asset_id, device_instance, device_address, protocol)
    
    return jsonify({
        "message": f"Fetching points for device {device_instance}",
        "task_id": task.id,
        "status": "processing"
    }), 202

@bp.route('/device-points/status/<task_id>', methods=['GET'])
def get_device_points_status(task_id):
    """Check status of a device points fetch task"""
    # Get task status
    task = fetch_points_task.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'status': 'pending',
            'message': 'Task is pending'
        }
    elif task.state == 'FAILURE':
        response = {
            'status': 'failed',
            'message': str(task.info)
        }
    elif task.state == 'SUCCESS':
        response = {
            'status': 'success',
            'result': task.result
        }
    else:
        response = {
            'status': 'processing',
            'message': 'Task is still processing'
        }
    
    return jsonify(response)

@bp.route('/network-config/<asset_id>', methods=['GET'])
def get_network_config(asset_id):
    """Retrieve available network options for device discovery"""
    # Validate asset_id
    if not asset_id:
        return jsonify({"error": "Missing asset_id parameter", "code": "MISSING_PARAMS"}), 400
    
    # Start task to get network configuration
    task = get_network_config_task.delay(asset_id)
    
    # Return immediate response with task ID
    return jsonify({
        "message": f"Retrieving network configuration for asset {asset_id}",
        "task_id": task.id,
        "status": "processing"
    }), 202

@bp.route('/network-config/status/<task_id>', methods=['GET'])
def get_network_config_status(task_id):
    """Check status of a network configuration task"""
    # Get task status
    task = get_network_config_task.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'status': 'pending',
            'message': 'Task is pending'
        }
    elif task.state == 'FAILURE':
        response = {
            'status': 'failed',
            'message': str(task.info)
        }
    elif task.state == 'SUCCESS':
        response = {
            'status': 'success',
            'networks': task.result.get('networks', [])
        }
    else:
        response = {
            'status': 'processing',
            'message': 'Task is still processing'
        }
    
    return jsonify(response)

@bp.route('/discover-devices', methods=['POST'])
def discover_devices():
    """Initiate device discovery on selected networks"""
    # Get request parameters
    data = request.json
    asset_id = data.get('asset_id')
    networks = data.get('networks', [])
    protocol = data.get('protocol', 'bacnet')
    
    # Validation
    if not asset_id:
        return jsonify({"error": "Missing asset_id parameter", "code": "MISSING_PARAMS"}), 400
    
    if not networks:
        return jsonify({"error": "Missing networks parameter", "code": "MISSING_PARAMS"}), 400
    
    # Start device discovery task
    task = discover_devices_task.delay(asset_id, networks, protocol)
    
    return jsonify({
        "message": "Device discovery initiated",
        "task_id": task.id,
        "status": "processing"
    }), 202

@bp.route('/discover-devices/status/<task_id>', methods=['GET'])
def get_discover_devices_status(task_id):
    """Check status of a device discovery task"""
    # Get task status
    task = discover_devices_task.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'status': 'pending',
            'message': 'Task is pending'
        }
    elif task.state == 'FAILURE':
        response = {
            'status': 'failed',
            'message': str(task.info)
        }
    elif task.state == 'SUCCESS':
        response = {
            'status': 'success',
            'devices': task.result.get('devices', []),
            'count': task.result.get('count', 0)
        }
    else:
        response = {
            'status': 'processing',
            'message': 'Task is still processing'
        }
    
    return jsonify(response) 

# Reflection Layer Endpoints

@bp.route('/reflection/stats', methods=['GET'])
def get_reflection_stats():
    """Get statistics about the reflection system"""
    try:
        stats = reflection_system.get_reflection_stats()
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        current_app.logger.error(f"Error getting reflection stats: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@bp.route('/reflection/analyze', methods=['POST'])
def analyze_mappings():
    """Analyze a batch of mappings to extract patterns and insights"""
    try:
        data = request.json
        mappings = data.get('mappings', [])
        
        if not mappings:
            return jsonify({
                "success": False,
                "error": "No mappings provided"
            }), 400
            
        analysis = reflection_system.analyze_mappings(mappings)
        
        return jsonify({
            "success": True,
            "analysis": analysis
        })
    except Exception as e:
        current_app.logger.error(f"Error analyzing mappings: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@bp.route('/reflection/suggest', methods=['POST'])
def suggest_mapping():
    """Suggest a mapping for a point based on reflection data"""
    try:
        data = request.json
        point = data.get('point', {})
        
        if not point or not point.get('pointName') or not point.get('deviceType'):
            return jsonify({
                "success": False,
                "error": "Invalid or missing point data"
            }), 400
            
        suggestion = reflection_system.suggest_mapping(point)
        
        return jsonify({
            "success": True,
            "suggestion": suggestion
        })
    except Exception as e:
        current_app.logger.error(f"Error suggesting mapping: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@bp.route('/reflection/patterns', methods=['POST'])
def extract_patterns():
    """Extract patterns from a list of points"""
    try:
        data = request.json
        points = data.get('points', [])
        
        if not points:
            return jsonify({
                "success": False,
                "error": "No points provided"
            }), 400
            
        patterns = reflection_system.pattern_analysis.extract_patterns(points)
        
        return jsonify({
            "success": True,
            "patterns": patterns
        })
    except Exception as e:
        current_app.logger.error(f"Error extracting patterns: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@bp.route('/reflection/quality', methods=['POST'])
def assess_quality():
    """Assess mapping quality using the reflection system.
    
    Request body:
    {
        "mappings": [
            {
                "original": { ... point data ... },
                "mapping": { ... mapping result ... }
            },
            ...
        ]
    }
    """
    # Get request data
    data = request.json
    
    if not data or "mappings" not in data:
        return jsonify({"error": "Missing mappings data"}), 400
    
    # Assess quality
    quality_assessment = reflection_system.quality_framework.assess_mappings(data["mappings"])
    
    return jsonify(quality_assessment)

@bp.route('/points/map-with-reasoning', methods=['POST'])
def map_points_with_reasoning():
    """Map BMS points to EnOS points with reasoning capabilities.
    
    Request body:
    {
        "points_data": [
            {
                "pointId": "point-1",
                "pointName": "AHU.ReturnAirTemp",
                "deviceType": "AHU",
                "deviceId": "AHU-1",
                "unit": "°C",
                "description": "Return air temperature"
            },
            ...
        ],
        "reasoning_level": 1  # optional, default 1
    }
    """
    # Get request data
    data = request.json
    
    if not data or not data.get("points_data"):
        return jsonify({"error": "Missing points_data"}), 400
    
    # Extract parameters
    points_data = data["points_data"]
    reasoning_level = data.get("reasoning_level", 1)
    
    # Generate operation ID for tracking progress
    operation_id = str(uuid.uuid4())
    
    # Initialize progress
    total_points = len(points_data)
    reasoning_logger.log_progress(
        operation_id,
        "map_with_reasoning",
        total_points,
        0,
        "started",
        {"reasoning_level": reasoning_level}
    )
    
    try:
        # Get mapper and reasoning engine
        mapper = get_mapper()
        reasoning_engine = get_reasoning_engine()
        
        # Process points in batches of 20
        batch_size = 20
        all_results = []
        
        for i in range(0, total_points, batch_size):
            # Get current batch
            current_batch = points_data[i:i+batch_size]
            batch_size_actual = len(current_batch)
            
            # Group points based on device type
            grouped_points = reasoning_engine.chain_of_thought_grouping(current_batch)
            
            # Process each group
            batch_results = []
            
            for device_type, device_points in grouped_points.items():
                # Generate reasoning for each point
                for point in device_points:
                    # Extract point info
                    point_id = point.get("pointId", "unknown")
                    
                    # Generate chain of thought reasoning
                    reasoning_chain = reasoning_engine.chain_of_thought_mapping(point, device_type)
                    
                    # Create mapping context with reasoning
                    mapping_context = {
                        "point": point,
                        "device_type": device_type,
                        "reasoning_chain": reasoning_chain,
                        "reasoning_level": reasoning_level
                    }
                    
                    # Map the point using the standard mapping function
                    try:
                        mapping_result = mapper.process_ai_response(
                            mapper._get_ai_mapping(str(mapping_context)), 
                            point
                        )
                        
                        # Add reasoning chain to result
                        mapping_result["reasoning"] = {
                            "chain": reasoning_chain,
                            "level": reasoning_level
                        }
                        
                        # Store reasoning data
                        reasoning_engine.store_reasoning_data(
                            point_id,
                            reasoning_chain,
                            None,  # No reflection yet
                            mapping_result
                        )
                        
                        batch_results.append(mapping_result)
                        
                    except Exception as e:
                        # Log error
                        logging.error(f"Error mapping point {point_id}: {str(e)}")
                        
                        # Create error result
                        error_result = {
                            "original": {
                                "pointId": point_id,
                                "pointName": point.get("pointName", ""),
                                "deviceType": device_type
                            },
                            "mapping": {
                                "enosPoint": "unknown",
                                "status": "error"
                            },
                            "error": str(e),
                            "reasoning": {
                                "chain": reasoning_chain,
                                "level": reasoning_level
                            }
                        }
                        
                        batch_results.append(error_result)
            
            # Add batch results to overall results
            all_results.extend(batch_results)
            
            # Update progress
            reasoning_logger.log_progress(
                operation_id,
                "map_with_reasoning",
                total_points,
                min(i + batch_size, total_points),
                "processing",
                {"processed_batch": i // batch_size + 1, "total_batches": (total_points + batch_size - 1) // batch_size}
            )
        
        # Update final progress
        reasoning_logger.log_progress(
            operation_id,
            "map_with_reasoning",
            total_points,
            total_points,
            "completed",
            {"success": True}
        )
        
        # Return results
        return jsonify({
            "operation_id": operation_id,
            "status": "completed",
            "total_points": total_points,
            "reasoning_level": reasoning_level,
            "results": all_results
        })
        
    except Exception as e:
        # Log error
        logging.error(f"Error in map_points_with_reasoning: {str(e)}")
        
        # Update progress with error
        reasoning_logger.log_progress(
            operation_id,
            "map_with_reasoning",
            total_points,
            0,
            "failed",
            {"error": str(e)}
        )
        
        # Return error
        return jsonify({
            "operation_id": operation_id,
            "status": "failed",
            "error": str(e)
        }), 500

@bp.route('/points/reflect-and-remap/<point_id>', methods=['POST'])
def reflect_and_remap_point(point_id):
    """Reflect on a previous mapping attempt and try remapping.
    
    Path parameters:
        point_id: ID of the point to remap
        
    Request body:
    {
        "point_data": {
            "pointId": "point-1",
            "pointName": "AHU.ReturnAirTemp",
            "deviceType": "AHU",
            "deviceId": "AHU-1",
            "unit": "°C",
            "description": "Return air temperature"
        },
        "previous_result": {
            "original": { ... point data ... },
            "mapping": { ... mapping result ... },
            "reasoning": { ... reasoning data ... }
        }
    }
    """
    # Get request data
    data = request.json
    
    if not data or not data.get("point_data") or not data.get("previous_result"):
        return jsonify({"error": "Missing point_data or previous_result"}), 400
    
    # Extract parameters
    point_data = data["point_data"]
    previous_result = data["previous_result"]
    
    # Validate point ID
    if point_data.get("pointId", "") != point_id:
        return jsonify({"error": f"Point ID mismatch: {point_data.get('pointId', '')} != {point_id}"}), 400
    
    try:
        # Get mapper and reasoning engine
        mapper = get_mapper()
        reasoning_engine = get_reasoning_engine()
        
        # Generate operation ID for tracking progress
        operation_id = str(uuid.uuid4())
        
        # Initialize progress
        reasoning_logger.log_progress(
            operation_id,
            "reflect_and_remap",
            1,
            0,
            "started",
            {"point_id": point_id}
        )
        
        # Extract error type from previous result
        error_type = previous_result.get("reflection", {}).get("reason", "unknown")
        
        # Generate reflection
        reflection = reasoning_engine.reflect_on_mapping(
            point_data,
            previous_result,
            error_type
        )
        
        # Get the original reasoning chain
        original_reasoning = previous_result.get("reasoning", {}).get("chain", [])
        
        # Generate refined prompt
        device_type = point_data.get("deviceType", "unknown")
        prompt = reasoning_engine.generate_refined_prompt(
            point_data,
            original_reasoning,
            reflection
        )
        
        # Update progress
        reasoning_logger.log_progress(
            operation_id,
            "reflect_and_remap",
            1,
            0.5,
            "reflecting",
            {"reflection_generated": True}
        )
        
        # Run the LLM with refined prompt
        try:
            llm_response = mapper._get_ai_mapping(prompt)
            
            # Process and validate result
            new_result = mapper.process_ai_response(llm_response, point_data)
            
            # Add reflection to result
            new_result["reflection"] = {
                "analysis": reflection["analysis"],
                "previous_mapping": previous_result.get("mapping", {}).get("enosPoint", "unknown"),
                "success": new_result["mapping"]["enosPoint"] != "unknown"
            }
            
            # Store reasoning and reflection data
            reasoning_engine.store_reasoning_data(
                point_id,
                original_reasoning,
                reflection,
                new_result
            )
            
            # Update final progress
            reasoning_logger.log_progress(
                operation_id,
                "reflect_and_remap",
                1,
                1,
                "completed",
                {"success": new_result["reflection"]["success"]}
            )
            
            # Return result
            return jsonify({
                "operation_id": operation_id,
                "status": "completed",
                "result": new_result
            })
            
        except Exception as e:
            # Log error
            logging.error(f"Error remapping point {point_id}: {str(e)}")
            
            # Update progress with error
            reasoning_logger.log_progress(
                operation_id,
                "reflect_and_remap",
                1,
                0.5,
                "failed",
                {"error": str(e)}
            )
            
            # Return error
            return jsonify({
                "operation_id": operation_id,
                "status": "failed",
                "error": str(e)
            }), 500
            
    except Exception as e:
        # Log error
        logging.error(f"Error in reflect_and_remap_point: {str(e)}")
        
        # Return error
        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 500

@bp.route('/points/reflect-and-remap-batch', methods=['POST'])
def reflect_and_remap_points_batch():
    """Reflect on previous mapping attempts and try remapping multiple points at once.
    
    Request body:
    {
        "points_data": [
            {
                "pointId": "point-1",
                "pointName": "AHU.ReturnAirTemp",
                "deviceType": "AHU",
                "deviceId": "AHU-1",
                "unit": "°C",
                "description": "Return air temperature"
            },
            ...
        ],
        "previous_results": [
            {
                "original": { ... point data ... },
                "mapping": { ... mapping result ... },
                "reasoning": { ... reasoning data ... }
            },
            ...
        ],
        "batch_size": 20  # optional, default 20
    }
    """
    # Get request data
    data = request.json
    
    if not data or not data.get("points_data") or not data.get("previous_results"):
        return jsonify({"error": "Missing points_data or previous_results"}), 400
    
    # Extract parameters
    points_data = data["points_data"]
    previous_results = data["previous_results"]
    batch_size = data.get("batch_size", 20)
    
    # Validate input lists have same length
    if len(points_data) != len(previous_results):
        return jsonify({"error": "Points data and previous results must have the same length"}), 400
    
    # Generate operation ID for tracking progress
    operation_id = str(uuid.uuid4())
    
    # Initialize progress
    total_points = len(points_data)
    reasoning_logger.log_progress(
        operation_id,
        "reflect_and_remap_batch",
        total_points,
        0,
        "started",
        {"batch_size": batch_size}
    )
    
    try:
        # Get mapper and reasoning engine
        mapper = get_mapper()
        reasoning_engine = get_reasoning_engine()
        
        # Process points in batches
        all_results = []
        
        for i in range(0, total_points, batch_size):
            # Get current batch
            current_batch_points = points_data[i:i+batch_size]
            current_batch_results = previous_results[i:i+batch_size]
            batch_size_actual = len(current_batch_points)
            
            # Process each point in the batch
            batch_results = []
            
            for j, point_data in enumerate(current_batch_points):
                # Get point ID and previous result
                point_id = point_data.get("pointId", f"unknown_{i+j}")
                previous_result = current_batch_results[j]
                
                # Extract error type from previous result
                error_type = previous_result.get("reflection", {}).get("reason", "unknown")
                
                # Generate reflection
                reflection = reasoning_engine.reflect_on_mapping(
                    point_data,
                    previous_result,
                    error_type
                )
                
                # Get the original reasoning chain
                original_reasoning = previous_result.get("reasoning", {}).get("chain", [])
                
                # Generate refined prompt
                device_type = point_data.get("deviceType", "unknown")
                prompt = reasoning_engine.generate_refined_prompt(
                    point_data,
                    original_reasoning,
                    reflection
                )
                
                try:
                    # Run the LLM with refined prompt
                    llm_response = mapper._get_ai_mapping(prompt)
                    
                    # Process and validate result
                    new_result = mapper.process_ai_response(llm_response, point_data)
                    
                    # Add reflection to result
                    new_result["reflection"] = {
                        "analysis": reflection["analysis"],
                        "previous_mapping": previous_result.get("mapping", {}).get("enosPoint", "unknown"),
                        "success": new_result["mapping"]["enosPoint"] != "unknown"
                    }
                    
                    # Store reasoning and reflection data
                    reasoning_engine.store_reasoning_data(
                        point_id,
                        original_reasoning,
                        reflection,
                        new_result
                    )
                    
                    batch_results.append(new_result)
                    
                except Exception as e:
                    # Log error
                    logging.error(f"Error remapping point {point_id}: {str(e)}")
                    
                    # Create error result
                    error_result = {
                        "original": {
                            "pointId": point_id,
                            "pointName": point_data.get("pointName", ""),
                            "deviceType": device_type
                        },
                        "mapping": {
                            "enosPoint": "unknown",
                            "status": "error"
                        },
                        "error": str(e),
                        "reflection": {
                            "analysis": reflection["analysis"] if reflection else [],
                            "previous_mapping": previous_result.get("mapping", {}).get("enosPoint", "unknown"),
                            "success": False
                        }
                    }
                    
                    batch_results.append(error_result)
            
            # Add batch results to overall results
            all_results.extend(batch_results)
            
            # Update progress
            reasoning_logger.log_progress(
                operation_id,
                "reflect_and_remap_batch",
                total_points,
                min(i + batch_size, total_points),
                "processing",
                {"processed_batch": i // batch_size + 1, "total_batches": (total_points + batch_size - 1) // batch_size}
            )
        
        # Update final progress
        reasoning_logger.log_progress(
            operation_id,
            "reflect_and_remap_batch",
            total_points,
            total_points,
            "completed",
            {"success": True}
        )
        
        # Return results
        return jsonify({
            "operation_id": operation_id,
            "status": "completed",
            "total_points": total_points,
            "results": all_results
        })
        
    except Exception as e:
        # Log error
        logging.error(f"Error in reflect_and_remap_points_batch: {str(e)}")
        
        # Update progress with error
        reasoning_logger.log_progress(
            operation_id,
            "reflect_and_remap_batch",
            total_points,
            0,
            "failed",
            {"error": str(e)}
        )
        
        # Return error
        return jsonify({
            "operation_id": operation_id,
            "status": "failed",
            "error": str(e)
        }), 500

@bp.route('/progress/<operation_id>', methods=['GET'])
def get_operation_progress(operation_id):
    """Get progress of an operation.
    
    Path parameters:
        operation_id: ID of the operation
    """
    # Get reasoning logger
    try:
        # Get progress
        progress = reasoning_logger.get_progress(operation_id)
        
        # Return progress
        return jsonify(progress)
        
    except Exception as e:
        # Log error
        logging.error(f"Error getting progress for operation {operation_id}: {str(e)}")
        
        # Return error
        return jsonify({
            "operation_id": operation_id,
            "status": "error",
            "error": str(e)
        }), 500

@bp.route('/progress-dashboard', methods=['GET'])
def progress_dashboard():
    """Serve the progress tracking dashboard."""
    return current_app.send_static_file('progress.html')

@bp.route('/points/ai-grouping', methods=['POST', 'OPTIONS'])
def ai_grouping():
    """
    Group BMS points using AI-powered semantic grouping.
    
    This endpoint uses Chain of Thought (CoT) reasoning to analyze point names
    and group them by device type and device instance.
    """
    # For OPTIONS requests (CORS preflight)
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
    
    try:
        # Get request data
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        # Get points
        points = data.get('points', [])
        if not points:
            return jsonify({"success": False, "error": "No points provided"}), 400
            
        # Log the number of points
        current_app.logger.info(f"Grouping {len(points)} points using AI")
        
        # Initialize the device grouper
        grouper = get_grouper()
        
        # Generate operation ID for tracking progress
        operation_id = str(uuid.uuid4())
        reasoning_logger = get_reasoning_engine().logger
        
        # Initialize progress tracking - use log_progress instead of start_operation
        reasoning_logger.log_progress(
            operation_id=operation_id,
            operation_type="ai_grouping",
            total=len(points),
            current=0,
            status="started",
            details={"description": f"AI grouping of {len(points)} points"}
        )
        
        try:
            # Group the points using the AI-powered grouper
            grouped_points = grouper.process(points)
            
            # Calculate the number of grouped points
            total_grouped = sum(sum(len(pts) for pts in devices.values()) for devices in grouped_points.values())
            
            # Mark operation as complete - use log_progress instead of complete_operation
            reasoning_logger.log_progress(
                operation_id=operation_id,
                operation_type="ai_grouping",
                total=len(points),
                current=len(points),
                status="completed",
                details={
                    "success": True,
                    "stats": {
                        "total": len(points),
                        "grouped": total_grouped
                    }
                }
            )
            
            # Return the grouped points
            return jsonify({
                "success": True,
                "grouped_points": grouped_points,
                "operation_id": operation_id,
                "stats": {
                    "total": len(points),
                    "grouped": total_grouped,
                    "errors": 0
                }
            })
            
        except Exception as e:
            # Mark operation as failed - use log_progress instead of complete_operation
            reasoning_logger.log_progress(
                operation_id=operation_id,
                operation_type="ai_grouping",
                total=len(points),
                current=0,
                status="failed",
                details={"error": str(e)}
            )
            
            # Re-raise the exception to be caught by the outer try-except
            raise e
            
    except Exception as e:
        current_app.logger.error(f"Error in ai_grouping: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "grouped_points": {},
            "stats": {"total": len(points) if 'points' in locals() else 0, "grouped": 0, "errors": 1}
        }), 500

@bp.route('/points/group-with-reasoning', methods=['POST'])
def group_points_with_reasoning():
    """Group BMS points by device type with reasoning.
    
    Returns:
        Grouped points with reasoning chains
    """
    try:
        # Get points data from request
        data = request.json
        if not data or 'points' not in data:
            return jsonify({"success": False, "error": "Missing points data"}), 400
            
        points_data = data.get('points', [])
        if not points_data:
            return jsonify({"success": False, "error": "Empty points array"}), 400
            
        # Get reasoning engine
        reasoning_engine = get_reasoning_engine()
        
        # Group points with reasoning
        grouped_points = reasoning_engine._group_points_with_reasoning(points_data)
        
        # Format response
        response = {}
        
        for device_type, points in grouped_points.items():
            # Extract reasoning chains
            all_reasoning = []
            for point in points:
                if "grouping_reasoning" in point:
                    all_reasoning.extend(point["grouping_reasoning"])
                
                # Remove reasoning from individual points to reduce response size
                if "grouping_reasoning" in point:
                    del point["grouping_reasoning"]
            
            # Deduplicate reasoning steps
            unique_reasoning = list(dict.fromkeys(all_reasoning))
            
            response[device_type] = {
                "points": points,
                "reasoning": unique_reasoning
            }
        
        return jsonify({"success": True, "grouped_points": response})
        
    except Exception as e:
        current_app.logger.error(f"Error in group_points_with_reasoning: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@bp.route('/points/verify-groups', methods=['POST'])
def verify_point_groups():
    """Verify and finalize point groupings.
    
    Returns:
        Verified groups with additional confidence metrics
    """
    try:
        # Get verified groups from request
        data = request.json
        if not data or 'groups' not in data:
            return jsonify({"success": False, "error": "Missing groups data"}), 400
            
        verified_groups = data.get('groups', {})
        if not verified_groups:
            return jsonify({"success": False, "error": "Empty groups data"}), 400
            
        # Initialize reasoning engine
        reasoning_engine = get_reasoning_engine()
        
        # Verify each group
        verification_results = {}
        
        for device_type, group_data in verified_groups.items():
            points = group_data.get('points', [])
            
            # Skip empty groups
            if not points:
                continue
                
            # Calculate confidence scores
            confidence_scores = reasoning_engine.calculate_group_confidence(device_type, points)
            
            # Store results
            verification_results[device_type] = {
                "points": points,
                "confidence": confidence_scores["overall"],
                "confidence_details": confidence_scores["details"]
            }
        
        return jsonify({
            "success": True, 
            "verified_groups": verification_results
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in verify_point_groups: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500