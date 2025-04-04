/**
 * @deprecated IMPORTANT: This entire file is deprecated and will be removed in a future version.
 * Use the BMSClient class and useBMSClient hook instead.
 * 
 * Migration Guide:
 * - For components: import { useBMSClient } from '../hooks/useBMSClient'
 * - For services: import { BMSClient, createBMSClient } from './bmsClient'
 * - Function mapping:
 *   - fetchPoints → bmsClient.fetchPoints
 *   - fetchDevices → bmsClient.fetchDevices
 *   - getNetworkConfig → bmsClient.getNetworkConfig
 *   - discoverDevices → bmsClient.discoverDevices
 *   - groupPointsWithAI → bmsClient.groupPointsWithAI
 *   - mapPointsToEnOS → bmsClient.mapPointsToEnOS
 *   - saveMappingToCSV → bmsClient.saveMappingToCSV
 *   - listSavedMappingFiles → bmsClient.listSavedMappingFiles
 *   - loadMappingFromCSV → bmsClient.loadMappingFromCSV
 *   - getFileDownloadURL → bmsClient.getFileDownloadURL
 *   - exportMappingToEnOS → bmsClient.exportMappingToEnOS
 * 
 * Legacy BMS Service - DEPRECATED
 * This service is being phased out in favor of the consolidated BMSClient.
 * Use with caution as it will be removed in a future version.
 */

import { 
  BMSPoint,
  BMSPointRaw,
  // These types are commented out as they're not currently used
  // but may be needed in future implementations
  // FetchPointsRequest, 
  // FetchPointsResponse, 
  // HttpMethod
} from '../types/apiTypes';
// import { request } from '../api/apiClient';
import { BMSClient, createBMSClient, BMSClientConfig } from './bmsClient';
import axios from 'axios';

// Import logger utility if available or define a simple logger
import { logger } from '../utils/logger';

// Create a shared client instance for all legacy methods
let sharedBmsClient: BMSClient | null = null;

// Default API credentials
const DEFAULT_CREDENTIALS = {
  accessKey: '',
  secretKey: ''
};

/**
 * Track usage of deprecated functions to help plan for removal
 * @private Internal tracking function
 */
function trackDeprecatedUsage(functionName: string, details?: Record<string, unknown>): void {
  // Log the usage with appropriate metadata
  logger.warn(`DEPRECATED_USAGE: ${functionName}`, { 
    service: 'bmsService',
    functionName,
    timestamp: new Date().toISOString(),
    ...details
  });
  
  // If available in the environment, send telemetry data
  // This could be expanded to use an analytics service
  if (process.env.REACT_APP_TRACK_DEPRECATIONS === 'true' && 
      typeof window !== 'undefined' && 
      window.performance && 
      window.performance.mark) {
    window.performance.mark(`deprecated_${functionName}`);
  }
}

/**
 * Get or create a shared BMS client instance
 */
function getSharedClient(config: Partial<APIConfig>): BMSClient {
  // Ensure required properties are present
  const fullConfig: APIConfig = {
    ...DEFAULT_CREDENTIALS,
    ...config,
    accessKey: config.accessKey || DEFAULT_CREDENTIALS.accessKey,
    secretKey: config.secretKey || DEFAULT_CREDENTIALS.secretKey
  };
  
  if (!sharedBmsClient) {
    sharedBmsClient = createBMSClient(fullConfig);
  } else {
    // Update the config if needed
    sharedBmsClient.updateConfig(fullConfig);
  }
  return sharedBmsClient;
}

/**
 * API configuration
 * @deprecated Use BMSClientConfig from bmsClient.ts instead
 */
export interface APIConfig extends BMSClientConfig {
  // No additional fields needed
}

// Exported for potential future use
export interface BMSServicePaginatedResponse<T> {
  record?: T[];
  totalCount?: number;
  hasMore?: boolean;
  page?: number;
  pageSize?: number;
}

/**
 * Convert a raw point from the API into the application's BMSPoint format
 * @deprecated Use BMSClient.mapRawPoint or utility function in a dedicated utils file instead.
 * This function will be removed in a future version.
 * Migration example:
 * ```
 * // Before
 * import { mapRawPoint } from '../api/bmsService';
 * const point = mapRawPoint(rawPoint);
 * 
 * // After - with BMSClient
 * import { BMSClient } from '../api/bmsClient';
 * const point = BMSClient.mapRawPoint(rawPoint);
 * 
 * // After - with utility function
 * import { mapBMSRawPoint } from '../utils/pointsUtils';
 * const point = mapBMSRawPoint(rawPoint);
 * ```
 * @private Currently only used internally, but exported for potential future use
 */
