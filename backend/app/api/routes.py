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
            
    except Exception as e:
        current_app.logger.error(f"Error in map_points: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "mappings": [],
            "stats": {"total": 0, "mapped": 0, "errors": 1}
        }), 500
