/**
 * @deprecated IMPORTANT: This entire file is deprecated and will be removed in a future version.
 * Use the BMSClient class and useBMSClient hook instead.
 * 
 * Migration Guide:
 * - For components: import { useBMSClient } from '../hooks/useBMSClient'
 * - For services: import { BMSClient, createBMSClient } from './bmsClient'
 * 
 * Migration examples:
 * ```
 * // Before
 * import { BMSDiscoveryService } from './bmsDiscoveryService';
 * 
 * const discoveryService = new BMSDiscoveryService(config);
 * const networks = await discoveryService.getNetworkConfig();
 * const devices = await discoveryService.discoverDevices(networks);
 * 
 * // After - with hook
 * import { useBMSClient } from '../hooks/useBMSClient';
 * 
 * const bmsClient = useBMSClient(config);
 * const networks = await bmsClient.getNetworkConfig();
 * const devices = await bmsClient.discoverDevices(networks);
 * 
 * // After - with class
 * import { createBMSClient } from './bmsClient';
 * 
 * const client = createBMSClient(config);
 * const networks = await client.getNetworkConfig();
 * const devices = await client.discoverDevices(networks);
 * ```
 * 
 * Legacy BMS Discovery Service - DEPRECATED
 * This service is being phased out in favor of the consolidated BMSClient.
 * Use with caution as it will be removed in a future version.
 */

// These imports are intentionally commented out as they're not currently used
// but may be needed in future implementation
// import { request } from './apiClient';
// import { HttpMethod } from '../types/apiTypes';
import { APIConfig as BaseAPIConfig } from './bmsService';
// import axios, { AxiosInstance } from 'axios';
import { 
  BMSClient, 
  createBMSClient, 
  NetworkInterface as BMSNetworkInterface,
  DeviceDiscoveryResponse,
  DeviceDiscoveryStatusResponse,
  PointsSearchResponse,
  DevicePointsResponse,
  PointsSearchStatusResponse,
  DevicePointsStatusResponse,
  GroupPointsResponse,
  PointMapping,
  MapPointsResponse
} from './bmsClient';
import { logger } from '../utils/logger';

// Re-export NetworkInterface for backward compatibility
export type NetworkInterface = BMSNetworkInterface;

// These constants are commented out as they're not currently used
// but may be needed in future implementations
// Define the base URL for all BMS API requests
// const BMS_API_BASE_URL = 'http://localhost:5000';
// Define the versioned API base path
// const API_V1_PATH = '/api/v1';

// Extend the base APIConfig
export interface APIConfig extends BaseAPIConfig {
  // No additional fields needed
}

// Create a shared client instance for all legacy methods
let sharedBmsClient: BMSClient | null = null;

/**
 * Track usage of deprecated service methods to help plan for removal
 * @private Internal tracking function
 */
function trackDeprecatedUsage(methodName: string, details?: Record<string, unknown>): void {
  // Log the usage with appropriate metadata
  logger.warn(`DEPRECATED_USAGE: ${methodName}`, { 
    service: 'bmsDiscoveryService',
    className: 'BMSDiscoveryService',
    methodName,
    timestamp: new Date().toISOString(),
    ...details
  });
  
  // If available in the environment, send telemetry data
  // This could be expanded to use an analytics service
  if (process.env.REACT_APP_TRACK_DEPRECATIONS === 'true' && 
      typeof window !== 'undefined' && 
      window.performance && 
      window.performance.mark) {
    window.performance.mark(`deprecated_discovery_${methodName}`);
  }
}

/**
 * Get or create a shared BMS client instance
 * @deprecated Not currently used but kept for potential future use
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function _getSharedClient(config: APIConfig): BMSClient {
  if (!sharedBmsClient) {
    sharedBmsClient = createBMSClient(config);
  } else {
    // Update the config if needed
    sharedBmsClient.updateConfig(config);
  }
  return sharedBmsClient;
}

/**
 * @deprecated Use BMSClient instead
 * Migration example:
 * ```
 * // Before
 * import { BMSDiscoveryService } from './bmsDiscoveryService';
 * const service = new BMSDiscoveryService(config);
 * 
 * // After - with hook
 * import { useBMSClient } from '../hooks/useBMSClient';
 * const bmsClient = useBMSClient(config);
 * 
 * // After - with class
 * import { createBMSClient } from './bmsClient';
 * const client = createBMSClient(config);
 * ```
 */
export class BMSDiscoveryService {
  private config: APIConfig;
  private bmsClient: BMSClient;
  
  constructor(config: APIConfig) {
    console.warn('DEPRECATED: BMSDiscoveryService is deprecated. Use BMSClient instead.');
    trackDeprecatedUsage('constructor', { assetId: config.assetId });
    
    this.config = config;
    this.bmsClient = createBMSClient(config);
  }

