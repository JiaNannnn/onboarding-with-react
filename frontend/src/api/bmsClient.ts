/**
 * Consolidated BMS API Client
 * 
 * This client handles all BMS-related API operations including:
 * - Network configuration
 * - Device discovery
 * - Points search and retrieval
 * - Points grouping and mapping
 * 
 * It uses the unified API client from core/apiClient.ts as the foundation for HTTP requests
 * and enforces the localhost:5000 base URL policy.
 */

import { api } from './apiClient';
import { 
  BMSPoint,
  BMSPointRaw,
  FetchPointsRequest
} from '../types/apiTypes';

// Define the versioned API base path
const API_V1_PATH = '/api/v1';

// Define the type for the api object methods we use
type ApiMethods = {
  get: <T>(url: string, params?: Record<string, any>, config?: any) => Promise<T>;
  post: <T>(url: string, data?: any, config?: any) => Promise<T>;
  put: <T>(url: string, data?: any, config?: any) => Promise<T>;
  delete: <T>(url: string, config?: any) => Promise<T>;
  // Add index signature to allow accessing properties like 'baseURL', 'assetId', 'orgId' if needed for config
  [key: string]: any; 
};

/**
 * Unified configuration interface for BMS API operations
 */
export interface BMSClientConfig {
  // API credentials and endpoints
  apiGateway?: string;  // External API gateway (passed in request body only)
  accessKey: string;    // Access key for authentication
  secretKey: string;    // Secret key for authentication
  
  // Optional organization and asset identifiers
  orgId?: string;      // Organization ID
  assetId?: string;    // Asset ID
  
  // Legacy parameter (for backward compatibility)
  apiUrl?: string;     // Legacy API URL parameter
}

/**
 * Network interface information
 */
export interface NetworkInterface {
  id: string;
  name: string;
  description: string;
  ipAddress: string;
  macAddress: string;
  isActive: boolean;
}

/**
 * Network configuration response
 */
export interface NetworkConfigResponse {
  networks: NetworkInterface[];
  status: string;
  message?: string;
}

/**
 * Device discovery response
 */
export interface DeviceDiscoveryResponse {
  message: string;
  task_id?: string;
  taskId?: string;
  status: string;
}

/**
 * Device discovery status response
 */
export interface DeviceDiscoveryStatusResponse {
  status: string;
  result?: {
    code?: number;
    all_devices?: Array<{
      otDeviceInst: number;
      deviceName: string;
      address: string;
    }>;
    devices?: Array<{
      instanceNumber: number;
      name: string;
      address: string;
      model?: string;
      vendor?: string;
    }>;
    count: number;
  };
}

/**
 * Points search response
 */
export interface PointsSearchResponse {
  message: string;
  task_id?: string;
  taskId?: string;
  status: string;
}

/**
 * Device points response
 */
export interface DevicePointsResponse {
  message: string;
  task_id?: string;
  taskId?: string;
  status: string;
}

/**
 * Points search status response
 */
export interface PointsSearchStatusResponse {
  status: string;
  result?: {
    status: string;
    message: string;
    device_tasks?: {
      [deviceInstance: string]: {
        task_id: string;
        status: string;
        point_count?: number;
      };
    };
  };
  pointCount?: number;
  samplePoints?: Array<{
    name: string;
    value: any;
    units: string;
  }>;
}

/**
 * Device points status response
 */
export interface DevicePointsStatusResponse {
  status: string;
  point_count?: number;
  pointCount?: number;
  file_path?: string;
  sample_points?: Array<{
    pointId: string;
    pointName: string;
    pointType: string;
    description: string;
  }>;
  samplePoints?: Array<{
    name: string;
    value: any;
    units: string;
  }>;
}

/**
 * Point grouping request 
 */
export interface GroupPointsRequest {
  points: string[];
  useAi?: boolean;
}

/**
 * Point grouping response
 */
export interface GroupPointsResponse {
  message: string;
  groups: {
    [deviceType: string]: {
      [deviceId: string]: string[];
    };
  };
  count: {
    totalPoints: number;
    deviceTypes: number;
    devices: number;
  };
  method: string;
}

/**
 * Point mapping
 */
export interface PointMapping {
  pointName: string;
  deviceType: string;
  enosPoint?: string;
  status?: string;
}