export function mapRawPoint(rawPoint: BMSPointRaw): BMSPoint {
  console.warn('DEPRECATED: Use BMSClient.mapRawPoint or a utility function instead of bmsService.mapRawPoint');
  trackDeprecatedUsage('mapRawPoint', { pointId: rawPoint.id || rawPoint.pointId });
  
  return {
    id: rawPoint.id || rawPoint.pointId || `point-${Math.random().toString(36).substr(2, 9)}`,
    pointName: rawPoint.pointName || '',
    pointType: rawPoint.pointType || 'Unknown',
    unit: rawPoint.unit || '',
    description: rawPoint.description || ''
  };
}

/**
 * Fetch BMS points from a device
 * @deprecated Use BMSClient.fetchPoints or useBMSClient().fetchPoints instead.
 * This function will be removed in a future version.
 * Migration example:
 * ```
 * // Before
 * const points = await fetchPoints(assetId, deviceInstance, deviceAddress, apiConfig, page, pageSize);
 * 
 * // After - with hook
 * const bmsClient = useBMSClient(apiConfig);
 * const points = await bmsClient.fetchPoints(deviceInstance, deviceAddress, page, pageSize);
 * 
 * // After - with class
 * const client = createBMSClient({...apiConfig, assetId});
 * const points = await client.fetchPoints(deviceInstance, deviceAddress, page, pageSize);
 * ```
 */
export async function fetchPoints(
  assetId: string,
  deviceInstance: string | number,
  deviceAddress: string,
  config: APIConfig,
  page: number = 0,
  pageSize: number = 100,
  onProgress?: (current: number, total: number, points: BMSPoint[]) => void
): Promise<BMSPoint[]> {
  console.warn('DEPRECATED: Use BMSClient.fetchPoints instead of bmsService.fetchPoints');
  trackDeprecatedUsage('fetchPoints', { assetId, deviceInstance, deviceAddress, page, pageSize });
  
  // Use consolidated client
  const client = getSharedClient({
    ...config,
    assetId
  });
  
  return client.fetchPoints(
    deviceInstance,
    deviceAddress,
    page,
    pageSize,
    onProgress
  );
}

/**
 * Fetch devices for an asset
 * @deprecated Use BMSClient.fetchDevices or useBMSClient().fetchDevices instead.
 * This function will be removed in a future version.
 * Migration example:
 * ```
 * // Before
 * const devices = await fetchDevices(assetId);
 * 
 * // After - with hook
 * const bmsClient = useBMSClient({assetId});
 * const devices = await bmsClient.fetchDevices();
 * 
 * // After - with class
 * const client = createBMSClient({assetId});
 * const devices = await client.fetchDevices();
 * ```
 */
export async function fetchDevices(assetId: string) {
  console.warn('DEPRECATED: Use BMSClient.fetchDevices instead of bmsService.fetchDevices');
  trackDeprecatedUsage('fetchDevices', { assetId });
  
  // Use consolidated client
  const client = getSharedClient({ 
    assetId,
    accessKey: DEFAULT_CREDENTIALS.accessKey,
    secretKey: DEFAULT_CREDENTIALS.secretKey
  });
  return client.fetchDevices();
}

/**
 * Get available networks for asset
 * @deprecated Use BMSClient.getNetworkConfig or useBMSClient().getNetworkConfig instead.
 * This function will be removed in a future version.
 * Migration example:
 * ```
 * // Before
 * const networks = await getNetworkConfig(assetId);
 * 
 * // After - with hook
 * const bmsClient = useBMSClient({assetId});
 * const networks = await bmsClient.getNetworkConfig();
 * 
 * // After - with class
 * const client = createBMSClient({assetId});
 * const networks = await client.getNetworkConfig();
 * ```
 */
export async function getNetworkConfig(assetId: string) {
  console.warn('DEPRECATED: Use BMSClient.getNetworkConfig instead of bmsService.getNetworkConfig');
  trackDeprecatedUsage('getNetworkConfig', { assetId });
  
  // Use consolidated client
  const client = getSharedClient({ 
    assetId,
    accessKey: DEFAULT_CREDENTIALS.accessKey, 
    secretKey: DEFAULT_CREDENTIALS.secretKey
  });
  return client.getNetworkConfig();
}

