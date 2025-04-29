# API Client Migration Guide

This document provides a comprehensive guide for migrating from deprecated API services to the new consolidated BMSClient architecture.

## Overview

The API client layer has been refactored to consolidate duplicate implementations and improve code organization, type safety, and maintainability. The new architecture consists of:

1. A unified `APIClient` class in `/src/api/core/apiClient.ts`
2. A domain-specific `BMSClient` class in `/src/api/bmsClient.ts`
3. React hooks for simplified component integration in `/src/hooks/useBMSClient.ts`

The legacy services in `bmsService.ts` and `bmsDiscoveryService.ts` are now deprecated and will be removed in a future version.

## Benefits of Migration

Migrating to the new API client architecture provides several benefits:

- **Improved Type Safety**: Comprehensive TypeScript types for requests and responses
- **Consistent Error Handling**: Standardized error transformation and propagation
- **Better State Management**: Hooks provide loading, error, and result states
- **Reduced Duplication**: Consolidated request handling and configuration
- **Simpler API**: More intuitive API with cleaner method signatures
- **Better Testing**: Easier to mock and test API interactions

## Migration Approaches

There are two main approaches to migrating from the legacy services:

### 1. Hook-Based Approach (Recommended for Components)

For React components, we recommend using the hook-based approach:

```typescript
// Before
import { fetchPoints } from '../api/bmsService';

function MyComponent() {
  const [points, setPoints] = useState<BMSPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const loadPoints = async () => {
    setLoading(true);
    try {
      const result = await fetchPoints(assetId, deviceId, deviceAddr, apiConfig);
      setPoints(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  // ...
}

// After
import { useBMSClient } from '../hooks/useBMSClient';

function MyComponent() {
  const bmsClient = useBMSClient({ assetId });
  const { data: points, loading, error, execute: loadPoints } = bmsClient.fetchPoints(deviceId, deviceAddr);

  // Execute the API call
  useEffect(() => {
    loadPoints();
  }, [loadPoints]);

  // ...
}
```

### 2. Class-Based Approach (Recommended for Services)

For non-React services and utilities, we recommend using the class-based approach:

```typescript
// Before
import { fetchDevices, getNetworkConfig } from '../api/bmsService';

async function initializeSystem(assetId: string) {
  const networks = await getNetworkConfig(assetId);
  const devices = await fetchDevices(assetId);
  // ...
}

// After
import { createBMSClient } from '../api/bmsClient';

async function initializeSystem(assetId: string) {
  const client = createBMSClient({ assetId });
  const networks = await client.getNetworkConfig();
  const devices = await client.fetchDevices();
  // ...
}
```

## Function Mapping

The following table maps deprecated functions to their new equivalents:

| Deprecated Function | New BMSClient Method | New Hook Method |
|--------------------|---------------------|----------------|
| `bmsService.fetchPoints` | `client.fetchPoints` | `bmsClient.fetchPoints` |
| `bmsService.fetchDevices` | `client.fetchDevices` | `bmsClient.fetchDevices` |
| `bmsService.getNetworkConfig` | `client.getNetworkConfig` | `bmsClient.getNetworkConfig` |
| `bmsService.discoverDevices` | `client.discoverDevices` | `bmsClient.discoverDevices` |
| `bmsService.groupPointsWithAI` | `client.groupPointsWithAI` | `bmsClient.groupPointsWithAI` |
| `bmsService.mapPointsToEnOS` | `client.mapPointsToEnOS` | `bmsClient.mapPointsToEnOS` |
| `bmsService.saveMappingToCSV` | `client.saveMappingToCSV` | `bmsClient.saveMappingToCSV` |
| `bmsService.listSavedMappingFiles` | `client.listSavedMappingFiles` | `bmsClient.listSavedMappingFiles` |
| `bmsService.loadMappingFromCSV` | `client.loadMappingFromCSV` | `bmsClient.loadMappingFromCSV` |
| `bmsService.getFileDownloadURL` | `client.getFileDownloadURL` | `bmsClient.getFileDownloadURL` |
| `bmsService.exportMappingToEnOS` | `client.exportMappingToEnOS` | `bmsClient.exportMappingToEnOS` |
| `bmsDiscoveryService.getNetworkConfig` | `client.getNetworkConfig` | `bmsClient.getNetworkConfig` |
| `bmsDiscoveryService.discoverDevices` | `client.discoverDevices` | `bmsClient.discoverDevices` |
| `bmsDiscoveryService.checkDeviceDiscoveryStatus` | `client.checkDeviceDiscoveryStatus` | `bmsClient.checkDeviceDiscoveryStatus` |
| `bmsDiscoveryService.initiatePointsSearch` | `client.initiatePointsSearch` | `bmsClient.initiatePointsSearch` |
| `bmsDiscoveryService.checkPointsSearchStatus` | `client.checkPointsSearchStatus` | `bmsClient.checkPointsSearchStatus` |
| `bmsDiscoveryService.fetchDevicePoints` | `client.fetchDevicePoints` | `bmsClient.fetchDevicePoints` |
| `bmsDiscoveryService.checkDevicePointsStatus` | `client.checkDevicePointsStatus` | `bmsClient.checkDevicePointsStatus` |
| `bmsDiscoveryService.pollUntilComplete` | `client.pollUntilComplete` | `bmsClient.pollUntilComplete` |
| `bmsDiscoveryService.groupPoints` | `client.groupPoints` | `bmsClient.groupPoints` |
| `bmsDiscoveryService.mapPoints` | `client.mapPoints` | `bmsClient.mapPoints` |

## Detailed Migration Examples

### Example 1: Migrating a Component that Fetches Points

**Before:**
```typescript
import React, { useState, useEffect } from 'react';
import { fetchPoints } from '../api/bmsService';
import { BMSPoint } from '../types/apiTypes';

interface FetchPointsProps {
  assetId: string;
  deviceInstance: string;
  deviceAddress: string;
}

export const FetchPointsComponent: React.FC<FetchPointsProps> = ({ 
  assetId, 
  deviceInstance, 
  deviceAddress 
}) => {
  const [points, setPoints] = useState<BMSPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const loadPoints = async () => {
      setLoading(true);
      setError(null);
      try {
        const apiConfig = { apiGateway: process.env.REACT_APP_API_GATEWAY || '' };
        const result = await fetchPoints(assetId, deviceInstance, deviceAddress, apiConfig);
        setPoints(result);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      } finally {
        setLoading(false);
      }
    };

    loadPoints();
  }, [assetId, deviceInstance, deviceAddress]);

  if (loading) return <div>Loading points...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h2>Points for {deviceInstance}</h2>
      <ul>
        {points.map(point => (
          <li key={point.id}>{point.pointName}</li>
        ))}
      </ul>
    </div>
  );
};
```

**After:**
```typescript
import React from 'react';
import { useBMSClient } from '../hooks/useBMSClient';

interface FetchPointsProps {
  assetId: string;
  deviceInstance: string;
  deviceAddress: string;
}

export const FetchPointsComponent: React.FC<FetchPointsProps> = ({ 
  assetId, 
  deviceInstance, 
  deviceAddress 
}) => {
  const apiConfig = { 
    apiGateway: process.env.REACT_APP_API_GATEWAY || '',
    assetId 
  };
  
  const bmsClient = useBMSClient(apiConfig);
  const { 
    data: points, 
    loading, 
    error, 
    execute: fetchPoints 
  } = bmsClient.fetchPoints(deviceInstance, deviceAddress);

  // Execute the API call
  React.useEffect(() => {
    fetchPoints();
  }, [fetchPoints]);

  if (loading) return <div>Loading points...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h2>Points for {deviceInstance}</h2>
      <ul>
        {points?.map(point => (
          <li key={point.id}>{point.pointName}</li>
        ))}
      </ul>
    </div>
  );
};
```

### Example 2: Migrating a Service that Uses Multiple BMS Functions