/**
 * Point mapping request
 */
export interface MapPointsRequest {
  points: PointMapping[];
  useAi?: boolean;
}

/**
 * Point mapping response
 */
export interface MapPointsResponse {
  success: boolean;
  message?: string;
  mappings: PointMapping[];
  statistics?: {
    total: number;
    mapped: number;
    unmapped: number;
    errors: number;
    timeouts: number;
  };
  method?: string;
  error?: string;
}

/**
 * Paginated response interface
 */
export interface PaginatedResponse<T> {
  record?: T[];
  totalCount?: number;
  hasMore?: boolean;
  page?: number;
  pageSize?: number;
}

/**
 * Helper function to safely convert optional string to required string
 */
function ensureString(value?: string): string {
  return value || '';
}

/**
 * Group points with AI response interface
 */
export interface GroupPointsWithAIResponse {
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
}

/**
 * Map points to EnOS response interface
 */
export interface MapPointsToEnOSResponse {
  success: boolean;
  mappings?: Array<{
    original?: {
      pointName: string;
      deviceType: string;
      deviceId: string;
      pointType: string;
      unit: string;
      value: any;
    };
    mapping?: {
      pointId: string;
      enosPoint: string | null;
      status: 'mapped' | 'error';
      error?: string;
    };
    // For backward compatibility with older format
    pointId?: string;
    pointName?: string;
    pointType?: string;
    enosPoint?: string;
    status?: 'mapped' | 'error';
    // Additional fields from enhanced implementation
    deviceType?: string;
    deviceId?: string;
    unit?: string;
    pointCategory?: string;
    mappingSource?: string;
  }>;
  stats?: {
    total: number;
    mapped: number;
    errors: number;
    deviceCount?: number;
    deviceTypes?: number;
    timeouts?: number;
    unmapped?: number;
  };
  error?: string;
  message?: string;
  status?: string;
  taskId?: string;
  targetSchema?: string;
  // Batch processing fields
  batchMode?: boolean;
  totalBatches?: number;
  completedBatches?: number;
  progress?: number;
}

/**
 * Mapping configuration interface
 */
export interface MappingConfig {
  targetSchema?: string;
  transformationRules?: Record<string, string>;
  matchingStrategy?: 'strict' | 'fuzzy' | 'ai';
  includeDeviceContext?: boolean;
  deviceTypes?: string[];
  includeSuggestions?: boolean;
  prioritizeFailedPatterns?: boolean;
  includeReflectionData?: boolean;
}

/**
 * Mapping data interface
 */
export interface MappingData {
  enosEntity: string;
  enosPoint: string;
  rawPoint: string;
  rawUnit?: string;
  rawFactor?: number;
}

/**
 * Save mapping response interface
 */
export interface SaveMappingResponse {
  success: boolean;
  filepath?: string;
  error?: string;
}

/**
 * List files response interface
 */
export interface ListFilesResponse {
  success: boolean;
  files?: Array<{
    filename: string;
    filepath: string;
    size: number;
    modified: string;
  }>;
  error?: string;
}

/**
 * Load CSV response interface
 */
export interface LoadCSVResponse {
  success: boolean;
  data?: Array<Record<string, unknown>>;
  error?: string;
}

/**
 * Export mapping response interface
 */
export interface ExportMappingResponse {
  success: boolean;
  filepath?: string;
  exportData?: Record<string, unknown>;
  error?: string;
}

/**
 * BMS Client that handles all BMS API operations
 */
export class BMSClient {
  private apiClient: ApiMethods; // Use the defined type
  
  /**
   * Create a new BMS client instance
   */
  constructor(config: BMSClientConfig) {
    // Create API client for BMS operations with the provided configuration
    this.apiClient = api;
  }
  
  /**
   * Test backend connectivity
   */
  async pingBackend(): Promise<{ status: string }> {
    try {
      console.log('Attempting to ping backend...');
      const response = await this.apiClient.get<{ status: string }>('/api');
      console.log('Ping response:', response);
      return response;
    } catch (error) {
      console.error('Ping failed:', error);
      throw error;
    }
  }
  
