import json
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import os

def upload_model_with_cookie(url, file_path, cookie_value, file_type="json", patch_update=True):
    """
    Upload a Thing Model using the batch import API with authentication via a cookie.
    
    Args:
        url (str): Full URL for the batch import API
        file_path (str): Path to the model file
        cookie_value (str): Full cookie string from browser
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
        
        # Prepare headers with cookie for authentication
        headers = {
            'Content-Type': multipart_data.content_type,
            'Cookie': cookie_value
        }
        
        print(f"Attempting to upload to: {url}")
        
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
    batch_import_url = "https://portal-ppe1.envisioniot.com/dm-bff/rest/model/batchImportModels"
    model_file = "scripts/ThingModel_ABC_HVAC_CH.json"
    
    # Get cookie from browser
    print("===================================================")
    print("To get the cookie value:")
    print("1. Log in to the EnOS portal in your browser")
    print("2. Press F12 to open developer tools")
    print("3. Go to the Network tab")
    print("4. Refresh the page")
    print("5. Click on any request to the portal")
    print("6. Look for the 'Cookie' header in the request headers")
    print("7. Copy the entire cookie string")
    print("===================================================")
    
    cookie_value = input("Paste the cookie value from your browser: ")
    
    if not cookie_value:
        print("No cookie provided. Exiting.")
    else:
        # Try the upload with cookie authentication
        print("\nAttempting model upload with cookie authentication...")
        result = upload_model_with_cookie(batch_import_url, model_file, cookie_value)
        
        if result:
            print("\nUpload result summary:")
            if result.get("successful", False):
                print("Upload successful!")
            else:
                print(f"Upload failed: {result.get('message', 'Unknown error')}")
        else:
            print("\nUpload attempt returned no result") 