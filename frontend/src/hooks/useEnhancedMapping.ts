/**
 * Enhanced mapping hook for BMS to EnOS mapping operations
 * 
 * This hook provides specialized functionality for:
 * - Mapping quality assessment
 * - Mapping improvement recommendations
 * - Batch processing optimization
 * - Device type analysis
 */

import { useState, useCallback, useMemo } from 'react';
import { BMSPoint } from '../types/apiTypes';
import { MapPointsToEnOSResponse, MappingConfig } from '../api/bmsClient';
import { analyzeMappingQuality, MappingQualityResult } from './enhancedMapping';
import { useBMSClient } from './useBMSClient';

/**
 * Enhanced mapping state interface
 */
export interface EnhancedMappingState {
  isAnalyzing: boolean;
  isImproving: boolean;
  error: string | null;
  qualityResults: MappingQualityResult | null;
  improvementTaskId: string | null;
  batchProgress: {
    isInBatchMode: boolean;
    totalBatches: number;
    completedBatches: number;
    progress: number;
  };
}

/**
 * Configuration for mapping improvement
 */
export interface MappingImprovementConfig {
  qualityFilter: 'poor' | 'unacceptable' | 'below_fair' | 'all';
  deviceTypes?: string[];
  includeDeviceContext?: boolean;
  includeSuggestions?: boolean;
}

/**
 * Default improvement configuration
 */
const defaultImprovementConfig: MappingImprovementConfig = {
  qualityFilter: 'all',
  includeDeviceContext: true,
  includeSuggestions: true
};

/**
 * Enhanced mapping hook for comprehensive mapping operations
 */
