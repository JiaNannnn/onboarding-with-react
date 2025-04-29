# EnOS Batch Device Creation Tool

This script provides a utility for batch creating multiple devices in the EnOS platform using the Connection Service API v2.4 and the poseidon library for authentication.

## Features

- Create multiple devices at once under a specified product
- Automatically generate device names and descriptions
- Option to retrieve device secrets for authentication
- Save results to a JSON file for reference
- Detailed logging for troubleshooting

## Prerequisites

- Python 3.6 or higher
- The poseidon library installed (`pip install poseidon`)
- A valid EnOS account with API access
- An existing product under which to create devices

## Installation

Clone this repository and navigate to the scripts directory:

```bash
cd scripts
```

## Usage

To create devices, you need to provide the product key of an existing product:

```bash
python batch_create_devices.py --product-key YOUR_PRODUCT_KEY
```

### Command-line Arguments

- `--apigw-url`: API Gateway URL (default: https://apim-ppe1.envisioniot.com)
- `--product-key`: Product key under which to create devices (REQUIRED)
- `--device-count`: Number of devices to create (default: 5)
- `--require-secret`: Return device secrets (requires RSA key pair setup)
- `--debug`: Enable debug logging

### Examples

Create 10 devices under a specific product:
```bash
python batch_create_devices.py --product-key YOUR_PRODUCT_KEY --device-count 10
```

Create devices and retrieve their secrets:
```bash
python batch_create_devices.py --product-key YOUR_PRODUCT_KEY --require-secret
```

## API Documentation

This script implements the following EnOS API:
- [Batch Create Devices (V2.4)](https://support.enos-iot.com/docs/connection-api/en/3.0.0/V2.4/batch_create_devices.html)

## Authentication Note

If you use the `--require-secret` flag, you must have created an RSA key pair for your application in the EnOS Developer Console.

## Output

The script creates a JSON file named `batch_devices_<product_key>.json` containing the full API response, and prints a summary of the device creation results to the console. 