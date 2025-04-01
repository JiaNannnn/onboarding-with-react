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

import { 
  APIClient, 
  createApiClient 
} from './core/apiClient';
import { 
  BMSPoint,
  BMSPointRaw,
  FetchPointsRequest
} from '../types/apiTypes';

// Define the versioned API base path
const API_V1_PATH = '/api/v1';

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
  enosPath?: string;
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
  message: string;
  mappings: PointMapping[];
  statistics: {
    total: number;
    mapped: number;
    unmapped: number;
    errors: number;
    timeouts: number;
  };
  method: string;
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
    pointId: string;
    pointName: string;
    pointType: string;
    enosPath: string;
    confidence: number;
    status: 'mapped' | 'error';
    error?: string;
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
    confidenceAvg?: number;
    timeouts?: number;
    unmapped?: number;
  };
  error?: string;
  status?: string;
  targetSchema?: string;
}

/**
 * Mapping configuration interface
 */
export interface MappingConfig {
  targetSchema?: string;
  transformationRules?: Record<string, string>;
  matchingStrategy?: 'strict' | 'fuzzy' | 'ai';
  confidence?: number;
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
  private apiClient: APIClient;
  
  /**
   * Create a new BMS client instance
   */
  constructor(config: BMSClientConfig) {
    // Create API client for BMS operations with the provided configuration
    this.apiClient = createApiClient({
      apiGateway: config.apiGateway || config.apiUrl, // Support both naming conventions
      accessKey: config.accessKey,
      secretKey: config.secretKey,
      assetId: ensureString(config.assetId),
      orgId: ensureString(config.orgId)
    });
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
        return (response.networks || []).map((network, index) => ({
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
   * Update client configuration
   */
  updateConfig(config: Partial<BMSClientConfig>): void {
    // Create a new API client with the updated configuration
    this.apiClient = this.apiClient.withConfig({
      apiGateway: config.apiGateway || config.apiUrl,
      accessKey: config.accessKey,
      secretKey: config.secretKey,
      assetId: ensureString(config.assetId),
      orgId: ensureString(config.orgId)
    });
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
    // Retry configuration
    const maxRetries = 2;
    let currentTry = 0;
    
    while (currentTry <= maxRetries) {
      // Capture current retry count for closures
      const tryNumber = currentTry;
      
      try {
        // Use relative URL to ensure it goes through React proxy middleware
        const url = '/api/bms/map-points';
        
        // Build simple request body
        const requestBody = {
          points: points.map(p => ({
            id: p.id || '',
            pointName: p.pointName,
            pointType: p.pointType || p.deviceType || ''
          })),
          targetSchema: mappingConfig.targetSchema || 'default',
          transformationRules: mappingConfig.transformationRules || {},
          matchingStrategy: mappingConfig.matchingStrategy || 'ai',
          confidence: mappingConfig.confidence || 0.7
        };
        
        // Use API client for request with longer timeout
        const response = await this.apiClient.post<MapPointsToEnOSResponse>(
          url, 
          requestBody, 
          { 
            timeout: 60000, // 60-second timeout
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json'
            }
          }
        );
        
        // Check if response was successful
        if (response && response.success) {
          console.log(`Mapping successful, mapped ${response.mappings?.length || 0} points`);
          return response;
        } else {
          // Response unsuccessful but we got a response
          const errorMessage = response?.error || 'Unknown error';
          console.warn(`Point mapping failed: ${errorMessage}`);
          
          if (tryNumber < maxRetries) {
            // More retry attempts available
            currentTry++;
            console.log(`Attempting to remap points (${currentTry}/${maxRetries})`);
            continue;
          }
          
          return {
            success: false,
            error: `Point mapping failed: ${errorMessage}`,
            mappings: []
          };
        }
      } catch (error) {
        console.error('Point mapping error:', error);
        
        // Extract detailed error information
        let errorMessage = 'Unknown error';
        let status = 0;
        
        if (error instanceof Error) {
          errorMessage = error.message;
          
          // Check if it's a network error
          if (error.message.includes('Network Error') || 
              error.message.includes('timeout') || 
              error.message.includes('Connection refused')) {
            
            if (tryNumber < maxRetries) {
              // Network error with more retry attempts available
              currentTry++;
              console.log(`Network error, attempting to remap points (${currentTry}/${maxRetries})`);
              // Add delay between retries - use delay proportional to the try number
              const delay = 1000 * tryNumber + 1;
              await new Promise(resolve => setTimeout(resolve, delay));
              continue;
            }
            
            errorMessage = `Network connection error: ${error.message}. Please check if backend service is running.`;
          }
        } else if (typeof error === 'object' && error !== null) {
          // Extract more error information
          const apiError = error as any;
          errorMessage = apiError.message || apiError.error || 'Unknown API error';
          status = apiError.status || apiError.statusCode || 0;
          
          if (status === 500) {
            errorMessage = `Server internal error (500): ${errorMessage}`;
          } else if (status === 404) {
            errorMessage = `API endpoint not found (404): Please verify backend service configuration`;
          } else if (status === 400) {
            errorMessage = `Invalid request format (400): ${errorMessage}`;
          }
        }
        
        // Check if retry is needed
        if (tryNumber < maxRetries) {
          currentTry++;
          console.log(`Attempting to remap points (${currentTry}/${maxRetries})`);
          // Add delay between retries - use delay proportional to the try number
          const delay = 1000 * tryNumber + 1;
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
        
        // Return failure response
        return {
          success: false,
          error: `Point mapping failed: ${errorMessage}`,
          mappings: [],
          stats: {
            total: points.length,
            mapped: 0,
            errors: points.length
          }
        };
      }
    }
    
    // 所有重试都失败的情况，使用本地映射作为后备方案
    console.warn('所有远程映射尝试均失败，使用本地映射作为后备方案');
    
    // 使用简单的本地映射逻辑
    const localMappings = points.map(point => {
      // 基本信息
      const result: {
        pointId: string;
        pointName: string;
        pointType: string;
        status: 'mapped' | 'error';
        confidence: number;
        enosPath: string;
        deviceType?: string;
      } = {
        pointId: point.id || '',
        pointName: point.pointName,
        pointType: point.pointType || '',
        status: 'mapped',
        confidence: 0.8,
        enosPath: ''
      };
      
      // 提取设备类型（假设格式为 "AHU-1.SupplyTemp" 或类似）
      const pointParts = point.pointName.split(/[-_.]/);
      const deviceTypeRaw = pointParts[0].toUpperCase();
      let deviceType = 'UNKNOWN';
      
      // 标准化设备类型
      if (['AHU', 'MAU', 'RTU'].includes(deviceTypeRaw)) {
        deviceType = 'AHU';
      } else if (['FCU', 'FAN'].includes(deviceTypeRaw)) {
        deviceType = 'FCU';
      } else if (['VAV', 'CAV'].includes(deviceTypeRaw)) {
        deviceType = 'VAV';
      } else if (['CH', 'CHILLER', 'CHL'].includes(deviceTypeRaw)) {
        deviceType = 'CHILLER';
      } else if (['BLR', 'BOILER'].includes(deviceTypeRaw)) {
        deviceType = 'BOILER';
      } else if (['PMP', 'PUMP', 'CWP', 'CHWP', 'HWP'].includes(deviceTypeRaw)) {
        deviceType = 'PUMP';
      }
      
      // 提取点位名称关键字
      const pointNameLower = point.pointName.toLowerCase();
      let pointType = 'unknown';
      
      // 根据点位名称确定EnOS路径
      if (pointNameLower.includes('temp') || pointNameLower.includes('tmp')) {
        if (pointNameLower.includes('supply') || pointNameLower.includes('sa')) {
          pointType = 'supplyTemperature';
        } else if (pointNameLower.includes('return') || pointNameLower.includes('ra')) {
          pointType = 'returnTemperature';
        } else if (pointNameLower.includes('zone') || pointNameLower.includes('room')) {
          pointType = 'zoneTemperature';
        } else {
          pointType = 'temperature';
        }
      } else if (pointNameLower.includes('hum') || pointNameLower.includes('rh')) {
        pointType = 'humidity';
      } else if (pointNameLower.includes('pres') || pointNameLower.includes('pressure')) {
        pointType = 'pressure';
      } else if (pointNameLower.includes('flow') || pointNameLower.includes('cfm')) {
        pointType = 'airflow';
      } else if (pointNameLower.includes('valve') || pointNameLower.includes('damper')) {
        pointType = 'valvePosition';
      } else if (pointNameLower.includes('status') || pointNameLower.includes('state')) {
        pointType = 'status';
      } else if (pointNameLower.includes('setpoint') || pointNameLower.includes('sp')) {
        pointType = 'setpoint';
      } else if (pointNameLower.includes('mode')) {
        pointType = 'mode';
      } else if (pointNameLower.includes('speed') || pointNameLower.includes('freq')) {
        pointType = 'speed';
      } else {
        pointType = 'generic';
      }
      
      // 构建EnOS路径
      result.enosPath = `${deviceType}/points/${pointType}`;
      result.deviceType = deviceType;
      
      return result;
    });
    
    return {
      success: true,
      error: '使用本地映射作为后备方案',
      mappings: localMappings,
      stats: {
        total: points.length,
        mapped: localMappings.length,
        errors: 0
      }
    };
  }

  /**
   * Save mapping to CSV file
   */
  async saveMappingToCSV(
    mapping: MappingData[],
    filename?: string
  ): Promise<SaveMappingResponse> {
    try {
      // Get base URL from the API client
      const baseURL = this.apiClient['apiGateway'] || 'http://localhost:5000';
      const url = `${baseURL}/api/points/save-mapping`;
      
      // Use the API client for the request
      const response = await this.apiClient.post<SaveMappingResponse>(url, {
        mapping,
        filename
      });
      
      return response;
    } catch (error) {
      console.error('Error saving mapping to CSV:', error);
      if (error instanceof Error) {
        throw new Error(`Failed to save mapping: ${error.message}`);
      }
      throw new Error('Failed to save mapping');
    }
  }

  /**
   * List saved mapping files
   */
  async listSavedMappingFiles(): Promise<ListFilesResponse> {
    try {
      // Get base URL from the API client
      const baseURL = this.apiClient['apiGateway'] || 'http://localhost:5000';
      const url = `${baseURL}/api/bms/list-saved-files`;
      
      // Use the API client for the request
      const response = await this.apiClient.get<ListFilesResponse>(url);
      
      return response;
    } catch (error) {
      console.error('Error listing saved mapping files:', error);
      if (error instanceof Error) {
        throw new Error(`Failed to list saved mappings: ${error.message}`);
      }
      throw new Error('Failed to list saved mappings');
    }
  }

  /**
   * Load mapping from CSV file
   */
  async loadMappingFromCSV(filepath: string): Promise<LoadCSVResponse> {
    try {
      // Get base URL from the API client
      const baseURL = this.apiClient['apiGateway'] || 'http://localhost:5000';
      const url = `${baseURL}/api/bms/load-csv`;
      
      // Use the API client for the request
      const response = await this.apiClient.post<LoadCSVResponse>(url, {
        filepath
      });
      
      return response;
    } catch (error) {
      console.error('Error loading mapping from CSV:', error);
      if (error instanceof Error) {
        throw new Error(`Failed to load mapping: ${error.message}`);
      }
      throw new Error('Failed to load mapping');
    }
  }

  /**
   * Generate download URL for a file
   */
  getFileDownloadURL(filepath: string): string {
    // Get base URL from the API client
    const baseURL = this.apiClient['apiGateway'] || 'http://localhost:5000';
    return `${baseURL}/api/bms/download-file?filepath=${encodeURIComponent(filepath)}`;
  }

  /**
   * Export mapping to a format compatible with EnOS
   */
  async exportMappingToEnOS(mapping: MappingData[]): Promise<ExportMappingResponse> {
    try {
      // Get base URL from the API client
      const baseURL = this.apiClient['apiGateway'] || 'http://localhost:5000';
      const url = `${baseURL}/api/bms/export-mapping`;
      
      // Use the API client for the request
      const response = await this.apiClient.post<ExportMappingResponse>(url, {
        mapping
      });
      
      return response;
    } catch (error) {
      console.error('Error exporting mapping to EnOS:', error);
      if (error instanceof Error) {
        throw new Error(`Failed to export mapping: ${error.message}`);
      }
      throw new Error('Failed to export mapping');
    }
  }
}

// Helper function to create a new client instance
export function createBMSClient(config: BMSClientConfig): BMSClient {
  return new BMSClient(config);
}

// Default export - singleton instance
export default BMSClient;