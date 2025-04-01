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
    // Restore the API call using the client instance
    return withStateHandling(
      () => client.mapPointsToEnOS(points, mappingConfig),
      'mapping points to EnOS'
    );
    
    /*
    // Previous local mapping logic (now commented out)
    console.log("Using guaranteed local mapping to avoid backend issues");
    
    // Create a success response with locally mapped points
    const mappedPoints = points.map(point => {
      // Extract device type from point name (e.g., "FCU" from "FCU-B1-46A.RoomTemp")
      const pointNameParts = point.pointName.split(/[-_.]/);
      const deviceType = pointNameParts[0].toUpperCase();
      let deviceId = '';
      
      // Try to extract device ID (e.g., "B1-46A" from "FCU-B1-46A.RoomTemp")
      if (pointNameParts.length > 1) {
        deviceId = pointNameParts[1];
        if (pointNameParts.length > 2 && !pointNameParts[1].match(/^\d+$/)) {
          deviceId += '-' + pointNameParts[2];
        }
      }
      
      // Determine point category based on point name/type
      const pointNameLower = point.pointName.toLowerCase();
      let pointCategory = 'generic';
      let confidence = 0.75;
      let enosPath = '';
      
      // Specialized mapping logic based on device type and point name
      // ... (local mapping rules omitted for brevity) ...

      return {
        pointId: point.id,
        pointName: point.pointName,
        pointType: point.pointType,
        enosPath: enosPath,
        confidence: confidence,
        status: 'mapped' as 'mapped',
        deviceType: deviceType,
        deviceId: deviceId,
        unit: point.unit,
        pointCategory: pointCategory,
        mappingSource: 'local-fallback'
      };
    });

    return Promise.resolve({
      success: true,
      mappings: mappedPoints,
      stats: {
        total: points.length,
        mapped: mappedPoints.length,
        errors: 0
      }
    });
    */
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
    groupPoints,
    mapPoints,
    // File operations
    saveMappingToCSV,
    listSavedMappingFiles,
    loadMappingFromCSV,
    getFileDownloadURL,
    exportMappingToEnOS,
    // Config management
    updateConfig,
  };
}

export default useBMSClient;