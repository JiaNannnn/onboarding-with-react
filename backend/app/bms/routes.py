from flask import Blueprint, request, jsonify, current_app
from app.bms.utils import EnOSClient
from app.bms.tasks import fetch_points_task, search_points_task, discover_devices_task, get_network_config_task
from app.bms.mapping import EnOSMapper
from app.bms.reflection import ReflectionSystem, MappingMemorySystem, PatternAnalysisEngine, QualityAssessmentFramework
from . import bp

# Initialize reflection system
reflection_system = ReflectionSystem()

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
    """Assess quality of a mapping"""
    try:
        data = request.json
        mapping = data.get('mapping', {})
        reference_mappings = data.get('reference_mappings', [])
        
        if not mapping:
            return jsonify({
                "success": False,
                "error": "No mapping provided"
            }), 400
            
        quality_assessment = reflection_system.quality_assessment.assess_mapping_quality(
            mapping, 
            reference_mappings
        )
        
        return jsonify({
            "success": True,
            "quality_assessment": quality_assessment
        })
    except Exception as e:
        current_app.logger.error(f"Error assessing quality: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500