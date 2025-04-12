from flask import Blueprint, request, jsonify, current_app
from ..utils import handle_error
from .. import cache
from .mapping import BMSEnosMapper
from .reasoning import ReasoningEngine
from .app_logging import ReasoningLogger
from .llm_grouper import LLMGrouper
import os

@bms_bp.route('/group_points_llm', methods=['POST'])
def group_points_llm_endpoint():
    """
    Groups points from a specified CSV file using LLM.
    Expects JSON body with 'file_path' and optional 'point_column'.
    --- 
    # ... (Swagger documentation remains the same for now)
    """
    data = request.get_json()
    if not data or 'file_path' not in data:
        return jsonify({"error": "Missing 'file_path' in request body"}), 400
    
    # Construct the full path relative to the backend directory
    # IMPORTANT: This assumes the file_path provided is relative to the 'backend' directory.
    # Adjust if the path reference point is different.
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) # Gets backend directory
    relative_file_path = data['file_path']
    # Basic security check to prevent directory traversal
    if ".." in relative_file_path:
         return jsonify({"error": "Invalid file path specified."}), 400
    full_file_path = os.path.join(base_dir, relative_file_path)
    
    point_column = data.get('point_column', 'pointName') # Default column name
    chunk_size = data.get('chunk_size', 100) # Default chunk size
    
    # Ensure chunk_size is reasonable
    try:
        chunk_size = int(chunk_size)
        if chunk_size <= 0 or chunk_size > 1000: # Set practical limits
            raise ValueError("Chunk size out of range")
    except ValueError:
        return jsonify({"error": "Invalid 'chunk_size' parameter. Must be an integer between 1 and 1000."}), 400
        
    try:
        # Use the new LLM grouper
        grouper = LLMGrouper(chunk_size=chunk_size)
        grouped_data = grouper.group_points_from_csv(full_file_path, point_column)
        
        if "error" in grouped_data:
             # Handle errors reported by the grouper (e.g., file not found)
             return jsonify(grouped_data), 400
             
        return jsonify(grouped_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Error during LLM point grouping: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred during point grouping."}), 500 