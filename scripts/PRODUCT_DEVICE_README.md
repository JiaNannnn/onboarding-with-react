# EnOS Product Creation Tool

This script provides a tool for creating products in the EnOS platform using the Connection Service API and the poseidon library for authentication.

## Features

- Create products with specified model ID
- Simple authentication using the poseidon library
- Automatically generates product names based on model ID

## Prerequisites

- Python 3.7 or higher
- Required Python packages:
  ```
  requests>=2.28.1
  poseidon>=0.1.0
  ```
- A valid model ID in your EnOS organization

## Installation

1. Ensure Python 3.7+ is installed:
   ```
   python --version
   ```

2. Install required dependencies:
   ```
   pip install requests poseidon
   ```

## Usage

### Creating a Product

The script has been simplified to require only the model ID, following the standard EnOS API for product creation as specified in the [EnOS API documentation](https://support.enos-iot.com/docs/connection-api/en/3.0.0/oldversion/create_product.html).

```bash
python scripts/create_product_device.py --model-id "your-model-id"
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `--apigw-url` | API Gateway URL (default: "https://apim-ppe1.envisioniot.com") |
| `--model-id` | Model ID for the product (required) |
| `--debug` | Enable debug logging (optional) |

## Output Format

The script generates a JSON output file with the product information:

```json
{
  "product": {
    "key": "product-key-value",
    "name": "model-id_Product",
    "model_id": "model-id"
  }
}
```

## Using the API Client in Your Code

You can also import the `EnOSConnectionClient` class for use in your own Python scripts:

```python
from scripts.create_product_device import EnOSConnectionClient

# Initialize client
client = EnOSConnectionClient(
    apigw_url="https://apim-ppe1.envisioniot.com",
    app_key="your-app-key",
    app_secret="your-app-secret",
    org_id="your-org-id"
)

# Create a product (this matches the EnOS API exactly)
product_key = client.create_product(
    product_name="My Product",
    model_id="your-model-id"
)
```

## Authentication

The script uses the poseidon library for authentication, which simplifies the process by automatically handling token generation and authentication. This eliminates the need for manually managing access tokens.

## Troubleshooting

1. **Authentication Issues**
   - Verify the hardcoded app key and secret are correct
   - Ensure your application has the necessary permissions in EnOS

2. **Product Creation Failures**
   - Confirm the model ID exists in your organization
   - Check that the product name is unique within your organization

## Security Considerations

- The script uses hardcoded credentials for simplicity
- In a production environment, consider using environment variables for sensitive information

## API Reference

This script implements the following EnOS API:
- [Create Product (V2.1)](https://support.enos-iot.com/docs/connection-api/en/3.0.0/oldversion/create_product.html) 