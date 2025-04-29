"""
Backend API for BMS Data Integration

This module initializes the Flask application and registers all 
API blueprints for network configuration, device discovery, and point retrieval.
"""

import os
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

def create_app(test_config=None):
    """
    Application factory function that creates and configures the Flask app.
    
    Args:
        test_config: Configuration dictionary for testing
        
    Returns:
        The configured Flask application
    """
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Enable CORS
    CORS(app)
    
    # Load configuration
    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_object('app.config.Config')
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Register blueprints
    from app.api import networks, devices, points
    
    app.register_blueprint(networks.bp)
    app.register_blueprint(devices.bp)
    app.register_blueprint(points.bp)
    
    # Initialize Swagger documentation
    swagger = Swagger(app)
    
    # Simple index route
    @app.route('/')
    def index():
        return {
            'status': 'ok',
            'message': 'BMS API Server is running'
        }
    
    return app
