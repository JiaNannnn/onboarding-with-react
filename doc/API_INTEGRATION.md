# BMS API Integration Guide

## Overview

This guide provides comprehensive documentation on how to integrate with the Building Management System (BMS) API. It covers both frontend and backend aspects of the integration, with detailed code examples and best practices.

## Architecture

The BMS API follows a client-server architecture:

- **Backend**: Python-based REST API server that handles device discovery, point management, grouping and mapping operations.
- **Frontend**: React-based client application that interacts with the backend through a structured API client.

Communication between frontend and backend is handled via HTTP/HTTPS using JSON for data exchange.

## Backend API Reference

### Base URL

```
http://localhost:5000
```

### Endpoints

#### Health Check

```
GET /api/ping
```

Response:
```json
{
  "status": "ok",
  "message": "Server is running"
}
```

#### Point Management

##### AI Point Grouping

```
POST /api/points/ai-grouping
```

Request body:
```json
{
  "points": [
    {
      "id": "1",
      "pointName": "AHU1_SAT",
      "pointType": "Temperature"
    },
    {
      "id": "2",
      "pointName": "AHU1_RAT",
      "pointType": "Temperature"
    }
  ]
}
```

Response:
```json
{
  "success": true,
  "grouped_points": {
    "AHU": {
      "AHU1": ["AHU1_SAT", "AHU1_RAT"]
    }
  },
  "stats": {
    "total": 2,
    "grouped": 2,
    "errors": 0
  }
}
```

##### Map Points to EnOS

```
POST /api/bms/map-points
```

Request body:
```json
{
  "points": [
    {
      "id": "1",
      "pointName": "AHU1_SAT",
      "pointType": "Temperature"
    }
  ],
  "matchingStrategy": "ai",
  "confidence": 0.7
}
```

Response:
```json
{
  "success": true,
  "mappings": [
    {
      "pointId": "1",
      "pointName": "AHU1_SAT",
      "pointType": "Temperature",
      "enosPath": "AirHandlingUnit.Supply.Temperature",
      "confidence": 0.85,
      "status": "mapped"
    }
  ],
  "stats": {
    "total": 1,
    "mapped": 1,
    "errors": 0
  }
}
```

#### Device Discovery

##### Get Networks

```
POST /api/networks
```

Request body:
```json
{
  "apiGateway": "http://gateway.example.com",
  "accessKey": "your-access-key",
  "secretKey": "your-secret-key",
  "orgId": "your-org-id",
  "assetId": "your-asset-id"
}
```

Response:
```json
{
  "success": true,
  "networks": [
    {
      "id": "network-1",
      "name": "Building A - BACnet",
      "protocol": "bacnet",
      "address": "192.168.1.0/24"
    },
    {
      "id": "network-2",
      "name": "Building B - Modbus",
      "protocol": "modbus",
      "address": "192.168.2.0/24"
    }
  ]
}
```

##### Discover Devices

```
POST /api/devices/discover
```

Request body:
```json
{
  "apiGateway": "http://gateway.example.com",
  "accessKey": "your-access-key",
  "secretKey": "your-secret-key",
  "orgId": "your-org-id",
  "assetId": "your-asset-id",
  "protocol": "bacnet"
}
```

Response:
```json
{
  "success": true,
  "taskId": "task-12345"
}
```

##### Get Discovery Status

```
GET /api/devices/discover/{task_id}
```

Response:
```json
{
  "state": "COMPLETED",
  "progress": 100,
  "devices": [
    {
      "id": "device-1",
      "name": "AHU-1",
      "ip": "192.168.1.100",
      "protocol": "bacnet",
      "model": "BACnet Controller"
    }
  ]
}
```

#### Point Search

##### Search Points

```
POST /api/points/search
```

Request body:
```json
{
  "deviceIds": ["device-1", "device-2"],
  "pointTypes": ["Temperature", "Pressure"],
  "maxResults": 1000
}
```

Response:
```json
{
  "success": true,
  "taskId": "task-67890"
}
```

##### Get Search Status

```
GET /api/tasks/{task_id}
```

Response:
```json
{
  "state": "COMPLETED",
  "progress": 100,
  "points": [
    {
      "id": "point-1",
      "pointName": "AHU1_SAT",
      "pointType": "Temperature",
      "deviceId": "device-1",
      "deviceName": "AHU-1",
      "unit": "°C",
      "description": "Supply Air Temperature"
    }
  ]
}
```

