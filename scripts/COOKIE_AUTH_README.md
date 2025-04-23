# EnOS Thing Model Upload with Browser Cookie Authentication

This approach lets you upload Thing Models to EnOS using authentication cookies from your browser session, bypassing the need to implement the direct API login flow.

## Why this approach?

If direct API authentication is challenging due to:
- Unknown API endpoint structure
- Complex authentication flow
- Rate limiting or security measures

Using a browser cookie allows you to leverage your existing active session.

## Prerequisites

- Python 3.7 or higher
- Required Python packages (install via `pip install -r requirements.txt`):
  - requests
  - requests-toolbelt
- Active EnOS portal browser session

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## How to Use

1. **Log in to the EnOS portal in your browser**
   - Navigate to the EnOS portal and log in with your credentials

2. **Extract your session cookie**
   - Press F12 to open developer tools
   - Go to the Network tab
   - Perform any action (or refresh the page)
   - Click on any request to the portal
   - In the request details, look for the "Cookie" header under the "Headers" tab
   - Copy the entire cookie string (it will be a long string with name=value pairs)

3. **Run the script**
   ```
   python scripts/manual_cookie_upload.py
   ```

4. **Paste the cookie when prompted**
   - When the script asks for the cookie value, paste the entire cookie string

5. **Review the upload results**
   - The script will display the response from the API

## Important Notes

- **Security**: Cookies contain sensitive authentication information. Never share them or commit them to version control.
- **Session Expiry**: Browser cookies have an expiration time. If upload fails, you may need to refresh your session and get a new cookie.
- **Cookie Format**: Copy the entire cookie string exactly as shown in the request header, including all name=value pairs.

## Troubleshooting

1. **Upload Fails with 401 Unauthorized**
   - Your session may have expired. Log out, log back in, and get a fresh cookie.
   - Ensure you copied the entire cookie string correctly.

2. **Invalid Multipart Form Data**
   - The API may expect specific field names or formats. Check the error message for clues.

3. **File Not Found**
   - Verify the path to your Thing Model file is correct.

## Alternative Approaches

If this method doesn't work, consider:
1. Using official EnOS SDKs if available
2. Implementing browser automation to perform the upload
3. Contacting EnOS support for API documentation 