/**
 * Discover devices on network
 * @deprecated Use BMSClient.discoverDevices or useBMSClient().discoverDevices instead.
 * This function will be removed in a future version.
 * Migration example:
 * ```
 * // Before
 * const result = await discoverDevices(assetId, network);
 * 
 * // After - with hook
 * const bmsClient = useBMSClient({assetId});
 * const result = await bmsClient.discoverDevices([network]);
 * 
 * // After - with class
 * const client = createBMSClient({assetId});
 * const result = await client.discoverDevices([network]);
 * ```
 */
export async function discoverDevices(assetId: string, network: string) {
  console.warn('DEPRECATED: Use BMSClient.discoverDevices instead of bmsService.discoverDevices');
  trackDeprecatedUsage('discoverDevices', { assetId, network });
  
  // Use consolidated client
  const client = getSharedClient({ 
    assetId,
    accessKey: DEFAULT_CREDENTIALS.accessKey,
    secretKey: DEFAULT_CREDENTIALS.secretKey
  });
  return client.discoverDevices([network]);
}

/**
 * Group points using AI-based semantic analysis
 * @deprecated Use BMSClient.groupPointsWithAI or useBMSClient().groupPointsWithAI instead.
 * This function will be removed in a future version.
 * Migration example:
 * ```
 * // Before
 * const result = await groupPointsWithAI(points, apiConfig);
 * 
 * // After - with hook
 * const bmsClient = useBMSClient(apiConfig);
 * const result = await bmsClient.groupPointsWithAI(points);
 * 
 * // After - with class
 * const client = createBMSClient(apiConfig);
 * const result = await client.groupPointsWithAI(points);
 * ```
 * @param points Array of points to group
 * @param config API configuration
 * @returns Promise with grouped points
 */