### Error Handling

All API endpoints follow a consistent error format:

```json
{
  "success": false,
  "error": "Error message explaining what went wrong",
  "code": "ERROR_CODE"
}
```

Common error codes:
- `INVALID_REQUEST`: Request format or parameters are invalid
- `NETWORK_ERROR`: Network connectivity issues
- `AUTHENTICATION_ERROR`: Authentication failed
- `PERMISSION_DENIED`: Insufficient permissions
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `SERVER_ERROR`: Internal server error
- `TIMEOUT`: Operation timed out

### CORS Support

All API endpoints support Cross-Origin Resource Sharing (CORS) with the following headers:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 3600
```

### Backend Implementation Examples

#### Python Example - Creating a Point Mapping Endpoint

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
from app.bms.mapping import bms_map_points

app = Flask(__name__)
CORS(app)

@app.route('/api/bms/map-points', methods=['POST'])
def map_points():
    try:
        request_data = request.get_json()
        
        if not request_data or 'points' not in request_data:
            return jsonify({
                'success': False,
                'error': 'Invalid request: points array is required',
                'code': 'INVALID_REQUEST'
            }), 400
        
        points = request_data.get('points', [])
        matching_strategy = request_data.get('matchingStrategy', 'ai')
        confidence = request_data.get('confidence', 0.7)
        
        result = bms_map_points(points, matching_strategy, confidence)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error mapping points: {str(e)}',
            'code': 'SERVER_ERROR'
        }), 500
```

## Frontend Integration

### Installing Dependencies

```bash
npm install axios react-query
# or
yarn add axios react-query
```

### Configuration

Frontend applications can integrate the BMS API in two ways:

1. **Class Instance Method**: Directly create a `BMSClient` instance
2. **Hook Method**: Use the `useBMSClient` React hook

#### Class Instance Configuration

```typescript
import { createBMSClient } from '../api/bmsClient';

// Create BMS client instance
const bmsClient = createBMSClient({
  apiGateway: 'http://localhost:5000', // Backend API address
  accessKey: 'your-access-key',        // Optional access key
  secretKey: 'your-secret-key',        // Optional secret key
  orgId: 'your-org-id',                // Optional organization ID
  assetId: 'your-asset-id'             // Optional asset ID
});
```

#### Hook Configuration

```typescript
import { useBMSClient } from '../hooks/useBMSClient';

function MyComponent() {
  // Create BMS client hook
  const bmsClient = useBMSClient({
    apiGateway: 'http://localhost:5000',
    accessKey: 'your-access-key',
    secretKey: 'your-secret-key',
    orgId: 'your-org-id',
    assetId: 'your-asset-id'
  });
  
  // Now you can use bmsClient methods
  // ...
}
```

### Basic Usage

#### Test Connection

```typescript
// Test connection to backend
try {
  const response = await bmsClient.pingBackend();
  console.log('Backend connection normal:', response.status);
} catch (error) {
  console.error('Backend connection failed:', error);
}
```

#### Error Handling Pattern

```typescript
try {
  const result = await bmsClient.mapPointsToEnOS(points);
  if (result.success) {
    // Handle successful result
    console.log(`Successfully mapped ${result.mappings?.length} points`);
  } else {
    // Handle API-returned errors
    console.error('Mapping failed:', result.error);
  }
} catch (error) {
  // Handle network or other uncaught errors
  console.error('Exception occurred:', error);
}
```

### Feature Examples

#### Point Grouping

```typescript
import { useBMSClient } from '../hooks/useBMSClient';
import { useState } from 'react';
import { BMSPoint } from '../types/apiTypes';

function PointGrouping({ points }) {
  const bmsClient = useBMSClient();
  const [groupedPoints, setGroupedPoints] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const handleGroupPoints = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await bmsClient.groupPointsWithAI(points);
      
      if (result.success) {
        setGroupedPoints(result.grouped_points);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message || 'Grouping failed');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <button 
        onClick={handleGroupPoints}
        disabled={loading || !points.length}
      >
        {loading ? 'Grouping...' : 'AI Grouping'}
      </button>
      
      {error && <div className="error">{error}</div>}
      
      {groupedPoints && (
        <div className="grouped-points">
          {/* Display grouping results */}
        </div>
      )}
    </div>
  );
}
```

