/**
 * Custom hook for BMS client operations
 * 
 * This hook provides a unified interface for all BMS-related operations:
 * - Network configuration
 * - Device discovery
 * - Points search and retrieval
 * - Grouping and mapping points
 * - File operations (saving, loading, exporting)
 */

import { useState, useCallback, useMemo } from 'react';
import { 
  createBMSClient,
  BMSClientConfig, 
  NetworkInterface,
  PointMapping,
  MappingConfig,
  MappingData,
  GroupPointsWithAIResponse,
  MapPointsToEnOSResponse,
  SaveMappingResponse,
  ListFilesResponse,
  LoadCSVResponse,
  ExportMappingResponse
} from '../api/bmsClient';
import { BMSPoint } from '../types/apiTypes';
// Import the enhanced mapping implementation
// import { enhancedMapPointsToEnOS } from './enhancedMapping';

/**
 * BMS client state interface
 */
export interface BMSClientState {
  loading: boolean;
  error: string | null;
}

/**
 * Default configuration for the BMS client
 */
const defaultConfig: BMSClientConfig = {
  apiGateway: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  accessKey: '',
  secretKey: '',
};

/**
 * Custom hook for BMS client operations
 */
export function useBMSClient(config: BMSClientConfig = defaultConfig) {
  // State to track loading and error states
  const [state, setState] = useState<BMSClientState>({
    loading: false,
    error: null,
  });

  // Create memoized BMS client instance
  const client = useMemo(() => createBMSClient(config), [config]);

  /**
   * General state management for async operations
   */
  const withStateHandling = useCallback(async <T>(
    operation: () => Promise<T>,
    operationName: string
  ): Promise<T> => {
    setState({ loading: true, error: null });
    try {
      const result = await operation();
      setState({ loading: false, error: null });
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : `Error during ${operationName}`;
      console.error(`${operationName} failed:`, error);
      setState({ loading: false, error: errorMessage });
      throw error;
    }
  }, []);

  /**
   * Get network configuration
   */
  const getNetworkConfig = useCallback((): Promise<NetworkInterface[]> => {
    return withStateHandling(
      () => client.getNetworkConfig(),
      'network configuration retrieval'
    );
  }, [client, withStateHandling]);

  /**
   * Fetch devices
   */
  const fetchDevices = useCallback((): Promise<any> => {
    return withStateHandling(
      () => client.fetchDevices(),
      'devices retrieval'
    );
  }, [client, withStateHandling]);

  /**
   * Fetch points from a device
   */
  const fetchPoints = useCallback((
    deviceInstance: string | number,
    deviceAddress: string,
    page: number = 0,
    pageSize: number = 100,
    onProgress?: (current: number, total: number, points: BMSPoint[]) => void
  ): Promise<BMSPoint[]> => {
    return withStateHandling(
      () => client.fetchPoints(deviceInstance, deviceAddress, page, pageSize, onProgress),
      'points retrieval'
    );
  }, [client, withStateHandling]);

  /**
   * Group points using AI
   */
  const groupPointsWithAI = useCallback((
    points: BMSPoint[]
  ): Promise<GroupPointsWithAIResponse> => {
    return withStateHandling(
      () => client.groupPointsWithAI(points),
      'AI grouping'
    );
  }, [client, withStateHandling]);

  /**
   * Map points to EnOS schema using the backend API
   */
  const mapPointsToEnOS = useCallback((
    points: BMSPoint[],
    mappingConfig: MappingConfig = {}
  ): Promise<MapPointsToEnOSResponse> => {
    // Start a mapping task and poll for results
    return withStateHandling(
      async () => {
        try {
          console.log("Starting mapping task with points:", points.length);
          // Call the client method that now handles polling
          const response = await client.mapPointsToEnOS(points, mappingConfig);
          
          // Transform result if needed for backward compatibility
          if (response.success && response.mappings) {
            // If mappings have nested structure, flatten them for compatibility
            const transformedMappings = response.mappings.map(mapping => {
              // Handle the new nested format
              if (mapping.original && mapping.mapping) {
                return {
                  pointId: mapping.mapping.pointId,
                  pointName: mapping.original.pointName,
                  pointType: mapping.original.pointType,
                  enosPoint: mapping.mapping.enosPoint || '',
                  status: mapping.mapping.status,
                  deviceType: mapping.original.deviceType,
                  deviceId: mapping.original.deviceId,
                  unit: mapping.original.unit,
                  error: mapping.mapping.error,
                  mappingSource: 'ai-backend'
                };
              }
              // Return as-is if already in flat format
              return mapping;
            });
            
            return {
              ...response,
              mappings: transformedMappings
            };
          }
          
          return response;
        } catch (error) {
          console.error("Error in mapping task:", error);
          throw error;
        }
      },
      'mapping points to EnOS'
    );
  }, [client, withStateHandling]);
  
  /**
   * Improve mapping results with a second round of AI mapping
   * This targets mappings with poor quality scores for enhancement
   * and groups requests by device type for better batch processing
   */
  const improveMappingResults = useCallback((
    originalTaskId: string,
    qualityFilter: 'poor' | 'unacceptable' | 'below_fair' | 'all' = 'below_fair',
    mappingConfig: MappingConfig = {}
  ): Promise<MapPointsToEnOSResponse> => {
    return withStateHandling(
      async () => {
        try {
          console.log(`Starting mapping improvement task for task ID: ${originalTaskId}`);
          
          // 1. First, get the original mapping data to analyze device types
          const originalMapping = await client.checkPointsMappingStatus(originalTaskId);
          
          if (!originalMapping.success) {
            console.error("Failed to retrieve original mapping data");
            return {
              success: false,
              error: "Failed to retrieve original mapping data",
              stats: { total: 0, mapped: 0, errors: 1 }
            };
          }
          
          // 2. Extract all actual device types and IDs from the data
          const deviceTypes = new Set<string>();
          const deviceIds = new Map<string, Set<string>>(); // deviceType -> Set of deviceIds
          
          if (originalMapping.mappings && originalMapping.mappings.length > 0) {
            console.log(`Analyzing ${originalMapping.mappings.length} mappings for device types...`);
            
            originalMapping.mappings.forEach(mapping => {
              // Handle both nested and flat structures
              const deviceType = (mapping.original?.deviceType || mapping.deviceType || "").toString();
              const deviceId = (mapping.original?.deviceId || mapping.deviceId || "").toString();
              
              if (deviceType && deviceType !== "undefined" && deviceType !== "null") {
                // Add to device types set
                deviceTypes.add(deviceType);
                
                // Group device IDs by device type
                if (!deviceIds.has(deviceType)) {
                  deviceIds.set(deviceType, new Set());
                }
                
                if (deviceId && deviceId !== "undefined" && deviceId !== "null") {
                  deviceIds.get(deviceType)?.add(deviceId);
                }
              }
            });
            
            // 3. Log found device types and IDs
            console.log(`Found ${deviceTypes.size} device types in mapping data:`);
            deviceTypes.forEach(type => {
              const ids = deviceIds.get(type) || new Set();
              console.log(`- ${type}: ${ids.size} unique devices`);
            });
          } else {
            console.warn("No mappings found in the original task data");
          }
          
          // 4. Prepare enhanced mapping config with device information
          const enhancedConfig = {
            ...mappingConfig,
            // Include device types from the data
            deviceTypes: Array.from(deviceTypes),
            // Enable device context and grouping
            includeDeviceContext: true,
            groupByDevice: true,
            prioritizeFailedPatterns: true,
            includeReflectionData: true
          };
          
          console.log(`Requesting improvement with ${deviceTypes.size} device types`);
          
          // 5. Call the client method with enhanced config
          let responseData = await client.improveMappingResults(
            originalTaskId,
            qualityFilter,
            enhancedConfig
          );
          
          // Check for empty batch response (processing with no batches)
          if (responseData.success && responseData.status === 'processing') {
            if (responseData.totalBatches === 0) {
              console.log('Received 0 batches response. This may indicate no devices matched the criteria.');
            }
            
            if (!responseData.mappings || responseData.mappings.length === 0) {
              console.log('Received processing response with no mappings, waiting for results...');
              
              // Poll for results since the task is still processing
              let pollAttempts = 0;
              const maxPollAttempts = 30; // 5 minutes with 10-second interval
              
              while (pollAttempts < maxPollAttempts) {
                await new Promise(resolve => setTimeout(resolve, 10000)); // 10 second delay
                
                console.log(`Polling for mapping results, attempt ${pollAttempts + 1}`);
                const pollResponse = await client.checkPointsMappingStatus(responseData.taskId || '');
                
                // Check if we have results or if batches have been created
                if (pollResponse.status !== 'processing' || 
                    (pollResponse.mappings && pollResponse.mappings.length > 0) ||
                    (pollResponse.totalBatches && pollResponse.totalBatches > 0)) {
                  
                  if (pollResponse.totalBatches && pollResponse.totalBatches > 0) {
                    console.log(`Server now processing ${pollResponse.totalBatches} batches`);
                  }
                  
                  responseData = pollResponse;
                  if (pollResponse.mappings && pollResponse.mappings.length > 0) {
                    console.log(`Received ${pollResponse.mappings.length} mappings, polling complete`);
                    break;
                  }
                }
                
                // Log batch progress if available
                if (pollResponse.batchMode && pollResponse.totalBatches && pollResponse.totalBatches > 0) {
                  console.log(`Processing ${pollResponse.completedBatches || 0} of ${pollResponse.totalBatches} batches (${Math.round((pollResponse.progress || 0) * 100)}%)`);
                }
                
                pollAttempts++;
              }
              
              // If we still have no mappings after polling, return a meaningful error
              if (responseData.status === 'processing' && 
                  (!responseData.mappings || responseData.mappings.length === 0)) {
                
                // If batches were created but not completed
                if (responseData.totalBatches && responseData.totalBatches > 0) {
                  return {
                    success: false,
                    error: `Task is still processing ${responseData.totalBatches} batches. Please check back later for results.`,
                    stats: { total: 0, mapped: 0, errors: 1 },
                    taskId: responseData.taskId // Return taskId for later checking
                  };
                }
                
                // If no batches were created
                return {
                  success: false,
                  error: 'No device batches were created. This may be because no mappings match the quality filter criteria.',
                  stats: { total: 0, mapped: 0, errors: 1 }
                };
              }
            }
          }
          
          // Transform result if needed for backward compatibility
          if (responseData.success && responseData.mappings) {
            // If mappings have nested structure, flatten them for compatibility
            const transformedMappings = responseData.mappings.map(mapping => {
              // Handle the new nested format
              if (mapping.original && mapping.mapping) {
                return {
                  pointId: mapping.mapping.pointId,
                  pointName: mapping.original.pointName,
                  pointType: mapping.original.pointType,
                  enosPoint: mapping.mapping.enosPoint || '',
                  status: mapping.mapping.status,
                  deviceType: mapping.original.deviceType,
                  deviceId: mapping.original.deviceId,
                  unit: mapping.original.unit,
                  error: mapping.mapping.error,
                  mappingSource: 'ai-backend-improved'
                };
              }
              // Return as-is if already in flat format
              return mapping;
            });
            
            return {
              ...responseData,
              mappings: transformedMappings
            };
          }
          
          return responseData;
        } catch (error) {
          console.error("Error in mapping improvement task:", error);
          throw error;
        }
      },
      'improving mapping results'
    );
  }, [client, withStateHandling]);
  
  /**
   * Analyze CSV file for device types and IDs
   * Useful for understanding what device types are in your data
   */
  const analyzeCSVDeviceTypes = useCallback(async (
    csvFilePath: string
  ): Promise<string[]> => {
    return withStateHandling(
      async () => {
        const csvData = await client.loadMappingFromCSV(csvFilePath);
        
        if (!csvData.success || !csvData.data) {
          console.error("Failed to load CSV data");
          return [];
        }
        
        const deviceTypes = new Set<string>();
        const deviceCount = new Map<string, number>();
        
        // Analyze CSV data for device types
        csvData.data.forEach((row: any) => {
          const deviceType = (row.deviceType || row.device_type || "").toString();
          
          if (deviceType && deviceType !== "undefined" && deviceType !== "null") {
            deviceTypes.add(deviceType);
            
            // Count each device type
            deviceCount.set(deviceType, (deviceCount.get(deviceType) || 0) + 1);
          }
        });
        
        console.log("CSV Device Type Analysis:");
        deviceCount.forEach((count, type) => {
          console.log(`- ${type}: ${count} points`);
        });
        
        return Array.from(deviceTypes);
      },
      'analyzing CSV device types'
    );
  }, [client, withStateHandling]);

  /**
   * Save mapping to CSV
   */
  const saveMappingToCSV = useCallback((
    mapping: MappingData[],
    filename?: string
  ): Promise<SaveMappingResponse> => {
    return withStateHandling(
      () => client.saveMappingToCSV(mapping, filename),
      'save mapping'
    );
  }, [client, withStateHandling]);

  /**
   * List saved mapping files
   */
  const listSavedMappingFiles = useCallback((): Promise<ListFilesResponse> => {
    return withStateHandling(
      () => client.listSavedMappingFiles(),
      'list saved files'
    );
  }, [client, withStateHandling]);

  /**
   * Load mapping from CSV
   */
  const loadMappingFromCSV = useCallback((
    filepath: string
  ): Promise<LoadCSVResponse> => {
    return withStateHandling(
      () => client.loadMappingFromCSV(filepath),
      'load mapping'
    );
  }, [client, withStateHandling]);

  /**
   * Get file download URL
   */
  const getFileDownloadURL = useCallback((
    filepath: string
  ): string => {
    return client.getFileDownloadURL(filepath);
  }, [client]);

  /**
   * Export mapping to EnOS
   */
  const exportMappingToEnOS = useCallback((
    mapping: MappingData[]
  ): Promise<ExportMappingResponse> => {
    return withStateHandling(
      () => client.exportMappingToEnOS(mapping),
      'export mapping'
    );
  }, [client, withStateHandling]);

  /**
   * Map points using BMS client
   */
  const mapPoints = useCallback((
    points: PointMapping[],
    useAi: boolean = true
  ): Promise<any> => {
    return withStateHandling(
      () => client.mapPoints(points, useAi),
      'map points'
    );
  }, [client, withStateHandling]);

  /**
   * Group points using BMS client
   */
  const groupPoints = useCallback((
    points: string[],
    useAi: boolean = true
  ): Promise<any> => {
    return withStateHandling(
      () => client.groupPoints(points, useAi),
      'group points'
    );
  }, [client, withStateHandling]);

  /**
   * Update client configuration
   */
  const updateConfig = useCallback((newConfig: Partial<BMSClientConfig>): void => {
    client.updateConfig(newConfig);
  }, [client]);

  return {
    state,
    client, // Expose the client directly for advanced use cases
    // Network and device operations
    getNetworkConfig,
    fetchDevices,
    fetchPoints,
    // Grouping and mapping
    groupPointsWithAI,
    mapPointsToEnOS,
    improveMappingResults,
    groupPoints,
    mapPoints,
    // File operations
    saveMappingToCSV,
    listSavedMappingFiles,
    loadMappingFromCSV,
    getFileDownloadURL,
    exportMappingToEnOS,
    // Analysis
    analyzeCSVDeviceTypes,
    // Config management
    updateConfig,
    // Status checking
    checkPointsMappingStatus: client.checkPointsMappingStatus.bind(client),
  };
}

export default useBMSClient;