"""
Configuration module for the BMS API.

This module loads configuration from environment variables and provides
sensible defaults for development.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Base configuration class for the application."""
    
    # Flask configuration
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    
    # API Information for Swagger
    API_TITLE = "BMS Data Integration API"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "API for BMS device discovery and point retrieval"
    
    # EnOS API Configuration
    ENOS_API_URL = os.getenv('ENOS_API_URL', 'https://ag-eu2.envisioniot.com')
    ENOS_ACCESS_KEY = os.getenv('ENOS_ACCESS_KEY', '')
    ENOS_SECRET_KEY = os.getenv('ENOS_SECRET_KEY', '')
    ENOS_ORG_ID = os.getenv('ENOS_ORG_ID', '')
    
    # Default Asset ID (can be overridden in requests)
    DEFAULT_ASSET_ID = os.getenv('DEFAULT_ASSET_ID', '')
    
    # Results directory for storing BMS data
    RESULTS_DIR = os.getenv('RESULTS_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/results'))
    
    # Ensure results directory exists
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Swagger configuration
    SWAGGER = {
        'title': API_TITLE,
        'uiversion': 3,
        'version': API_VERSION,
        'description': API_DESCRIPTION,
        'termsOfService': '',
        'specs_route': '/apidocs/',
        'securityDefinitions': {
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header'
            }
        }
    }


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # In production, all keys should come from environment variables
    # with no defaults