export function useEnhancedMapping() {
  // Get the BMS client hook
  const bmsClient = useBMSClient();
  
  // State for enhanced mapping operations
  const [state, setState] = useState<EnhancedMappingState>({
    isAnalyzing: false,
    isImproving: false,
    error: null,
    qualityResults: null,
    improvementTaskId: null,
    batchProgress: {
      isInBatchMode: false,
      totalBatches: 0,
      completedBatches: 0,
      progress: 0
    }
  });

  /**
   * Reset all state values
   */
  const resetState = useCallback(() => {
    setState({
      isAnalyzing: false,
      isImproving: false,
      error: null,
      qualityResults: null,
      improvementTaskId: null,
      batchProgress: {
        isInBatchMode: false,
        totalBatches: 0,
        completedBatches: 0,
        progress: 0
      }
    });
  }, []);

  /**
   * Update batch progress information
   */
  const updateBatchProgress = useCallback((
    isInBatchMode: boolean,
    totalBatches: number,
    completedBatches: number,
    progress: number
  ) => {
    setState(prevState => ({
      ...prevState,
      batchProgress: {
        isInBatchMode,
        totalBatches,
        completedBatches,
        progress
      }
    }));
  }, []);

  /**
   * Analyze mapping quality
   */
  const analyzeQuality = useCallback((mappings: MapPointsToEnOSResponse): Promise<MappingQualityResult> => {
    setState(prevState => ({ ...prevState, isAnalyzing: true, error: null }));
    
    try {
      // Perform the quality analysis
      const results = analyzeMappingQuality(mappings);
      
      // Update state with results
      setState(prevState => ({ 
        ...prevState, 
        isAnalyzing: false, 
        qualityResults: results 
      }));
      
      return Promise.resolve(results);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error during quality analysis';
      setState(prevState => ({ 
        ...prevState, 
        isAnalyzing: false, 
        error: errorMessage 
      }));
      
      return Promise.reject(error);
    }
  }, []);

  /**
   * Detect device types from a dataset
   */
  const detectDeviceTypes = useCallback((points: BMSPoint[]): string[] => {
    // Find all unique device types
    const deviceTypes = new Set<string>();
    
    points.forEach(point => {
      // Extract from device type field if available
      if (point.deviceType && typeof point.deviceType === 'string') {
        deviceTypes.add(point.deviceType);
      } 
      // Try to extract from point name (e.g., "FCU-B1-46A.RoomTemp")
      else if (point.pointName) {
        const pointNameParts = point.pointName.split(/[-_.]/);
        const deviceType = pointNameParts[0].toUpperCase();
        
        // Only add if it's a common HVAC device type
        const commonTypes = ['FCU', 'AHU', 'CH', 'CHILLER', 'PUMP', 'CT', 'VAV'];
        if (commonTypes.includes(deviceType)) {
          deviceTypes.add(deviceType);
        }
      }
    });
    
    return Array.from(deviceTypes);
  }, []);

  /**
   * Analyze CSV data for device categorization
   */
  const analyzeCSVDeviceTypes = useCallback(async (csvFilePath: string): Promise<string[]> => {
    try {
      return await bmsClient.analyzeCSVDeviceTypes(csvFilePath);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to analyze CSV device types';
      setState(prevState => ({ ...prevState, error: errorMessage }));
      return [];
    }
  }, [bmsClient]);

  /**
   * Group points by device type for batch processing
   */
  const groupPointsByDeviceType = useCallback((points: BMSPoint[]): Record<string, BMSPoint[]> => {
    const deviceGroups: Record<string, BMSPoint[]> = {};
    
    points.forEach(point => {
      // Get device type - either from the field or extract from name
      let deviceType = point.deviceType || 'Unknown';
      
      if (!deviceType || deviceType === 'Unknown') {
        // Try to extract from point name (e.g., "FCU-B1-46A.RoomTemp")
        const pointNameParts = point.pointName.split(/[-_.]/);
        deviceType = pointNameParts[0].toUpperCase();
      }
      
      // Initialize group if it doesn't exist
      if (!deviceGroups[deviceType]) {
        deviceGroups[deviceType] = [];
      }
      
      // Add point to the group
      deviceGroups[deviceType].push(point);
    });
    
    return deviceGroups;
  }, []);

  /**
   * Improve mapping results with a second round of mapping
   */
  const improveMappingResults = useCallback(async (
    originalTaskId: string,
    config: Partial<MappingImprovementConfig> = {}
  ): Promise<MapPointsToEnOSResponse> => {
    // Combine with default config
    const fullConfig: MappingImprovementConfig = {
      ...defaultImprovementConfig,
      ...config
    };
    
    setState(prevState => ({
      ...prevState,
      isImproving: true,
      error: null,
      improvementTaskId: null
    }));
    
    try {
      // Prepare the mapping config for the API
      const mappingConfig: MappingConfig = {
        includeDeviceContext: fullConfig.includeDeviceContext,
        deviceTypes: fullConfig.deviceTypes,
        includeSuggestions: fullConfig.includeSuggestions,
        prioritizeFailedPatterns: true,
        includeReflectionData: true
      };
      
      // Call the BMS client to improve the mapping
      const response = await bmsClient.improveMappingResults(
        originalTaskId,
        fullConfig.qualityFilter,
        mappingConfig
      );
      
      // Update batch progress if in batch mode
      if (response.batchMode && typeof response.totalBatches === 'number') {
        updateBatchProgress(
          true,
          response.totalBatches,
          response.completedBatches || 0,
          response.progress || 0
        );
      } else {
        updateBatchProgress(false, 0, 0, 0);
      }
      
      // Store the task ID for later reference
      setState(prevState => ({
        ...prevState,
        isImproving: false,
        improvementTaskId: response.taskId || null
      }));
      
      return response;
    } catch (error) {
      const errorMessage = error instanceof Error 
        ? error.message 
        : 'Failed to improve mapping results';
        
      setState(prevState => ({
        ...prevState,
        isImproving: false,
        error: errorMessage
      }));
      
      throw error;
    }
  }, [bmsClient, updateBatchProgress]);

  /**
   * Check improvement task status
   */
  const checkImprovementStatus = useCallback(async (
    taskId: string
  ): Promise<MapPointsToEnOSResponse> => {
    try {
      // Call the BMS client to check the status
      const response = await bmsClient.checkPointsMappingStatus(taskId);
      
      // Update batch progress if in batch mode
      if (response.batchMode && typeof response.totalBatches === 'number') {
        updateBatchProgress(
          true,
          response.totalBatches,
          response.completedBatches || 0,
          response.progress || 0
        );
      }
      
      return response;
    } catch (error) {
      const errorMessage = error instanceof Error 
        ? error.message 
        : 'Failed to check improvement status';
        
      setState(prevState => ({
        ...prevState,
        error: errorMessage
      }));
      
      throw error;
    }
  }, [bmsClient, updateBatchProgress]);

  /**
   * Calculate quality statistics from mapping results
   */
  const getQualityStatistics = useMemo(() => {
    if (!state.qualityResults) return null;
    
    const { qualitySummary } = state.qualityResults;
    const total = qualitySummary.excellent + qualitySummary.good + 
                  qualitySummary.fair + qualitySummary.poor + 
                  qualitySummary.unacceptable;
                  
    // Calculate percentages
    return {
      excellent: {
        count: qualitySummary.excellent,
        percentage: total > 0 ? (qualitySummary.excellent / total) * 100 : 0
      },
      good: {
        count: qualitySummary.good,
        percentage: total > 0 ? (qualitySummary.good / total) * 100 : 0
      },
      fair: {
        count: qualitySummary.fair,
        percentage: total > 0 ? (qualitySummary.fair / total) * 100 : 0
      },
      poor: {
        count: qualitySummary.poor,
        percentage: total > 0 ? (qualitySummary.poor / total) * 100 : 0
      },
      unacceptable: {
        count: qualitySummary.unacceptable,
        percentage: total > 0 ? (qualitySummary.unacceptable / total) * 100 : 0
      },
      needsImprovement: {
        count: qualitySummary.poor + qualitySummary.unacceptable,
        percentage: total > 0 ? ((qualitySummary.poor + qualitySummary.unacceptable) / total) * 100 : 0
      },
      total
    };
  }, [state.qualityResults]);

  // Return the hook interface
  return {
    // State
    isAnalyzing: state.isAnalyzing,
    isImproving: state.isImproving,
    error: state.error,
    qualityResults: state.qualityResults,
    improvementTaskId: state.improvementTaskId,
    batchProgress: state.batchProgress,
    qualityStatistics: getQualityStatistics,
    
    // Methods
    analyzeQuality,
    improveMappingResults,
    checkImprovementStatus,
    detectDeviceTypes,
    analyzeCSVDeviceTypes,
    groupPointsByDeviceType,
    resetState,
    updateBatchProgress
  };
}

export default useEnhancedMapping;