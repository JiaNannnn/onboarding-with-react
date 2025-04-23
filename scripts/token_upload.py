import json
import requests
import time
import hashlib
from requests_toolbelt.multipart.encoder import MultipartEncoder
import os

def get_access_token(apigw_url, app_key, app_secret):
    """
    Get an access token using the application credentials.
    
    Args:
        apigw_url (str): API Gateway URL
        app_key (str): Application access key
        app_secret (str): Application secret key
        
    Returns:
        tuple: (access_token, expire_time) or (None, None) if failed
    """
    token_url = f"{apigw_url}/apim-token-service/v2.0/token/get"
    
    # Generate timestamp (milliseconds)
    timestamp = int(time.time() * 1000)
    
    # Generate encryption according to the rule:
    # sha256(appKey+timestamp+appSecret).toLowerCase()
    plain_text = f"{app_key}{timestamp}{app_secret}"
    encryption = hashlib.sha256(plain_text.encode('utf-8')).hexdigest().lower()
    
    # Prepare request data
    request_data = {
        "appKey": app_key,
        "encryption": encryption,
        "timestamp": timestamp
    }
    
    print(f"Getting access token from: {token_url}")
    print(f"Request data: {json.dumps({k: v for k, v in request_data.items() if k != 'encryption'}, indent=2)}")
    
    try:
        response = requests.post(token_url, json=request_data)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_json = response.json()
            print(f"Response body: {json.dumps(response_json, indent=2)}")
            
            if response_json.get("status") == 0:  # Success status
                access_token = response_json.get("data", {}).get("accessToken")
                expire_time = response_json.get("data", {}).get("expire")
                print(f"Successfully obtained access token. Expires in {expire_time} seconds.")
                return access_token, expire_time
            else:
                error_msg = response_json.get("msg", "Unknown error")
                print(f"Token request failed! Error: {error_msg}")
                return None, None
        else:
            print(f"Failed to get token. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None, None
    except Exception as e:
        print(f"Exception during token request: {str(e)}")
        return None, None

def upload_model_with_token(url, file_path, access_token, file_type="json", patch_update=True):
    """
    Upload a Thing Model using the batch import API with token authentication.
    
    Args:
        url (str): Full URL for the batch import API
        file_path (str): Path to the model file
        access_token (str): Access token for authentication
        file_type (str): Type of the file (json or excel)
        patch_update (bool): Whether to patch update existing models
        
    Returns:
        dict: API response as JSON
    """
    # Ensure file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None
    
    print(f"Uploading file: {file_path}")
    print(f"File size: {os.path.getsize(file_path)} bytes")
    
    # Create multipart form data
    try:
        multipart_data = MultipartEncoder(
            fields={
                'fileType': file_type,
                'patchUpdate': str(patch_update).lower(),
                'file': ('ThingModel.json', open(file_path, 'rb'), 'application/json')
            }
        )
        
        # Prepare headers with access token
        headers = {
            'Content-Type': multipart_data.content_type,
            'Authorization': f'Bearer {access_token}'
        }
        
        print(f"Attempting to upload to: {url}")
        print(f"Using Authorization header with Bearer token")
        
        response = requests.post(url, data=multipart_data, headers=headers)
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        try:
            if response.text:
                print(f"Raw response: {response.text[:1000]}")  # Print first 1000 chars to avoid overwhelming output
                
                if response.headers.get('Content-Type', '').startswith('application/json'):
                    response_json = response.json()
                    print(f"Response as JSON: {json.dumps(response_json, indent=2)}")
                    return response_json
                else:
                    print("Response is not in JSON format")
                    return None
            else:
                print("Empty response received")
                return None
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {str(e)}")
            return None
    except Exception as e:
        print(f"Error during upload: {str(e)}")
        return None

if __name__ == "__main__":
    # Configuration
    apigw_url = "https://apim-ppe1.envisioniot.com"  # API Gateway URL
    batch_import_url = "https://portal-ppe1.envisioniot.com/dm-bff/rest/model/batchImportModels"  # Upload API URL
    model_file = "scripts/ThingModel_ABC_HVAC_CH.json"
    
    # Application credentials - REPLACE WITH YOUR ACTUAL CREDENTIALS
    app_key = "your_app_key"  # Replace with your app key
    app_secret = "your_app_secret"  # Replace with your app secret
    
    # Get access token
    print("Step 1: Getting access token...")
    access_token, expire_time = get_access_token(apigw_url, app_key, app_secret)
    
    if access_token:
        # Upload model using the token
        print("\nStep 2: Uploading model with access token...")
        result = upload_model_with_token(batch_import_url, model_file, access_token)
        
        if result:
            print("\nUpload result summary:")
            if result.get("successful", False):
                print("Upload successful!")
            else:
                print(f"Upload failed: {result.get('message', 'Unknown error')}")
        else:
            print("\nUpload attempt returned no result")
    else:
        print("Failed to get access token. Cannot proceed with model upload.") 