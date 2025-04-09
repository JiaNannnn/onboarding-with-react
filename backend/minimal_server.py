"""
Minimal Flask server that responds to the map-points endpoint.
This is for testing the frontend without needing the full backend to work.
"""

from flask import Flask, jsonify, request
import json

app = Flask(__name__)

# Set up CORS headers for all responses
@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response

# Handle OPTIONS requests for any route
@app.route('/<path:path>', methods=['OPTIONS'])
@app.route('/', methods=['OPTIONS'])
def handle_options(path=""):
    return jsonify({'status': 'ok'})

@app.route('/api/v1/map-points', methods=['POST', 'OPTIONS'])
def map_points():
    """Minimal implementation of map-points endpoint."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
        
    # Get request data
    data = request.json
    if not data or 'points' not in data:
        return jsonify({
            "success": False,
            "error": "Missing points data"
        }), 400
        
    points = data['points']
    if not points:
        return jsonify({
            "success": False,
            "error": "Empty points array"
        }), 400
        
    # Create a mock mapping response
    mappings = []
    for point in points:
        point_name = point.get('pointName', 'unknown')
        device_type = point.get('deviceType', 'unknown')
        
        # Create a mock mapping with confidence
        enos_point = f"{device_type}_raw_value"
        confidence = 0.85
        
        # Add to mappings array
        mappings.append({
            "original": point,
            "mapping": {
                "pointId": point.get('pointId', ''),
                "pointName": point_name,
                "enosPoint": enos_point,
                "confidence": confidence
            }
        })
    
    # Return the mock response
    return jsonify({
        "success": True,
        "mappings": mappings,
        "stats": {
            "total": len(points),
            "mapped": len(mappings),
            "errors": 0
        },
        "cacheStats": {
            "hits": 0,
            "misses": len(points),
            "apiCalls": len(points)
        }
    })

# Support both URL patterns for the AI grouping endpoint
@app.route('/api/points/ai-grouping', methods=['POST', 'OPTIONS'])
@app.route('/points/ai-grouping', methods=['POST', 'OPTIONS'])
def ai_grouping():
    """Endpoint to handle AI grouping of points."""
    # Handle OPTIONS requests explicitly
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
        
    # Get request data
    data = request.json
    if not data or 'points' not in data:
        return jsonify({
            "success": False,
            "error": "Missing points data"
        }), 400
        
    points = data['points']
    if not points:
        return jsonify({
            "success": False,
            "error": "Empty points array"
        }), 400
    
    # Create a mock AI grouping response
    # Group points by first letter to simulate AI grouping
    grouped_points = {}
    
    # Create some device types
    device_types = {
        'A': 'AHU',
        'B': 'Boiler',
        'C': 'Chiller',
        'F': 'Fan',
        'H': 'HVAC',
        'P': 'Pump',
        'T': 'Temperature',
        'V': 'Valve'
    }
    
    # Group points by first letter
    for point in points:
        if isinstance(point, str):
            point_name = point
        else:
            point_name = point.get('pointName', 'unknown')
            
        first_letter = point_name[0].upper() if point_name else 'U'
        device_type = device_types.get(first_letter, 'Other')
        
        if device_type not in grouped_points:
            grouped_points[device_type] = {}
            
        device_id = f"{device_type}_{first_letter}001"
        if device_id not in grouped_points[device_type]:
            grouped_points[device_type][device_id] = []
            
        grouped_points[device_type][device_id].append(point_name)
    
    # Return the mock response
    return jsonify({
        "success": True,
        "grouped_points": grouped_points,
        "stats": {
            "total": len(points),
            "grouped": len(points),
            "errors": 0
        }
    })

@app.route('/api/ping', methods=['GET'])
def ping():
    """Simple ping endpoint to test if the server is running."""
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    print("Starting minimal Flask server on http://localhost:5000")
    print("CORS support enabled for all routes")
    app.run(host='0.0.0.0', port=5000, debug=True) 