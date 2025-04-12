from flask import Blueprint, jsonify, request, current_app, send_from_directory
import os
import json
from datetime import datetime
# Import the correct tasks
from app.bms.tasks import search_points_task, fetch_points_task, discover_devices_task, get_network_config_task, group_points_task

# Create blueprint
bp = Blueprint('bms', __name__)

# Helper functions
def get_reasoning_engine():
    """Get or create a reasoning engine instance."""
    from .reasoning import ReasoningEngine
    return ReasoningEngine()

@bp.route('/points/group-with-reasoning', methods=['POST'])
def group_points_with_reasoning():
    """Group BMS points by device type with chain of thought reasoning.
    
    Returns:
        Grouped points with reasoning chains
    """
    # Get request data
    data = request.json
    if not data or not isinstance(data, list):
        return jsonify({"error": "Invalid request data. Expected list of points."}), 400
    
    # Initialize reasoning engine
    reasoning_engine = get_reasoning_engine()
    
    # Group points with reasoning
    try:
        grouped_points = reasoning_engine.chain_of_thought_grouping(data)
        
        # Format response
        response = {}
        
        for device_type, points in grouped_points.items():
            # Extract reasoning chains
            all_reasoning = []
            for point in points:
                if "grouping_reasoning" in point:
                    all_reasoning.extend(point["grouping_reasoning"])
                
                # Remove reasoning from individual points to reduce payload size
                if "grouping_reasoning" in point:
                    del point["grouping_reasoning"]
            
            # Deduplicate reasoning steps
            unique_reasoning = list(dict.fromkeys(all_reasoning))
            
            response[device_type] = {
                "points": points,
                "reasoning": unique_reasoning
            }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": f"Error during grouping: {str(e)}"}), 500

@bp.route('/points/verify-groups', methods=['POST'])
def verify_point_groups():
    """Verify and finalize point groupings.
    
    Returns:
        Verified groups with additional confidence metrics
    """
    # Get request data
    data = request.json
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid request data. Expected dictionary of groups."}), 400
            
    # Initialize reasoning engine
    reasoning_engine = get_reasoning_engine()
    
    # Verify each group
    try:
        verification_results = {}
        
        for device_type, group_data in data.items():
            if not isinstance(group_data, dict) or "points" not in group_data:
                continue
                
            points = group_data["points"]
            
            # Verify the group
            confidence_scores = reasoning_engine.calculate_group_confidence(device_type, points)
            
            # Store results
            verification_results[device_type] = {
                "points": points,
                "confidence": confidence_scores["overall"],
                "confidence_details": confidence_scores["details"]
            }
        
            # Preserve original reasoning if available
            if "reasoning" in group_data:
                verification_results[device_type]["reasoning"] = group_data["reasoning"]
        
        return jsonify(verification_results), 200
        
    except Exception as e:
        return jsonify({"error": f"Error during group verification: {str(e)}"}), 500

@bp.route('/group_points_llm', methods=['POST'])
def group_points_llm_endpoint():
    """
    Groups points from a specified CSV file using LLM (simulated).
    Expects JSON body with 'file_path' relative to backend dir and optional 'point_column', 'chunk_size'.
    """
    # Get request data
    data = request.json
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid request format. Expected JSON object."}), 400
    
    # Validate required parameters
    if 'file_path' not in data:
        return jsonify({"error": "Missing required parameter: file_path"}), 400
    
    file_path = data['file_path']
    point_column = data.get('point_column', 'pointName')
    chunk_size = data.get('chunk_size', 100)
    
    # Validate file path
    if not os.path.exists(file_path):
        return jsonify({"error": f"File not found: {file_path}"}), 404
    
    # Validate chunk size
    if not isinstance(chunk_size, int) or chunk_size < 1 or chunk_size > 1000:
        return jsonify({"error": "Invalid chunk_size. Must be an integer between 1 and 1000."}), 400
    
    try:
        # Get or create LLM grouper instance
        from .llm_grouper import LLMGrouper
        grouper = LLMGrouper()
        
        # Process the file with the LLM
        result = grouper.process_csv_file(file_path, point_column, chunk_size)
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({
            "error": f"Failed to process file: {str(e)}",
            "file_path": file_path,
            "point_column": point_column
        }), 500 