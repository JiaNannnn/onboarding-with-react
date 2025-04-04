import time
import json
import logging
from flask import request, g, current_app

class RequestLogger:
    """Middleware for logging API requests and responses."""
    
    @staticmethod
    def before_request():
        """Log request details before it's processed."""
        try:
            g.start_time = time.time()
            current_app.logger.info(f"=== API Request: {request.method} {request.path} ===")
            current_app.logger.info(f"Remote addr: {request.remote_addr}")
            
            # Log the headers (exclude sensitive ones)
            headers = dict(request.headers)
            if 'Authorization' in headers:
                headers['Authorization'] = '***REDACTED***'
            current_app.logger.info(f"Headers: {headers}")
            
            # Log the JSON body if present (exclude sensitive data)
            if request.is_json:
                safe_data = request.json.copy() if request.json else {}
                for key in ['access_key', 'secret_key', 'password', 'token', 'api_key']:
                    if key in safe_data:
                        safe_data[key] = '***REDACTED***'
                current_app.logger.info(f"JSON Body: {safe_data}")
        except Exception as e:
            # Use print as a fallback if logging itself is failing
            print(f"Error in before_request logging: {str(e)}")
    
    @staticmethod
    def after_request(response):
        """Log response details after it's processed."""
        try:
            # Calculate request duration
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                current_app.logger.info(f"Request completed in {duration:.4f} seconds")
            
            status_code = response.status_code
            current_app.logger.info(f"Response status: {status_code}")
            
            # Log response body for JSON responses (limit size)
            if response.content_type == 'application/json':
                try:
                    response_data = json.loads(response.get_data(as_text=True))
                    # Truncate large responses
                    if isinstance(response_data, dict) and len(str(response_data)) > 1000:
                        truncated_data = {}
                        for k, v in response_data.items():
                            if isinstance(v, (list, dict)) and len(str(v)) > 100:
                                truncated_data[k] = f"[{type(v).__name__} - TRUNCATED]"
                            else:
                                truncated_data[k] = v
                        current_app.logger.info(f"Response body: {truncated_data}")
                    else:
                        current_app.logger.info(f"Response body: {response_data}")
                except Exception as e:
                    current_app.logger.info(f"Could not parse JSON response: {str(e)}")
            
            current_app.logger.info("=== End of request ===")
        except Exception as e:
            # Use print as a fallback if logging itself is failing
            print(f"Error in after_request logging: {str(e)}")
        
        return response