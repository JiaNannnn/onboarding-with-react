# BMS Service Layer

This directory contains the service layer for the BMS application, which mediates between the controllers (API routes) and the data access layer.

## Architecture

The service layer follows a clean architecture approach:

```
Controller (API Routes) -> Service Layer -> Data Access Layer
```

### Benefits

1. **Separation of Concerns**: Business logic is isolated from API request/response handling
2. **Improved Testability**: Services can be unit tested independently
3. **Code Reusability**: The same business logic can be used across different API endpoints
4. **Maintainability**: Changes to the data access layer don't affect the API controllers

## Services

### BMSService

The `BMSService` class in `bms_service.py` provides methods for interacting with the EnOS API for BMS operations:

- `get_network_config`: Retrieves network configuration options
- `discover_devices`: Searches for devices on specified networks
- `get_device_discovery_status`: Checks the status of a device discovery task
- `get_device_points`: Fetches points for a specific device
- `get_device_points_status`: Checks the status of a device points task
- `search_points`: Searches for points across multiple devices

## Usage

Import the service singleton in your controller:

```python
from app.services.bms_service import bms_service

# Use the service in your controller
result = bms_service.get_network_config(
    api_url=api_url,
    access_key=access_key,
    secret_key=secret_key,
    org_id=org_id,
    asset_id=asset_id
)
```

## Error Handling

The service layer provides consistent error handling and returns standardized response formats:

```python
{
    "status": "success|error",
    "message": "Optional message",
    # Additional data depending on the operation
}
```

## Testing

Services can be mocked for controller tests or tested independently with unit tests.

## Future Considerations

1. Add dependency injection for better testability
2. Implement caching at the service layer
3. Add more comprehensive logging and monitoring
4. Create domain-specific exception classes 