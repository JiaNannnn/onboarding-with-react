# EnOS Thing Model Upload with Token-Based Authentication

This script implements the official token-based authentication flow for EnOS APIs, obtaining an access token and using it to upload Thing Models.

## How the EnOS API Authentication Works

The EnOS platform provides API authentication via access tokens:

1. **Application Registration**: You must first register an application in the EnOS Management Console to get an access key (app key) and secret key (app secret).

2. **Token Acquisition**: Your application uses these credentials to request an access token from the EnOS token service.

3. **API Invocation**: The obtained token is included in the HTTP header for all subsequent API calls.

## Prerequisites

- Python 3.7 or higher
- Required Python packages (install via `pip install -r requirements.txt`):
  - requests
  - requests-toolbelt
- An application registered in the EnOS Management Console with:
  - Application access key (app key)
  - Application secret key (app secret)
  - Proper permissions for model management

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Edit the `token_upload.py` script to set your:
   - EnOS API Gateway URL (if different from default)
   - Batch import API URL (if different from default)
   - Application access key (app_key)
   - Application secret key (app_secret)
   - Model file path (if different from default)

## Usage

Simply run the script with your configured credentials:
```
python scripts/token_upload.py
```

## How It Works

The script follows these steps:

1. **Get Access Token**:
   - Generates a timestamp in milliseconds
   - Creates an encryption string: SHA256(appKey+timestamp+appSecret)
   - Sends these values to the token service API
   - Receives an access token with its expiry time (typically 2 hours)

2. **Upload Model with Token Authentication**:
   - Prepares a multipart form request with the model file
   - Adds an Authorization header with the Bearer token
   - Sends the request to the batch import API
   - Processes and displays the response

## Security Considerations

- Store your app secret securely and never commit it to version control
- The access token has a limited lifetime (usually 2 hours)
- Use HTTPS for all API communications

## Troubleshooting

1. **Token Acquisition Fails**:
   - Verify your app key and secret are correct
   - Check that your application has the necessary permissions
   - Ensure you're using the correct API Gateway URL

2. **Upload Fails with 401 Unauthorized**:
   - The token may have expired (tokens typically last 2 hours)
   - The token may not have the necessary permissions for uploading models

3. **Other Upload Failures**:
   - Check for proper formatting of your Thing Model file
   - Verify that all required fields in the multipart request are correct

## API References

- [Get Access Token API](https://support.enos-iot.com/docs/api/en/2.4.0/token/get_access_token.html) - Documentation for obtaining an access token 