  /**
   * Get network configuration
   */
  async getNetworkConfig(): Promise<NetworkInterface[]> {
    try {
      console.log('Attempting to get network config');
      
      // First try the versioned endpoint
      try {
        console.log('Trying versioned endpoint');
        const response = await this.apiClient.post<NetworkConfigResponse>(`${API_V1_PATH}/networks`, {});
        return response.networks || [];
      } catch (v1Error) {
        console.log('V1 endpoint failed, trying legacy endpoint');
        // Fall back to the legacy endpoint as a last resort
        const response = await this.apiClient.post<{ status: string, networks: string[] }>('/api/network-config', {});
        
        // Convert legacy format to new format
        return (response.networks || []).map((network: string, index: number) => ({
          id: `network-${index}`,
          name: network,
          description: `Network interface ${network}`,
          ipAddress: network,
          macAddress: '',
          isActive: true
        }));
      }
    } catch (error) {
      console.error('Network config failed:', error);
      throw error;
    }
  }
  
  /**
   * Discover devices on selected networks
   */
  async discoverDevices(networks: string[], protocol: string = 'bacnet'): Promise<DeviceDiscoveryResponse> {
    try {
      // Try the recommended v1 endpoint first
      const response = await this.apiClient.post<DeviceDiscoveryResponse>(`${API_V1_PATH}/devices/discover`, {
        networks,
        protocol
      });
      return response;
    } catch (error) {
      console.log('V1 endpoint failed, trying legacy endpoint');
      // Fall back to the legacy endpoint
      const response = await this.apiClient.post<DeviceDiscoveryResponse>('/api/discover-devices', {
        networks,
        protocol
      });
      return response;
    }
  }

  /**
   * Check device discovery status
   */
  async checkDeviceDiscoveryStatus(taskId: string): Promise<DeviceDiscoveryStatusResponse> {
    try {
      // Try the recommended v1 endpoint first
      const response = await this.apiClient.get<DeviceDiscoveryStatusResponse>(`${API_V1_PATH}/devices/discover/${taskId}`);
      return response;
    } catch (error) {
      console.log('V1 endpoint failed, trying legacy endpoint');
      // Fall back to the legacy endpoint
      const response = await this.apiClient.get<DeviceDiscoveryStatusResponse>(`/api/discover-devices/${taskId}`);
      return response;
    }
  }

  /**
   * Initiate points search across multiple devices
   */
  async initiatePointsSearch(deviceInstances: number[], protocol: string = 'bacnet'): Promise<PointsSearchResponse> {
    try {
      // Try the recommended v1 endpoint first
      const response = await this.apiClient.post<PointsSearchResponse>(`${API_V1_PATH}/points/search`, {
        deviceIds: deviceInstances,
        protocol
      });
      return response;
    } catch (error) {
      console.log('V1 endpoint failed, trying legacy endpoint');
      // Fall back to the legacy endpoint
      const response = await this.apiClient.post<PointsSearchResponse>('/api/fetch-points', {
        deviceInstances,
        protocol
      });
      return response;
    }
  }

  /**
   * Check points search status
   */
  async checkPointsSearchStatus(taskId: string): Promise<PointsSearchStatusResponse> {
    try {
      // Try the recommended v1 endpoint first
      const response = await this.apiClient.get<PointsSearchStatusResponse>(`${API_V1_PATH}/tasks/${taskId}`);
      return response;
    } catch (error) {
      console.log('V1 endpoint failed, trying legacy endpoint');
      // Fall back to the legacy endpoint
      const response = await this.apiClient.get<PointsSearchStatusResponse>(`/api/fetch-points/${taskId}`);
      return response;
    }
  }

  /**
   * Fetch points for a single device
   */
  async fetchDevicePoints(deviceInstance: number, deviceAddress: string, protocol: string = 'bacnet'): Promise<DevicePointsResponse> {
    try {
      // Try the recommended v1 endpoint first
      const response = await this.apiClient.post<DevicePointsResponse>(`${API_V1_PATH}/devices/${deviceInstance}/points`, {
        deviceAddress,
        protocol
      });
      return response;
    } catch (error) {
      console.log('V1 endpoint failed, trying legacy endpoint');
      // Fall back to the legacy endpoint
      const response = await this.apiClient.post<DevicePointsResponse>('/api/device-points', {
        deviceInstance,
        deviceAddress,
        protocol
      });
      return response;
    }
  }

