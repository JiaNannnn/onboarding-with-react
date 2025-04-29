"""
Poseidon Client Module

This module provides utility functions for making API calls to the EnOS platform
using the same approach as in the original BMSDataPoints.py implementation.
"""

import json
import logging
import time
import base64
import hashlib
import hmac
import random
import string
import requests
from datetime import datetime
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

def generate_signature(
    access_key: str, 
    secret_key: str, 
    path: str,
    data: Dict[str, Any]
) -> str:
    """
    Generate signature for EnOS API call.
    
    Args:
        access_key: The access key for EnOS API
        secret_key: The secret key for EnOS API
        path: API path (e.g., "/bms/getPoints")
        data: Request data dictionary
        
    Returns:
        Signature string for the request
    """
    # Sort the data dictionary by key
    sorted_data = {k: data[k] for k in sorted(data.keys())}
    
    # Convert data to JSON string
    string_to_sign = json.dumps(sorted_data, separators=(',', ':'))
    
    # Current timestamp in milliseconds
    timestamp = int(time.time() * 1000)
    
    # Random string for nonce
    nonce = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
    
    # Signature string format: {path}|{access_key}|{timestamp}|{nonce}|{stringToSign}
    signature_string = f"{path}|{access_key}|{timestamp}|{nonce}|{string_to_sign}"
    
    # Generate HMAC-SHA256 signature
    hmac_obj = hmac.new(
        secret_key.encode('utf-8'),
        signature_string.encode('utf-8'),
        hashlib.sha256
    )
    signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')
    
    return signature, timestamp, nonce


def urlopen(
    access_key: str, 
    secret_key: str, 
    url: str, 
    data: Dict[str, Any],
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Make an API call to the EnOS platform.
    
    Args:
        access_key: The access key for EnOS API
        secret_key: The secret key for EnOS API
        url: Complete URL for the API call
        data: Request data dictionary
        timeout: Request timeout in seconds
        
    Returns:
        Response from the API as a dictionary
    """
    try:
        # Extract path from the URL
        path = url.split('.com', 1)[-1]
        if not path.startswith('/'):
            path = '/' + path
            
        # Get signature and related values
        signature, timestamp, nonce = generate_signature(access_key, secret_key, path, data)
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'apim-accesskey': access_key,
            'apim-signature': signature,
            'apim-timestamp': str(timestamp),
            'apim-nonce': nonce
        }
        
        # Log request details (debug level)
        logger.debug(f"Making API request to {url}")
        logger.debug(f"Headers: {headers}")
        logger.debug(f"Data: {json.dumps(data, indent=2)}")
        
        # Make the request
        response = requests.post(
            url, 
            headers=headers, 
            data=json.dumps(data),
            timeout=timeout
        )
        
        # Ensure response is JSON
        response.raise_for_status()
        result = response.json()
        
        # Log response (debug level)
        logger.debug(f"Response: {json.dumps(result, indent=2)}")
        
        return result
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        # Return error response in the same format as success responses
        return {
            "code": 500,
            "msg": f"Request error: {str(e)}",
            "data": None
        }
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return {
            "code": 500,
            "msg": f"JSON decode error: {str(e)}",
            "data": None
        }
    except Exception as e:
        logger.exception(f"Unexpected error in urlopen: {str(e)}")
        return {
            "code": 500,
            "msg": f"Unexpected error: {str(e)}",
            "data": None
        }


def make_api_call(
    access_key: str, 
    secret_key: str, 
    url: str, 
    data: Dict[str, Any],
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Make an API call to the EnOS platform. 
    
    This is a wrapper around urlopen for compatibility with tests that mock this function.
    
    Args:
        access_key: The access key for EnOS API
        secret_key: The secret key for EnOS API
        url: Complete URL for the API call
        data: Request data dictionary
        timeout: Request timeout in seconds
        
    Returns:
        Response from the API as a dictionary
    """
    return urlopen(access_key, secret_key, url, data, timeout) 