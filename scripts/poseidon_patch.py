"""
Patched version of the poseidon module with fixes for handling app keys and secrets
without hyphens.
"""
import requests
import json
import hmac
import hashlib
from base64 import b64encode
import time
from typing import Optional, Dict, Any, Union
from urllib.parse import quote_plus

def urlopen(url: str, 
           data: Optional[str] = None, 
           key: str = "", 
           secret: str = "", 
           method: str = "GET", 
           content_type: str = "application/x-www-form-urlencoded",
           timeout: int = 10) -> requests.Response:
    """
    Patched version of poseidon.urlopen that handles app keys and secrets without hyphens.
    
    This is a modified version of the original poseidon.urlopen function that doesn't
    assume the key and secret contain hyphens.
    
    Args:
        url: The URL to make the request to
        data: The payload data (JSON string or None)
        key: The application key
        secret: The application secret
        method: HTTP method (GET, POST, etc.)
        content_type: Content type header
        timeout: Request timeout in seconds
        
    Returns:
        Response object
    """
    # Custom pin function that doesn't assume hyphen in key/secret
    def custom_pin(key, secret):
        try:
            # Original approach tries to split by hyphen
            if "-" in key and "-" in secret:
                app_config = [key.split("-")[1], secret.split("-")[1]]
            else:
                # Fallback for keys without hyphens - use the full key/secret
                app_config = [key, secret]
        except IndexError:
            # Another fallback if the split fails
            app_config = [key, secret]
            
        return app_config
    
    # Get app config values
    app_config = custom_pin(key, secret)
    
    # Create signature using key and secret
    timestamp = str(int(time.time() * 1000))
    
    # For GET requests with no data, ensure data is not None
    if data is None:
        data = ""
    
    # Calculate signature (similar to original poseidon implementation)
    content_md5 = hashlib.md5(data.encode('utf-8')).hexdigest()
    
    # Signature string
    string_to_sign = method + "\n" + content_md5 + "\n" + content_type + "\n" + timestamp
    
    # Create signature
    digest_maker = hmac.new(app_config[1].encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha1)
    signature = b64encode(digest_maker.digest()).decode('utf-8')
    
    # Create headers
    headers = {
        'Content-Type': content_type,
        'Accept': 'application/json',
        'Content-MD5': content_md5,
        'Authorization': 'EnOS ' + app_config[0] + ':' + signature,
        'timestamp': timestamp
    }
    
    # Make the request
    if method == 'GET':
        response = requests.get(url, headers=headers, timeout=timeout)
    elif method == 'POST':
        response = requests.post(url, data=data, headers=headers, timeout=timeout)
    elif method == 'PUT':
        response = requests.put(url, data=data, headers=headers, timeout=timeout)
    elif method == 'DELETE':
        response = requests.delete(url, data=data, headers=headers, timeout=timeout)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
    
    return response 