  /**
   * Check device points status
   */
  async checkDevicePointsStatus(taskId: string): Promise<DevicePointsStatusResponse> {
    try {
      // Try the recommended v1 endpoint first
      const response = await this.apiClient.get<DevicePointsStatusResponse>(`${API_V1_PATH}/tasks/${taskId}`);
      return response;
    } catch (error) {
      console.log('V1 endpoint failed, trying legacy endpoint');
      // Fall back to the legacy endpoint
      const response = await this.apiClient.get<DevicePointsStatusResponse>(`/api/device-points/${taskId}`);
      return response;
    }
  }

  /**
   * Fetch BMS points from a device with pagination
   */
  async fetchPoints(
    deviceInstance: string | number,
    deviceAddress: string,
    page: number = 0,
    pageSize: number = 100,
    onProgress?: (current: number, total: number, points: BMSPoint[]) => void
  ): Promise<BMSPoint[]> {
    let allPoints: BMSPoint[] = [];
    let currentPage = page;
    let totalFetched = 0;
    let totalPoints = 0;
    let hasMore = true;
    
    try {
      while (hasMore) {
        // Prepare request data
        const requestData: FetchPointsRequest = {
          assetId: ensureString(this.apiClient['assetId']), // Access private property - not ideal but works
          deviceInstance,
          deviceAddress,
          page: currentPage,
          pageSize
        };
        
        // Add orgId if available from the client
        if (this.apiClient['orgId']) {
          requestData.orgId = this.apiClient['orgId'] as string;
        }
        
        const response = await this.apiClient.post<PaginatedResponse<BMSPointRaw>>('/api/bms/points', requestData);

        // Parse response
        if (response?.record && Array.isArray(response.record)) {
          // Process points
          const rawPoints = response.record as BMSPointRaw[];
          const points = rawPoints.map(this.mapRawPoint);
          allPoints = [...allPoints, ...points];
          
          // Update counters
          totalFetched += points.length;
          
          // Update total on first page if available
          if (currentPage === 0 && response.totalCount !== undefined) {
            totalPoints = response.totalCount;
          }
          
          // Call progress callback if provided
          if (onProgress) {
            onProgress(totalFetched, totalPoints, points);
          }
          
          // Check if we should continue
          hasMore = !!response.hasMore;
          currentPage++;
        } else {
          // No more points or error
          hasMore = false;
        }
      }
      
      return allPoints;
    } catch (error) {
      console.error('Error fetching points:', error);
      throw error;
    }
  }
  
  /**
   * Convert a raw point from the API into the application's BMSPoint format
   */
  private mapRawPoint(rawPoint: BMSPointRaw): BMSPoint {
    return {
      id: rawPoint.id || rawPoint.pointId || `point-${Math.random().toString(36).substr(2, 9)}`,
      pointName: rawPoint.pointName || '',
      pointType: rawPoint.pointType || 'Unknown',
      unit: rawPoint.unit || '',
      description: rawPoint.description || ''
    };
  }

  /**
   * Fetch devices for an asset
   */
  async fetchDevices(): Promise<any> {
    try {
      const url = `/api/devices/list`;
      const response = await this.apiClient.get(url);
      return response;
    } catch (error) {
      console.error('Error fetching devices:', error);
      throw error;
    }
  }

  /**
   * Group points by device type and device instance
   */
  async groupPoints(points: string[], useAi: boolean = true): Promise<GroupPointsResponse> {
    try {
      const response = await this.apiClient.post<GroupPointsResponse>(`${API_V1_PATH}/points/group`, {
        points,
        useAi
      });
      return response;
    } catch (error) {
      console.log('V1 endpoint failed, trying legacy endpoint');
      // Fall back to legacy endpoint
      const response = await this.apiClient.post<GroupPointsResponse>('/api/group-points', {
        points,
        useAi
      });
      return response;
    }
  }