  /**
   * Test backend connectivity
   */
  async pingBackend(): Promise<{ status: string }> {
    console.warn('DEPRECATED: Use BMSClient.pingBackend instead');
    trackDeprecatedUsage('pingBackend');
    return this.bmsClient.pingBackend();
  }

  /**
   * Step 1: Get Network Configuration
   */
  async getNetworkConfig(): Promise<NetworkInterface[]> {
    console.warn('DEPRECATED: Use BMSClient.getNetworkConfig instead');
    trackDeprecatedUsage('getNetworkConfig', { assetId: this.config.assetId });
    return this.bmsClient.getNetworkConfig();
  }

  /**
   * Step 2: Discover Devices
   */
  async discoverDevices(networks: string[], protocol: string = 'bacnet'): Promise<DeviceDiscoveryResponse> {
    console.warn('DEPRECATED: Use BMSClient.discoverDevices instead');
    trackDeprecatedUsage('discoverDevices', { 
      networks, 
      protocol, 
      assetId: this.config.assetId 
    });
    return this.bmsClient.discoverDevices(networks, protocol);
  }

  /**
   * Step 3: Check Device Discovery Status
   */
  async checkDeviceDiscoveryStatus(taskId: string): Promise<DeviceDiscoveryStatusResponse> {
    console.warn('DEPRECATED: Use BMSClient.checkDeviceDiscoveryStatus instead');
    trackDeprecatedUsage('checkDeviceDiscoveryStatus', { taskId });
    return this.bmsClient.checkDeviceDiscoveryStatus(taskId);
  }

  /**
   * Step 4: Initiate Points Search
   */
  async initiatePointsSearch(deviceInstances: number[], protocol: string = 'bacnet'): Promise<PointsSearchResponse> {
    console.warn('DEPRECATED: Use BMSClient.initiatePointsSearch instead');
    trackDeprecatedUsage('initiatePointsSearch', { 
      deviceCount: deviceInstances.length, 
      protocol 
    });
    return this.bmsClient.initiatePointsSearch(deviceInstances, protocol);
  }

  /**
   * Step 5: Check Points Search Status
   */
  async checkPointsSearchStatus(taskId: string): Promise<PointsSearchStatusResponse> {
    console.warn('DEPRECATED: Use BMSClient.checkPointsSearchStatus instead');
    trackDeprecatedUsage('checkPointsSearchStatus', { taskId });
    return this.bmsClient.checkPointsSearchStatus(taskId);
  }

  /**
   * Step 6: Fetch Points for Single Device
   */
  async fetchDevicePoints(deviceInstance: number, deviceAddress: string, protocol: string = 'bacnet'): Promise<DevicePointsResponse> {
    console.warn('DEPRECATED: Use BMSClient.fetchDevicePoints instead');
    trackDeprecatedUsage('fetchDevicePoints', { 
      deviceInstance, 
      deviceAddress, 
      protocol 
    });
    return this.bmsClient.fetchDevicePoints(deviceInstance, deviceAddress, protocol);
  }

  /**
   * Step 7: Check Device Points Status
   */
  async checkDevicePointsStatus(taskId: string): Promise<DevicePointsStatusResponse> {
    console.warn('DEPRECATED: Use BMSClient.checkDevicePointsStatus instead');
    trackDeprecatedUsage('checkDevicePointsStatus', { taskId });
    return this.bmsClient.checkDevicePointsStatus(taskId);
  }

  /**
   * Helper: Poll until task is complete
   */
  async pollUntilComplete<T>(
    checkFn: () => Promise<T>,
    isCompleteFn: (response: T) => boolean,
    interval: number = 10000,
    maxAttempts: number = 30
  ): Promise<T> {
    console.warn('DEPRECATED: Use BMSClient.pollUntilComplete instead');
    trackDeprecatedUsage('pollUntilComplete', { interval, maxAttempts });
    return this.bmsClient.pollUntilComplete(checkFn, isCompleteFn, interval, maxAttempts);
  }

  /**
   * Group points by device type and device instance
   */
  async groupPoints(points: string[], useAi: boolean = true): Promise<GroupPointsResponse> {
    console.warn('DEPRECATED: Use BMSClient.groupPoints instead');
    trackDeprecatedUsage('groupPoints', { pointCount: points.length, useAi });
    return this.bmsClient.groupPoints(points, useAi);
  }

  /**
   * Map points to EnOS schema
   */
  async mapPoints(points: PointMapping[], useAi: boolean = true): Promise<MapPointsResponse> {
    console.warn('DEPRECATED: Use BMSClient.mapPoints instead');
    trackDeprecatedUsage('mapPoints', { pointCount: points.length, useAi });
    return this.bmsClient.mapPoints(points, useAi);
  }
} 