export const groupPointsWithAI = async (
  points: BMSPoint[],
  config: APIConfig
): Promise<{
  success: boolean;
  grouped_points?: Record<string, {
    name: string;
    description: string;
    points: BMSPoint[];
    subgroups: Record<string, unknown>;
  }>;
  stats?: {
    total_points: number;
    equipment_types: number;
    equipment_instances: number;
  };
  method?: string;
  error?: string;
}> => {
  console.warn('DEPRECATED: Use BMSClient.groupPointsWithAI instead of bmsService.groupPointsWithAI');
  trackDeprecatedUsage('groupPointsWithAI', { pointCount: points.length });
  
  try {
    const url = `${config.apiGateway || ''}/api/bms/ai-group-points`;
    
    const response = await axios.post(url, {
      points,
      strategy: 'ai'
    }, {
      headers: {
        'Content-Type': 'application/json',
        'X-Access-Key': config.accessKey,
        'X-Secret-Key': config.secretKey
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error grouping points with AI:', error);
    if (error instanceof Error) {
      throw new Error(`Failed to group points with AI: ${error.message}`);
    }
    throw new Error('Failed to group points with AI');
  }
};

/**
 * Map BMS points to EnOS points
 * @deprecated Use BMSClient.mapPointsToEnOS or useBMSClient().mapPointsToEnOS instead.
 * This function will be removed in a future version.
 * Migration example:
 * ```
 * // Before
 * const result = await mapPointsToEnOS(points, apiConfig, mappingConfig);
 * 
 * // After - with hook
 * const bmsClient = useBMSClient(apiConfig);
 * const result = await bmsClient.mapPointsToEnOS(points, mappingConfig);
 * 
 * // After - with class
 * const client = createBMSClient(apiConfig);
 * const result = await client.mapPointsToEnOS(points, mappingConfig);
 * ```
 * @param points Array of points to map
 * @param config API configuration
 * @param mappingConfig Configuration for the mapping process
 * @returns Promise with mapping results
 */
export const mapPointsToEnOS = async (
  points: BMSPoint[],
  config: APIConfig,
  mappingConfig: {
    targetSchema?: string;
    transformationRules?: Record<string, string>;
    matchingStrategy?: 'strict' | 'fuzzy' | 'ai';
  }
): Promise<{
  success: boolean;
  mappings?: Array<{
    pointId: string;
    pointName: string;
    pointType: string;
    enosPoints: string;
    status: 'mapped' | 'error';
    error?: string;
  }>;
  stats?: {
    total: number;
    mapped: number;
    errors: number;
  };
  error?: string;
}> => {
  console.warn('DEPRECATED: Use BMSClient.mapPointsToEnOS instead of bmsService.mapPointsToEnOS');
  trackDeprecatedUsage('mapPointsToEnOS', { 
    pointCount: points.length, 
    strategy: mappingConfig.matchingStrategy || 'ai',
    targetSchema: mappingConfig.targetSchema 
  });
  
  try {
    const url = `${config.apiGateway || ''}/api/bms/map-points`;
    
    const response = await axios.post(url, {
      points,
      targetSchema: mappingConfig.targetSchema || 'default',
      transformationRules: mappingConfig.transformationRules || {},
      matchingStrategy: mappingConfig.matchingStrategy || 'ai',
    }, {
      headers: {
        'Content-Type': 'application/json',
        'X-Access-Key': config.accessKey,
        'X-Secret-Key': config.secretKey
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error mapping points to EnOS:', error);
    if (error instanceof Error) {
      throw new Error(`Failed to map points to EnOS: ${error.message}`);
    }
    throw new Error('Failed to map points to EnOS');
  }
};

/**
 * Save mapping to CSV file
 * @deprecated Use BMSClient.saveMappingToCSV or useBMSClient().saveMappingToCSV instead.
 * This function will be removed in a future version.
 * Migration example:
 * ```
 * // Before
 * const result = await saveMappingToCSV(mapping, apiConfig, filename);
 * 
 * // After - with hook
 * const bmsClient = useBMSClient(apiConfig);
 * const result = await bmsClient.saveMappingToCSV(mapping, filename);
 * 
 * // After - with class
 * const client = createBMSClient(apiConfig);
 * const result = await client.saveMappingToCSV(mapping, filename);
 * ```
 * @param mapping Mapping data to save
 * @param config API configuration
 * @param filename Optional filename
 * @returns Promise with save result
 */
export const saveMappingToCSV = async (
  mapping: Array<{
    enosEntity: string;
    enosPoint: string;
    rawPoint: string;
    rawUnit: string;
    rawFactor: number;
  }>,
  config: APIConfig,
  filename?: string
): Promise<{
  success: boolean;
  filepath?: string;
  error?: string;
}> => {
  console.warn('DEPRECATED: Use BMSClient.saveMappingToCSV instead of bmsService.saveMappingToCSV');
  trackDeprecatedUsage('saveMappingToCSV', { 
    mappingCount: mapping.length,
    filename: filename 
  });
  
  try {
    const url = `${config.apiGateway || ''}/api/bms/save-mapping`;
    
    const response = await axios.post(url, {
      mapping,
      filename
    }, {
      headers: {
        'Content-Type': 'application/json',
        'X-Access-Key': config.accessKey,
        'X-Secret-Key': config.secretKey
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error saving mapping to CSV:', error);
    if (error instanceof Error) {
      throw new Error(`Failed to save mapping: ${error.message}`);
    }
    throw new Error('Failed to save mapping');
  }
};

/**
 * List saved mapping files
 * @deprecated Use BMSClient.listSavedMappingFiles or useBMSClient().listSavedMappingFiles instead.
 * This function will be removed in a future version.
 * Migration example:
 * ```
 * // Before
 * const result = await listSavedMappingFiles(apiConfig);
 * 
 * // After - with hook
 * const bmsClient = useBMSClient(apiConfig);
 * const result = await bmsClient.listSavedMappingFiles();
 * 
 * // After - with class
 * const client = createBMSClient(apiConfig);
 * const result = await client.listSavedMappingFiles();
 * ```
 * @param config API configuration
 * @returns Promise with list of saved files
 */
export const listSavedMappingFiles = async (
  config: APIConfig
): Promise<{
  success: boolean;
  files?: Array<{
    filename: string;
    filepath: string;
    size: number;
    modified: string;
  }>;
  error?: string;
}> => {
  console.warn('DEPRECATED: Use BMSClient.listSavedMappingFiles instead of bmsService.listSavedMappingFiles');
  trackDeprecatedUsage('listSavedMappingFiles', {});
  
  try {
    const url = `${config.apiGateway || ''}/api/bms/list-saved-files`;
    
    const response = await axios.get(url, {
      headers: {
        'X-Access-Key': config.accessKey,
        'X-Secret-Key': config.secretKey
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error listing saved mapping files:', error);
    if (error instanceof Error) {
      throw new Error(`Failed to list saved mappings: ${error.message}`);
    }
    throw new Error('Failed to list saved mappings');
  }
};

/**
 * Load mapping from CSV file
 * @deprecated Use BMSClient.loadMappingFromCSV or useBMSClient().loadMappingFromCSV instead.
 * This function will be removed in a future version.
 * Migration example:
 * ```
 * // Before
 * const result = await loadMappingFromCSV(filepath, apiConfig);
 * 
 * // After - with hook
 * const bmsClient = useBMSClient(apiConfig);
 * const result = await bmsClient.loadMappingFromCSV(filepath);
 * 
 * // After - with class
 * const client = createBMSClient(apiConfig);
 * const result = await client.loadMappingFromCSV(filepath);
 * ```
 * @param filepath Path to the CSV file
 * @param config API configuration
 * @returns Promise with the file data
 */
export const loadMappingFromCSV = async (
  filepath: string,
  config: APIConfig
): Promise<{
  success: boolean;
  data?: Array<Record<string, unknown>>;
  error?: string;
}> => {
  console.warn('DEPRECATED: Use BMSClient.loadMappingFromCSV instead of bmsService.loadMappingFromCSV');
  trackDeprecatedUsage('loadMappingFromCSV', { filepath });
  
  try {
    const url = `${config.apiGateway || ''}/api/bms/load-csv`;
    
    const response = await axios.post(url, {
      filepath
    }, {
      headers: {
        'Content-Type': 'application/json',
        'X-Access-Key': config.accessKey,
        'X-Secret-Key': config.secretKey
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error loading mapping from CSV:', error);
    if (error instanceof Error) {
      throw new Error(`Failed to load mapping: ${error.message}`);
    }
    throw new Error('Failed to load mapping');
  }
};

/**
 * Generate download URL for a file
 * @deprecated Use BMSClient.getFileDownloadURL or useBMSClient().getFileDownloadURL instead.
 * This function will be removed in a future version.
 * Migration example:
 * ```
 * // Before
 * const url = getFileDownloadURL(filepath, apiConfig);
 * 
 * // After - with hook
 * const bmsClient = useBMSClient(apiConfig);
 * const url = bmsClient.getFileDownloadURL(filepath);
 * 
 * // After - with class
 * const client = createBMSClient(apiConfig);
 * const url = client.getFileDownloadURL(filepath);
 * ```
 * @param filepath Path to the file
 * @param config API configuration
 * @returns Download URL for the file
 */
export const getFileDownloadURL = (
  filepath: string,
  config: APIConfig
): string => {
  console.warn('DEPRECATED: Use BMSClient.getFileDownloadURL instead of bmsService.getFileDownloadURL');
  trackDeprecatedUsage('getFileDownloadURL', { filepath });
  
  return `${config.apiGateway || ''}/api/bms/download-file?filepath=${encodeURIComponent(filepath)}`;
};

/**
 * Export mapping to a format compatible with EnOS
 * @deprecated Use BMSClient.exportMappingToEnOS or useBMSClient().exportMappingToEnOS instead.
 * This function will be removed in a future version.
 * Migration example:
 * ```
 * // Before
 * const result = await exportMappingToEnOS(mapping, apiConfig);
 * 
 * // After - with hook
 * const bmsClient = useBMSClient(apiConfig);
 * const result = await bmsClient.exportMappingToEnOS(mapping);
 * 
 * // After - with class
 * const client = createBMSClient(apiConfig);
 * const result = await client.exportMappingToEnOS(mapping);
 * ```
 * @param mapping Mapping data to export
 * @param config API configuration
 * @returns Promise with export result
 */
export const exportMappingToEnOS = async (
  mapping: Array<{
    enosEntity: string;
    enosPoint: string;
    rawPoint: string;
    rawUnit: string;
    rawFactor: number;
  }>,
  config: APIConfig
): Promise<{
  success: boolean;
  filepath?: string;
  exportData?: Record<string, unknown>;
  error?: string;
}> => {
  console.warn('DEPRECATED: Use BMSClient.exportMappingToEnOS instead of bmsService.exportMappingToEnOS');
  trackDeprecatedUsage('exportMappingToEnOS', { mappingCount: mapping.length });
  
  try {
    const url = `${config.apiGateway || ''}/api/bms/export-mapping`;
    
    const response = await axios.post(url, {
      mapping
    }, {
      headers: {
        'Content-Type': 'application/json',
        'X-Access-Key': config.accessKey,
        'X-Secret-Key': config.secretKey
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error exporting mapping to EnOS:', error);
    if (error instanceof Error) {
      throw new Error(`Failed to export mapping: ${error.message}`);
    }
    throw new Error('Failed to export mapping');
  }
}; 