  /**
   * Map points to EnOS schema
   */
  async mapPoints(points: PointMapping[], useAi: boolean = true): Promise<MapPointsResponse> {
    try {
      const response = await this.apiClient.post<MapPointsResponse>(`${API_V1_PATH}/points/map`, {
        points,
        useAi
      });
      return response;
    } catch (error) {
      console.log('V1 endpoint failed, trying legacy endpoint');
      // Fall back to legacy endpoint
      const response = await this.apiClient.post<MapPointsResponse>('/api/map-points', {
        points,
        useAi
      });
      return response;
    }
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
    let attempts = 0;
    
    while (attempts < maxAttempts) {
      const response = await checkFn();
      if (isCompleteFn(response)) {
        return response;
      }
      
      attempts++;
      await new Promise(resolve => setTimeout(resolve, interval));
    }
    
    throw new Error(`Task did not complete after ${maxAttempts} attempts`);
  }
  
  /**
   * Check mapping task status
   * Public method for checking a mapping task's status
   */
  async checkPointsMappingStatus(taskId: string): Promise<MapPointsToEnOSResponse> {
    try {
      return await this.apiClient.get<MapPointsToEnOSResponse>(`${API_V1_PATH}/map-points/${taskId}`);
    } catch (error) {
      console.error(`Error checking mapping task status: ${error}`);
      return {
        success: false,
        error: `Failed to check status: ${error instanceof Error ? error.message : 'Unknown error'}`,
        stats: { total: 0, mapped: 0, errors: 1 }
      };
    }
  }
  /**con
   * Update client configuration
   */
  updateConfig(config: Partial<BMSClientConfig>): void {
    // Note: The base 'api' object is a singleton and cannot be reconfigured per instance this way.
    // Configuration like assetId/orgId should ideally be passed per request or handled differently.
    console.warn("BMSClient.updateConfig cannot reconfigure the shared API client instance.");
    // Store config values locally if needed for specific requests
    // e.g., this.orgId = ensureString(config.orgId);
  }

  /**
   * Group points using AI-based semantic analysis
   */
  async groupPointsWithAI(points: BMSPoint[]): Promise<GroupPointsWithAIResponse> {
    try {
      // Get base URL from the API client
      const baseURL = this.apiClient['apiGateway'] || 'http://localhost:5000';
      const url = `${baseURL}/api/bms/ai-group-points`;
      
      // Use the API client for the request
      const response = await this.apiClient.post<GroupPointsWithAIResponse>(url, {
        points,
        strategy: 'ai'
      });
      
      return response;
    } catch (error) {
      console.error('Error grouping points with AI:', error);
      if (error instanceof Error) {
        throw new Error(`Failed to group points with AI: ${error.message}`);
      }
      throw new Error('Failed to group points with AI');
    }
  }