#### Point Mapping

```typescript
import { useBMSClient } from '../hooks/useBMSClient';
import { useState } from 'react';
import { BMSPoint, MappingConfig } from '../types/apiTypes';

function PointMapping({ points }) {
  const bmsClient = useBMSClient();
  const [mappedPoints, setMappedPoints] = useState([]);
  const [isMapping, setIsMapping] = useState(false);
  const [error, setError] = useState(null);
  
  const handleMapPoints = async () => {
    setIsMapping(true);
    setError(null);
    
    const mappingConfig: MappingConfig = {
      matchingStrategy: 'ai',
      confidence: 0.7
    };
    
    try {
      const response = await bmsClient.mapPointsToEnOS(points, mappingConfig);
      
      if (response.success && response.mappings) {
        setMappedPoints(response.mappings);
      } else {
        throw new Error(response.error || 'Mapping failed');
      }
    } catch (err) {
      console.error('Mapping error:', err);
      setError(err instanceof Error ? err.message : 'Mapping failed');
    } finally {
      setIsMapping(false);
    }
  };
  
  return (
    <div>
      <button 
        onClick={handleMapPoints}
        disabled={isMapping || !points.length}
      >
        {isMapping ? 'Mapping...' : 'Map to EnOS'}
      </button>
      
      {error && <div className="error">{error}</div>}
      
      {mappedPoints.length > 0 && (
        <table className="mapping-table">
          <thead>
            <tr>
              <th>Point Name</th>
              <th>EnOS Path</th>
              <th>Confidence</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {mappedPoints.map(point => (
              <tr key={point.pointId}>
                <td>{point.pointName}</td>
                <td>{point.enosPath}</td>
                <td>{point.confidence}</td>
                <td>{point.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
```

#### Device Discovery

```typescript
import { useBMSClient } from '../hooks/useBMSClient';
import { useState, useEffect } from 'react';
import { NetworkConfig, DiscoveryStatus } from '../types/apiTypes';

function DeviceDiscovery() {
  const bmsClient = useBMSClient();
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState<DiscoveryStatus | null>(null);
  const [devices, setDevices] = useState([]);
  const [error, setError] = useState(null);
  
  // Function to initiate discovery
  const startDiscovery = async () => {
    setIsDiscovering(true);
    setError(null);
    
    const networkConfig: NetworkConfig = {
      apiGateway: 'http://gateway.example.com',
      accessKey: 'your-access-key',
      secretKey: 'your-secret-key',
      orgId: 'your-org-id',
      assetId: 'your-asset-id'
    };
    
    try {
      const result = await bmsClient.discoverDevices(networkConfig);
      
      if (result.success) {
        setTaskId(result.taskId);
      } else {
        setError(result.error);
        setIsDiscovering(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start discovery');
      setIsDiscovering(false);
    }
  };
  
  // Effect to poll status when taskId is available
  useEffect(() => {
    if (!taskId) return;
    
    const statusCheckInterval = setInterval(async () => {
      try {
        const status = await bmsClient.getDiscoveryStatus(taskId);
        setStatus(status);
        
        if (status.state === 'COMPLETED') {
          setDevices(status.devices || []);
          setIsDiscovering(false);
          clearInterval(statusCheckInterval);
        } else if (status.state === 'FAILED') {
          setError(status.error || 'Discovery failed');
          setIsDiscovering(false);
          clearInterval(statusCheckInterval);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to check status');
        setIsDiscovering(false);
        clearInterval(statusCheckInterval);
      }
    }, 5000);
    
    return () => clearInterval(statusCheckInterval);
  }, [taskId, bmsClient]);
  
  return (
    <div>
      <h2>Device Discovery</h2>
      
      <button 
        onClick={startDiscovery}
        disabled={isDiscovering}
      >
        {isDiscovering ? 'Discovering...' : 'Start Discovery'}
      </button>
      
      {status && status.state && (
        <div className="status">
          Status: {status.state}
          {status.progress && ` (${status.progress}%)`}
        </div>
      )}
      
      {error && <div className="error">{error}</div>}
      
      {devices.length > 0 && (
        <div className="discovered-devices">
          <h3>Discovered Devices ({devices.length})</h3>
          <ul>
            {devices.map((device, index) => (
              <li key={index}>
                <strong>{device.name || 'Unnamed Device'}</strong>
                <div>IP: {device.ip}</div>
                <div>Protocol: {device.protocol}</div>
                <div>Model: {device.model}</div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

## Advanced Features

### Retry Mechanism

The BMS client includes a built-in retry mechanism:

```typescript
// Retry mechanism configuration
const maxRetries = 2;
let currentTry = 0;

