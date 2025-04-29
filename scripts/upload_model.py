import json
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

def login_to_enos(url, auth_type, principal, credentials, expire_interval=3600):
    """
    Log in to EnOS using the IAM Login API.
    
    Args:
        url (str): Base URL for the EnOS API Gateway
        auth_type (int): Authentication type (0: EnOS, 1: LDAP)
        principal (str): Username/account name
        credentials (str): Password
        expire_interval (int): Session expiry time in seconds
        
    Returns:
        dict: Session information or None if login failed
    """
    # Try different URL formats for the login endpoint
    login_urls = [
        f"{url}/enos-iam-service/v2.0/login",
        f"{url}/api/enos-iam-service/v2.0/login",
        f"{url}/iam/v2.0/login"
    ]
    
    login_data = {
        "authType": auth_type,
        "principal": principal,
        "credentials": credentials,
        "expireInterval": expire_interval
    }
    for login_url in login_urls:
        print(f"\nAttempting login to: {login_url}")
        print(f"Login data: {json.dumps({k: v if k != 'credentials' else '******' for k, v in login_data.items()}, indent=2)}")
        
        try:
            response = requests.post(login_url, json=login_data)
            print(f"Status code: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Raw response: {response.text}")
            
            if response.status_code == 404:
                print("Endpoint not found, trying next URL...")
                continue
                
            try:
                if response.text and response.headers.get('Content-Type', '').startswith('application/json'):
                    response_json = response.json()
                    print(f"Response body: {json.dumps(response_json, indent=2)}")
                    
                    if response.status_code == 200 and response_json.get("successful", False):
                        print("Login successful!")
                        return response_json.get("session")
                    else:
                        error_code = response_json.get("status")
                        error_msg = response_json.get("message", "Unknown error")
                        print(f"Login failed! Error code: {error_code}, Message: {error_msg}")
                else:
                    print("Response is not in JSON format.")
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            print(f"Error during login attempt: {str(e)}")
    
    print("All login attempts failed.")
    return None

def upload_model(url, session_id, file_path, file_type="json", patch_update=True):
    """
    Upload a Thing Model using the batch import API with authentication.
    
    Args:
        url (str): Base URL for the EnOS API Gateway
        session_id (str): Session ID from successful login
        file_path (str): Path to the model file
        file_type (str): Type of the file (json or excel)
        patch_update (bool): Whether to patch update existing models
        
    Returns:
        dict: API response as JSON
    """
    import_url = f"{url}/dm-bff/rest/model/batchImportModels"
    
    # Create multipart form data
    multipart_data = MultipartEncoder(
        fields={
            'fileType': file_type,
            'patchUpdate': str(patch_update).lower(),
            'file': ('ThingModel.json', open(file_path, 'rb'), 'application/json')
        }
    )
    
    # Prepare headers with session ID for authentication
    headers = {
        'Content-Type': multipart_data.content_type,
        'Cookie': f'ENOS_IAM_SESSION_ID={session_id}'
    }
    
    try:
        response = requests.post(import_url, data=multipart_data, headers=headers)
        response_json = response.json()
        return response_json
    except Exception as e:
        print(f"Error during model upload: {str(e)}")
        return None

if __name__ == "__main__":
    # Configuration
    #https://apim-ppe1.envisioniot.com	
    base_url = "https://apim-ppe1.envisioniot.com"  # Replace with your actual EnOS environment URL
    model_file = "scripts/ThingModel_ABC_HVAC_CH.json"
    
    # Login credentials
    username = "nan.jia"  # Replace with your actual username
    password = "Enos2025!"  # Replace with your actual password
    
    # Login to get session
    session = login_to_enos(base_url, auth_type=0, principal=username, credentials=password)
    
    if session:
        # Extract session ID
        session_id = session.get("id")
        print(f"Session ID: {session_id}")
        
        # Upload the model using the session
        result = upload_model(base_url, session_id, model_file)
        
        # Print result
        print("Upload result:")
        print(json.dumps(result, indent=2))
    else:
        print("Authentication failed. Cannot proceed with model upload.")










# multipart/form-data; boundary=----WebKitFormBoundaryIleKNl3LqmAGg1Gp


# fileType: json
# patchUpdate: true
# file: (binary)