  /**
   * Map BMS points to EnOS points with advanced configuration
   */
  async mapPointsToEnOS(
    points: BMSPoint[],
    mappingConfig: MappingConfig = {}
  ): Promise<MapPointsToEnOSResponse> {
    try {
      console.log(`Starting mapping of ${points.length} points to EnOS with config:`, mappingConfig);
      // Get base URL from the API client configuration if possible, otherwise default
      const baseURL = (this.apiClient as any)['baseURL'] || 'http://localhost:5000'; 
      const url = `${baseURL}${API_V1_PATH}/map-points`; // Construct full URL

      const response = await this.apiClient.post<MapPointsToEnOSResponse>(url, {
        points,
        mappingConfig,
      });

      // Check response structure
      if (!response.success) {
        console.error("Mapping response indicates failure:", response);
        throw new Error(response.error || 'Mapping operation failed');
      }
      
      // If taskId is present, poll for completion
      if (response.taskId) {
        console.log(`Mapping task started with ID: ${response.taskId}`);
        return await this.pollUntilComplete<MapPointsToEnOSResponse>(
          () => this.checkPointsMappingStatus(response.taskId!),
          (statusResponse) => statusResponse.status !== 'processing',
          5000, // Check every 5 seconds
          120   // Allow up to 120 attempts (10 minutes)
        );
      } else {
         // If no taskId, assume immediate completion (older API versions?)
         console.log("Mapping completed immediately (no task ID returned).");
         return response; 
      }
    } catch (error) {
      console.error('Error mapping points to EnOS:', error);
      // Return a consistent error response format
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred during mapping',
        stats: { total: points.length, mapped: 0, errors: points.length },
      };
    }
  }

  /**
   * Improve mapping results with a second round of AI mapping
   * This targets specific points that had poor quality mappings
   */
  async improveMappingResults(
    originalTaskId: string,
    qualityFilter: 'poor' | 'unacceptable' | 'below_fair' | 'all' = 'below_fair',
    mappingConfig: MappingConfig = {}
  ): Promise<MapPointsToEnOSResponse> {
    try {
      // Implementation requires backend endpoint and logic
      console.log('Improve mapping called with:', originalTaskId, qualityFilter, mappingConfig);
      // Placeholder: Simulate calling an improvement endpoint
      const baseURL = this.apiClient['apiGateway'] || 'http://localhost:5000';
      const url = `${baseURL}${API_V1_PATH}/map-points/improve`; // Hypothetical endpoint
      
      const response = await this.apiClient.post<MapPointsToEnOSResponse>(url, {
        original_mapping_id: originalTaskId,
        filter_quality: qualityFilter,
        mappingConfig: {
           ...mappingConfig,
           prioritizeFailedPatterns: true,
           includeReflectionData: true
         }
      });

      if (!response.success) {
         throw new Error(response.error || 'Improvement task failed');
      }

      if (response.taskId) {
         console.log(`Improvement task started: ${response.taskId}`);
         return await this.pollUntilComplete<MapPointsToEnOSResponse>(
           () => this.checkPointsMappingStatus(response.taskId!),
           (statusResponse) => statusResponse.status !== 'processing',
           5000, 120
         );
      } else {
         console.warn("Improvement endpoint did not return a task ID.");
         return response;
      }
    } catch (error) {
      console.error('Error improving mapping results:', error);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error improving mapping', 
        stats: { total: 0, mapped: 0, errors: 1 }
      };
    }
  }

  /**
   * Save mapping to CSV file
   */
  async saveMappingToCSV(
    mapping: MappingData[],
    filename?: string
  ): Promise<SaveMappingResponse> {
    try {
      const baseURL = this.apiClient['apiGateway'] || 'http://localhost:5000';
      const url = `${baseURL}/api/bms/save-mapping`; // Adjusted endpoint
      const response = await this.apiClient.post<SaveMappingResponse>(url, {
        mapping,
        filename
      });
      return response;
    } catch (error) {
      console.error('Error saving mapping to CSV:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Failed to save mapping' };
    }
  }

  /**
   * List saved mapping files
   */
  async listSavedMappingFiles(): Promise<ListFilesResponse> {
    try {
      const baseURL = this.apiClient['apiGateway'] || 'http://localhost:5000';
      const url = `${baseURL}/api/bms/list-saved-files`;
      const response = await this.apiClient.get<ListFilesResponse>(url);
      return response;
    } catch (error) {
      console.error('Error listing saved mapping files:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Failed to list saved mappings' };
    }
  }

  /**
   * Load mapping from CSV file
   */
  async loadMappingFromCSV(filepath: string): Promise<LoadCSVResponse> {
    try {
      const baseURL = this.apiClient['apiGateway'] || 'http://localhost:5000';
      const url = `${baseURL}/api/bms/load-csv`;
      const response = await this.apiClient.post<LoadCSVResponse>(url, { filepath });
      return response;
    } catch (error) {
      console.error('Error loading mapping from CSV:', error);
       return { success: false, error: error instanceof Error ? error.message : 'Failed to load mapping' };
    }
  }

  /**
   * Generate download URL for a file
   */
  getFileDownloadURL(filepath: string): string {
    const baseURL = this.apiClient['apiGateway'] || 'http://localhost:5000';
    return `${baseURL}/api/bms/download-file?filepath=${encodeURIComponent(filepath)}`;
  }

  /**
   * Export mapping to a format compatible with EnOS
   */
  async exportMappingToEnOS(mapping: MappingData[]): Promise<ExportMappingResponse> {
    try {
      const baseURL = this.apiClient['apiGateway'] || 'http://localhost:5000';
      const url = `${baseURL}/api/bms/export-mapping`;
      const response = await this.apiClient.post<ExportMappingResponse>(url, { mapping });
      return response;
    } catch (error) {
      console.error('Error exporting mapping to EnOS:', error);
       return { success: false, error: error instanceof Error ? error.message : 'Failed to export mapping' };
    }
  }
}