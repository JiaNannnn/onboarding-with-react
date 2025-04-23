# EnOS Platform Utility Scripts

This directory contains utility scripts for interacting with the EnOS platform.

## Prerequisites

- Python 3.6 or higher
- Required Python packages (install using `pip install -r requirements.txt`)

## Installation

1. Clone this repository
2. Navigate to the `scripts` directory
3. Install dependencies:

```
pip install -r requirements.txt
```

## Available Scripts

### 1. create_product_device.py

Creates a product and associated device on the EnOS platform.

#### Usage

```
python create_product_device.py --apigw-url <API_GATEWAY_URL> --org-id <ORG_ID> --ak <ACCESS_KEY> --sk <SECRET_KEY> [OPTIONS]
```

#### Options

- `--apigw-url`: EnOS API Gateway URL (e.g., https://apim-gateway.eniot.io)
- `--org-id`: Organization ID
- `--ak`: Access Key
- `--sk`: Secret Key
- Additional options specific to product/device creation

### 2. batch_device_creator.py

Creates multiple devices in batch for an existing product on the EnOS platform.

#### Usage

```
python batch_device_creator.py --apigw-url <API_GATEWAY_URL> --org-id <ORG_ID> --ak <ACCESS_KEY> --sk <SECRET_KEY> --product-key <PRODUCT_KEY> [OPTIONS]
```

#### Options

- `--apigw-url`: EnOS API Gateway URL (e.g., https://apim-gateway.eniot.io)
- `--org-id`: Organization ID
- `--ak`: Access Key
- `--sk`: Secret Key
- `--product-key`: Product Key for device creation
- `--device-count`: Number of devices to create (default: 10)
- `--name-prefix`: Prefix for device names (default: "Device")
- `--model-id`: Model ID (optional)
- `--timezone`: Timezone for devices (default: +08:00)
- `--require-secret`: Require device secret (flag, default: False)
- `--debug`: Enable debug logging (flag)
- `--output-file`: Custom output file path (default: batch_devices_<product_key>.json)

#### Example

```
python batch_device_creator.py --apigw-url https://apim-gateway.eniot.io --org-id your_org_id --ak your_access_key --sk your_secret_key --product-key your_product_key --device-count 50 --name-prefix HVAC --require-secret
```

This will create 50 devices with names starting with "HVAC" for the specified product, and include device secrets in the output file.

## Environment Variables

Instead of providing sensitive information via command-line arguments, you can set the following environment variables in a `.env` file:

```
ENOS_APIGW_URL=https://apim-gateway.eniot.io
ENOS_ORG_ID=your_org_id
ENOS_AK=your_access_key
ENOS_SK=your_secret_key
```

## Error Handling

All scripts include comprehensive error handling and logging. For debugging, use the `--debug` flag to enable detailed logging.

## Output Files

Scripts that create resources on the EnOS platform will typically save the results to JSON files, which include details about the created resources, such as device keys, secrets, and other relevant information. 