**Before:**
```typescript
import { 
  getNetworkConfig, 
  discoverDevices, 
  fetchDevices 
} from '../api/bmsService';

export async function initializeAsset(assetId: string) {
  // Get network configuration
  const networks = await getNetworkConfig(assetId);
  
  // Discover devices on each network
  for (const network of networks) {
    await discoverDevices(assetId, network.name);
  }
  
  // Get all discovered devices
  const devices = await fetchDevices(assetId);
  
  return {
    networks,
    devices
  };
}
```

**After:**
```typescript
import { createBMSClient } from '../api/bmsClient';

export async function initializeAsset(assetId: string) {
  // Create a client instance
  const client = createBMSClient({ assetId });
  
  // Get network configuration
  const networks = await client.getNetworkConfig();
  
  // Discover devices on each network
  const networkNames = networks.map(network => network.name);
  await client.discoverDevices(networkNames);
  
  // Get all discovered devices
  const devices = await client.fetchDevices();
  
  return {
    networks,
    devices
  };
}
```

## Advanced Usage

### Using with TypeScript and Type Guards

The new API client architecture is designed with TypeScript in mind and provides comprehensive type definitions:

```typescript
import { createBMSClient } from '../api/bmsClient';
import { BMSPoint, ApiResponse, ApiError } from '../types/apiTypes';

async function fetchAndProcessPoints(assetId: string, deviceId: string) {
  const client = createBMSClient({ assetId });
  
  try {
    const points = await client.fetchPoints(deviceId, '192.168.1.1');
    
    // Points are properly typed as BMSPoint[]
    return points.map(point => ({
      id: point.id,
      name: point.pointName,
      type: point.pointType
    }));
  } catch (error) {
    // Proper error handling with type guards
    if (error instanceof ApiError) {
      // Handle API errors (e.g., 400, 500 responses)
      console.error(`API Error: ${error.status} - ${error.message}`);
    } else if (error instanceof Error) {
      // Handle general errors
      console.error(`General Error: ${error.message}`);
    } else {
      // Handle unknown errors
      console.error('Unknown error occurred');
    }
    return [];
  }
}
```

### Custom Configuration

The BMSClient can be configured with custom settings:

```typescript
import { createBMSClient } from '../api/bmsClient';

// Create a client with custom configuration
const client = createBMSClient({ 
  assetId: 'asset123',
  apiGateway: 'https://custom-api.example.com',
  accessKey: 'your-access-key',
  secretKey: 'your-secret-key',
  timeout: 30000, // 30 seconds
  retryAttempts: 3,
  logLevel: 'debug'
});

// Use the client with the custom configuration
const result = await client.fetchPoints('device456', '192.168.1.1');
```

### Using the Hooks with Advanced Features

The hooks provided by `useBMSClient` offer advanced features like caching, 
automatic loading state management, and error handling:

```typescript
import { useBMSClient } from '../hooks/useBMSClient';

function AdvancedComponent() {
  const bmsClient = useBMSClient({ assetId: 'asset123' });
  
  // Basic usage
  const { data: points, loading, error, execute: fetchPoints } = 
    bmsClient.fetchPoints('device456', '192.168.1.1');
  
  // With custom options
  const { data: devices, execute: fetchDevices } = 
    bmsClient.fetchDevices({
      cacheTime: 60000, // Cache for 1 minute
      staleTime: 30000, // Consider stale after 30 seconds
      retry: 3, // Retry 3 times on failure
      onSuccess: (data) => console.log('Success!', data),
      onError: (error) => console.error('Failed!', error)
    });
  
  // Manual execution
  const handleFetch = () => {
    fetchPoints();
    fetchDevices();
  };
  
  // ...
}
```

## Timeline for Deprecation

The deprecated services will be removed according to the following timeline:

1. **Phase 1 (Current)**: Add deprecation notices, migration examples, and tracking
2. **Phase 2 (Next Release)**: Implement usage tracking to monitor adoption of new architecture
3. **Phase 3 (Future Release)**: Mark functions as internal only
4. **Phase 4 (Final Release)**: Complete removal of deprecated services

We encourage all developers to migrate as soon as possible to ensure a smooth transition.

## Support and Questions

If you have any questions or need help with the migration, please contact the API Client Team or refer to the documentation in `/frontend/docs/`.