while (currentTry <= maxRetries) {
  try {
    // API call
    // ...
    break; // Exit loop on success
  } catch (error) {
    // Handle error and decide whether to retry
    if (currentTry < maxRetries) {
      currentTry++;
      // Increase interval time
      await new Promise(resolve => setTimeout(resolve, 1000 * currentTry));
      continue;
    }
    // Maximum retry count reached, throw or handle failure
    throw error;
  }
}
```

### Local Fallback

For point mapping operations, a local fallback mechanism ensures basic functionality:

```typescript
// When all remote mapping attempts fail, use local mapping as fallback
console.warn('All remote mapping attempts failed, using local mapping as fallback');

// Use simple local mapping logic
const localMappings = points.map(point => {
  const pointName = point.pointName.toLowerCase();
  let enosPath = null;
  let confidence = 0.6;
  
  // Simple rule-based mapping
  if (pointName.includes('sat') || pointName.includes('supply') && pointName.includes('temp')) {
    enosPath = 'AirHandlingUnit.Supply.Temperature';
    confidence = 0.8;
  } else if (pointName.includes('rat') || pointName.includes('return') && pointName.includes('temp')) {
    enosPath = 'AirHandlingUnit.Return.Temperature';
    confidence = 0.8;
  } else if (pointName.includes('fan') && pointName.includes('speed')) {
    enosPath = 'AirHandlingUnit.Fan.Speed';
    confidence = 0.75;
  }
  
  return {
    pointId: point.id,
    pointName: point.pointName,
    pointType: point.pointType,
    enosPath: enosPath,
    confidence: confidence,
    status: enosPath ? 'mapped' : 'unmapped',
    deviceType: pointName.includes('ahu') ? 'AirHandlingUnit' : 
                pointName.includes('fcu') ? 'FanCoilUnit' : 'Unknown'
  };
});

return {
  success: true,
  error: 'Using local mapping as fallback',
  mappings: localMappings,
  stats: {
    total: points.length,
    mapped: localMappings.filter(m => m.status === 'mapped').length,
    errors: 0
  }
};
```

## Best Practices

1. **Error Handling**: Always implement proper error handling for API calls.
2. **API Versioning**: Include version information in API routes for compatibility.
3. **Type Safety**: Use TypeScript types and interfaces for API requests and responses.
4. **Authentication**: Include authentication information in all API requests.
5. **Logging**: Implement logging for debugging purposes.
6. **Timeouts**: Set appropriate timeouts for API calls, especially for long-running operations.
7. **Rate Limiting**: Respect API rate limits, especially for resource-intensive operations.
8. **Data Validation**: Validate input data before sending requests.
9. **Feature Degradation**: Implement graceful degradation when advanced features are unavailable.
10. **Caching**: Use caching strategies to reduce API calls for frequently accessed data.

## Troubleshooting

### Common Issues

1. **Connection Refused**: Check if the backend server is running and accessible.
2. **CORS Errors**: Ensure CORS is properly configured on the backend.
3. **Authentication Failures**: Verify API keys and credentials.
4. **Timeout Errors**: Consider increasing timeout settings for long operations.
5. **Data Format Errors**: Verify request and response formats match API expectations.

### Debugging Tools

1. **Browser Developer Tools**: Use the Network tab to inspect API requests and responses.
2. **API Testing Tools**: Use tools like Postman or Insomnia to test API endpoints.
3. **Logging**: Enable verbose logging on both frontend and backend.
4. **Error Monitoring**: Use error monitoring tools to track and analyze errors.

## Conclusion

This API integration guide provides comprehensive details for working with the BMS API. By following these guidelines and best practices, developers can efficiently integrate BMS functionality into their applications. 