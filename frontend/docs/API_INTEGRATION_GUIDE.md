# Frontend API Integration Guide

## Overview

This document provides detailed guidance on how to integrate the backend BMS API into the frontend application, including example code for implementing various features using the `BMSClient` class and React hooks.

## Table of Contents

- [Configuration](#configuration)
- [Basic Usage](#basic-usage)
- [Error Handling](#error-handling)
- [Endpoint Details](#endpoint-details)
  - [Point Grouping](#point-grouping)
  - [Point Mapping](#point-mapping)
  - [Device Discovery](#device-discovery)
  - [Point Search](#point-search)
- [Advanced Features](#advanced-features)
  - [Retry Mechanism](#retry-mechanism)
  - [Local Fallback](#local-fallback)
  - [Caching Mechanism](#caching-mechanism)

## Configuration

Frontend applications can integrate the BMS API in two ways:

1. **Class Instance Method**: Directly create a `BMSClient` instance
2. **Hook Method**: Use the `useBMSClient` React hook

### Class Instance Configuration

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

### Hook Configuration

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

## Basic Usage

### Test Connection

```typescript
// Test connection to backend
try {
  const response = await bmsClient.pingBackend();
  console.log('Backend connection normal:', response.status);
} catch (error) {
  console.error('Backend connection failed:', error);
}
```

### Get Network Configuration

```typescript
// Get network configuration
try {
  const networks = await bmsClient.getNetworkConfig();
  console.log('Available networks:', networks);
} catch (error) {
  console.error('Failed to get network configuration:', error);
}
```

## Error Handling

`BMSClient` provides a consistent error handling mechanism:

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

## Endpoint Details

### Point Grouping

Use AI technology to semantically group BMS points.

#### Class Instance Method

```typescript
import { BMSPoint } from '../types/apiTypes';

// Prepare points to group
const points: BMSPoint[] = [
  { id: '1', pointName: 'AHU1_SAT', pointType: 'Temperature' },
  { id: '2', pointName: 'AHU1_RAT', pointType: 'Temperature' },
  { id: '3', pointName: 'FCU1_SAT', pointType: 'Temperature' }
];

// Call AI grouping function
try {
  const result = await bmsClient.groupPointsWithAI(points);
  
  if (result.success) {
    console.log('Grouping result:', result.grouped_points);
    console.log('Statistics:', result.stats);
  } else {
    console.error('Grouping failed:', result.error);
  }
} catch (error) {
  console.error('Error occurred during grouping:', error);
}
```

#### Hook Method

```typescript
import { useBMSClient } from '../hooks/useBMSClient';
import { useEffect, useState } from 'react';
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

### Point Mapping

Map BMS points to EnOS model paths.

#### Class Instance Method

```typescript
import { BMSPoint, MappingConfig } from '../types/apiTypes';

// Prepare points to map
const points: BMSPoint[] = [
  { id: '1', pointName: 'AHU1_SAT', pointType: 'Temperature' },
  { id: '2', pointName: 'FCU1_SpeedFan', pointType: 'Speed' }
];

// Configure mapping options
const mappingConfig: MappingConfig = {
  targetSchema: 'default',
  matchingStrategy: 'ai',
  confidence: 0.7
};

// Call mapping function
try {
  const result = await bmsClient.mapPointsToEnOS(points, mappingConfig);
  
  if (result.success) {
    console.log('Mapping result:', result.mappings);
    console.log('Statistics:', result.stats);
  } else {
    console.error('Mapping failed:', result.error);
  }
} catch (error) {
  console.error('Error occurred during mapping:', error);
}
```

#### Hook Method

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

### Device Discovery

Initiate device discovery on networks to find available BMS devices.

#### Class Instance Method

```typescript
import { NetworkConfig } from '../types/apiTypes';

// Configure discovery settings
const networkConfig: NetworkConfig = {
  apiGateway: 'http://gateway.example.com',
  accessKey: 'your-access-key',
  secretKey: 'your-secret-key',
  orgId: 'your-org-id',
  assetId: 'your-asset-id',
  protocol: 'bacnet'  // Optional - specific protocol
};

// Start device discovery
try {
  const result = await bmsClient.discoverDevices(networkConfig);
  
  if (result.success) {
    console.log('Discovery started, task ID:', result.taskId);
    
    // Check status periodically
    const statusCheckInterval = setInterval(async () => {
      const status = await bmsClient.getDiscoveryStatus(result.taskId);
      console.log('Discovery status:', status.state);
      
      if (status.state === 'COMPLETED' || status.state === 'FAILED') {
        clearInterval(statusCheckInterval);
        
        if (status.state === 'COMPLETED') {
          console.log('Discovered devices:', status.devices);
        } else {
          console.error('Discovery failed:', status.error);
        }
      }
    }, 5000);
  } else {
    console.error('Failed to start discovery:', result.error);
  }
} catch (error) {
  console.error('Error initiating discovery:', error);
}
```

#### Hook Method

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

### Point Search

Search for points on discovered devices.

#### Class Instance Method

```typescript
import { SearchConfig } from '../types/apiTypes';

// Configure point search settings
const searchConfig: SearchConfig = {
  deviceIds: ['device-1', 'device-2'],  // IDs of devices to search
  pointTypes: ['Temperature', 'Pressure'],  // Optional - filter by point types
  maxResults: 1000,  // Optional - limit results
  timeout: 120  // Optional - timeout in seconds
};

// Start point search
try {
  const result = await bmsClient.searchPoints(searchConfig);
  
  if (result.success) {
    console.log('Search started, task ID:', result.taskId);
    
    // Check status periodically
    const statusCheckInterval = setInterval(async () => {
      const status = await bmsClient.getSearchStatus(result.taskId);
      console.log('Search status:', status.state);
      
      if (status.state === 'COMPLETED' || status.state === 'FAILED') {
        clearInterval(statusCheckInterval);
        
        if (status.state === 'COMPLETED') {
          console.log('Found points:', status.points);
          console.log('Total points found:', status.points.length);
        } else {
          console.error('Search failed:', status.error);
        }
      }
    }, 5000);
  } else {
    console.error('Failed to start search:', result.error);
  }
} catch (error) {
  console.error('Error initiating search:', error);
}
```

#### Hook Method

```typescript
import { useBMSClient } from '../hooks/useBMSClient';
import { useState, useEffect } from 'react';
import { SearchConfig, SearchStatus, BMSPoint } from '../types/apiTypes';

function PointSearch({ selectedDevices }) {
  const bmsClient = useBMSClient();
  const [isSearching, setIsSearching] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState<SearchStatus | null>(null);
  const [points, setPoints] = useState<BMSPoint[]>([]);
  const [error, setError] = useState(null);
  
  // Function to initiate search
  const startSearch = async () => {
    if (!selectedDevices.length) {
      setError('Please select at least one device');
      return;
    }
    
    setIsSearching(true);
    setError(null);
    
    const searchConfig: SearchConfig = {
      deviceIds: selectedDevices.map(device => device.id),
      pointTypes: ['Temperature', 'Pressure', 'Speed', 'Status']
    };
    
    try {
      const result = await bmsClient.searchPoints(searchConfig);
      
      if (result.success) {
        setTaskId(result.taskId);
      } else {
        setError(result.error);
        setIsSearching(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start search');
      setIsSearching(false);
    }
  };
  
  // Effect to poll status when taskId is available
  useEffect(() => {
    if (!taskId) return;
    
    const statusCheckInterval = setInterval(async () => {
      try {
        const status = await bmsClient.getSearchStatus(taskId);
        setStatus(status);
        
        if (status.state === 'COMPLETED') {
          setPoints(status.points || []);
          setIsSearching(false);
          clearInterval(statusCheckInterval);
        } else if (status.state === 'FAILED') {
          setError(status.error || 'Search failed');
          setIsSearching(false);
          clearInterval(statusCheckInterval);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to check status');
        setIsSearching(false);
        clearInterval(statusCheckInterval);
      }
    }, 3000);
    
    return () => clearInterval(statusCheckInterval);
  }, [taskId, bmsClient]);
  
  return (
    <div>
      <h2>Point Search</h2>
      
      <div className="search-controls">
        <button 
          onClick={startSearch}
          disabled={isSearching || !selectedDevices.length}
        >
          {isSearching ? 'Searching...' : 'Search Points'}
        </button>
        
        {status && status.state && (
          <div className="status">
            Status: {status.state}
            {status.progress && ` (${status.progress}%)`}
          </div>
        )}
        
        {error && <div className="error">{error}</div>}
      </div>
      
      {points.length > 0 && (
        <div className="found-points">
          <h3>Found Points ({points.length})</h3>
          <table className="points-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Device</th>
                <th>Unit</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {points.map(point => (
                <tr key={point.id}>
                  <td>{point.pointName}</td>
                  <td>{point.pointType}</td>
                  <td>{point.deviceName}</td>
                  <td>{point.unit || 'N/A'}</td>
                  <td>{point.description || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
```

## Advanced Features

### Retry Mechanism

`BMSClient` has a built-in retry mechanism, especially in the `mapPointsToEnOS` method:

```typescript
// Retry mechanism configuration
const maxRetries = 2;
let currentTry = 0;

while (currentTry <= maxRetries) {
  try {
    // API call
    // ...
  } catch (error) {
    // Handle error and decide whether to retry
    if (currentTry < maxRetries) {
      currentTry++;
      // Increase interval time
      await new Promise(resolve => setTimeout(resolve, 1000 * currentTry));
      continue;
    }
    // Maximum retry count reached, return failure result
  }
}
```

### Local Fallback

When all retries fail, `mapPointsToEnOS` will use local mapping logic as a backup:

```typescript
// When all remote mapping attempts fail, use local mapping as fallback
console.warn('All remote mapping attempts failed, using local mapping as fallback');

// Use simple local mapping logic
const localMappings = points.map(point => {
  // Rule-based mapping based on point name
  // ...
});

return {
  success: true,
  error: 'Using local mapping as fallback',
  mappings: localMappings,
  stats: {
    total: points.length,
    mapped: localMappings.length,
    errors: 0
  }
};
```

### Caching Mechanism

Some implementations may also include caching mechanisms to reduce duplicate requests:

```typescript
// Example: A simple in-memory cache implementation
const cache = new Map();

function createCacheKey(points) {
  // Generate cache key
  return JSON.stringify(points.map(p => p.pointName).sort());
}

async function getWithCache(points, mappingFn) {
  const cacheKey = createCacheKey(points);
  
  // Check cache
  if (cache.has(cacheKey)) {
    console.log('Using cached mapping results');
    return cache.get(cacheKey);
  }
  
  // Execute actual mapping
  const result = await mappingFn(points);
  
  // Cache result
  if (result.success) {
    cache.set(cacheKey, result);
  }
  
  return result;
}

// Use mapping with cache
const result = await getWithCache(points, (pts) => bmsClient.mapPointsToEnOS(pts));
```

## Summary

This guide provides detailed instructions on how to integrate and use the BMS API, especially the point mapping functionality. By using the `BMSClient` class or `useBMSClient` hook, developers can easily implement complex BMS features in their frontend applications.

Key features include:
- AI point grouping
- Point mapping to EnOS models
- Device discovery and point search
- Built-in error handling and retry mechanisms
- Local fallback functionality, ensuring basic functionality even when backend services are unavailable 