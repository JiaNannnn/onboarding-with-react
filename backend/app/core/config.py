"""
Configuration module for the application.

This module provides configuration settings for the application,
with default values for testing.
"""

import os
from typing import List

class Settings:
    """Settings class that loads configuration from environment variables."""
    
    # API settings
    API_PREFIX: str = "/api"
    PROJECT_NAME: str = "BACnet API"
    PROJECT_DESCRIPTION: str = "API for BACnet device discovery and management"
    PROJECT_VERSION: str = "0.1.0"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # Static files
    SERVE_STATIC_FILES: bool = False
    
    # EnOS API credentials
    ENOS_API_URL: str = os.getenv("ENOS_API_URL", "https://api.example.com")
    ENOS_ACCESS_KEY: str = os.getenv("ENOS_ACCESS_KEY", "test_access_key")
    ENOS_SECRET_KEY: str = os.getenv("ENOS_SECRET_KEY", "test_secret_key")
    ENOS_ORG_ID: str = os.getenv("ENOS_ORG_ID", "test_org_id")
    

# Create settings instance
settings = Settings() 