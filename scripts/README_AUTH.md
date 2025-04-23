# EnOS Thing Model Upload with Authentication

This script demonstrates how to use the EnOS IAM Login API for authentication and then use the obtained session to upload Thing Models through the batch import API.

## Prerequisites

- Python 3.7 or higher
- Required Python packages (install via `pip install -r requirements.txt`):
  - requests
  - requests-toolbelt

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Edit the `upload_model.py` script to set your:
   - EnOS environment URL (if different from the default)
   - Username/account name
   - Password
   - Model file path (if different from the default)

## Usage

Simply run the script:
```
python scripts/upload_model.py
```

## Script Workflow

1. Login to EnOS using the IAM Login API
2. Extract the session ID from the response
3. Use the session ID for authentication in the batch import models API
4. Display the upload results

## API Reference

The script uses the following EnOS APIs:

1. **Login API**:
   - Endpoint: `/enos-iam-service/v2.0/login`
   - Documentation: https://support.enos-iot.com/docs/iam-api/en/2.4.0/login

2. **Batch Import Models API**:
   - Endpoint: `/dm-bff/rest/model/batchImportModels`
   - This API requires authentication via session ID

## Troubleshooting

If you encounter issues:

1. **Login Failure**:
   - Verify your credentials
   - Check that your account is not locked
   - Ensure you're using the correct authentication type (EnOS or LDAP)

2. **Upload Failure**:
   - Verify that your session is valid (sessions expire after the interval specified during login)
   - Ensure your model file is correctly formatted
   - Check that you have the necessary permissions to upload models 