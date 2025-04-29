import React, { createContext, useContext, useState, useCallback, ReactNode, useMemo } from 'react';
import { BMSPoint, PointMapping } from '../types/apiTypes';
import { MapPointsToEnOSResponse } from '../api/bmsClient';
import { MappingQualityResult } from '../hooks/enhancedMapping';

/**
 * Batch processing state interface
 */
interface BatchProcessingState {
  isInBatchMode: boolean;
  totalBatches: number;
  completedBatches: number;
  progress: number;
  taskId: string | null;
}

/**
 * Quality assessment state interface
 */
interface QualityAssessmentState {
  isAnalyzed: boolean;
  qualityResults: MappingQualityResult | null;
  improvements: {
    originalTaskId: string | null;
    improvementTaskId: string | null;
    isImproving: boolean;
    improved: boolean;
  };
}

/**
 * Mapping task information interface
 */
interface MappingTask {
  taskId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  timestamp: number;
  results?: MapPointsToEnOSResponse;
}

/**
 * Enhanced MappingContext state type definition
 */
interface MappingContextState {
  // Original fields
  mappings: PointMapping[];
  selectedMapping: PointMapping | null;
  filename: string;
  loading: boolean;
  error: string | null;
  
  // Enhanced fields
  rawPoints: BMSPoint[];
  mappedPoints: any[];  // Using any to support different mapping response formats
  deviceTypes: string[];
  batchProcessing: BatchProcessingState;
  qualityAssessment: QualityAssessmentState;
  tasks: MappingTask[];
  filters: {
    deviceType: string | null;
    qualityLevel: string | null;
    searchTerm: string | null;
  };
}

/**
 * MappingContext actions type definition (enhanced)
 */
interface MappingContextActions {
  // Original actions
  setMappings: (mappings: PointMapping[]) => void;
  addMapping: (mapping: PointMapping) => void;
  removeMapping: (index: number) => void;
  updateMapping: (index: number, mapping: Partial<PointMapping>) => void;
  selectMapping: (mapping: PointMapping | null) => void;
  clearMappings: () => void;
  setFilename: (filename: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Enhanced actions
  setRawPoints: (points: BMSPoint[]) => void;
  setMappedPoints: (points: any[]) => void;
  setDeviceTypes: (types: string[]) => void;
  addMappingTask: (task: MappingTask) => void;
  updateMappingTask: (taskId: string, updates: Partial<MappingTask>) => void;
  clearTasks: () => void;
  
  // Batch processing actions
  updateBatchProgress: (progress: Partial<BatchProcessingState>) => void;
  resetBatchProgress: () => void;
  
  // Quality assessment actions
  setQualityResults: (results: MappingQualityResult | null) => void;
  setImprovementTask: (originalTaskId: string | null, improvementTaskId: string | null) => void;
  setIsImproving: (isImproving: boolean) => void;
  setImproved: (improved: boolean) => void;
  
  // Filter actions
  setFilter: (filterName: 'deviceType' | 'qualityLevel' | 'searchTerm', value: string | null) => void;
  clearFilters: () => void;
}

/**
 * Combined MappingContext type
 */
type MappingContextType = MappingContextState & MappingContextActions & {
  // Computed properties
  filteredMappings: any[];
  hasLowQualityMappings: boolean;
};

/**
 * Default state for MappingContext
 */
const defaultMappingState: MappingContextState = {
  // Original fields
  mappings: [],
  selectedMapping: null,
  filename: 'mapping',
  loading: false,
  error: null,
  
  // Enhanced fields
  rawPoints: [],
  mappedPoints: [],
  deviceTypes: [],
  batchProcessing: {
    isInBatchMode: false,
    totalBatches: 0,
    completedBatches: 0,
    progress: 0,
    taskId: null
  },
  qualityAssessment: {
    isAnalyzed: false,
    qualityResults: null,
    improvements: {
      originalTaskId: null,
      improvementTaskId: null,
      isImproving: false,
      improved: false
    }
  },
  tasks: [],
  filters: {
    deviceType: null,
    qualityLevel: null,
    searchTerm: null
  }
};

/**
 * Create the MappingContext
 */
const MappingContext = createContext<MappingContextType | null>(null);

/**
 * MappingProvider props interface
 */
interface MappingProviderProps {
  children: ReactNode;
}

/**
 * Provider component for MappingContext
 */
export function MappingProvider({ children }: MappingProviderProps): JSX.Element {
  // Main state
  const [state, setState] = useState<MappingContextState>(defaultMappingState);

  /**
   * ORIGINAL ACTIONS
   */

  /**
   * Set all mappings
   */
  const setMappings = useCallback((mappings: PointMapping[]): void => {
    setState((prevState) => ({
      ...prevState,
      mappings,
    }));
  }, []);

  /**
   * Add a new mapping
   */
  const addMapping = useCallback((mapping: PointMapping): void => {
    setState((prevState) => ({
      ...prevState,
      mappings: [...prevState.mappings, mapping],
    }));
  }, []);

  /**
   * Remove a mapping by index
   */
  const removeMapping = useCallback((index: number): void => {
    setState((prevState) => ({
      ...prevState,
      mappings: prevState.mappings.filter((_, i) => i !== index),
    }));
  }, []);

  /**
   * Update an existing mapping
   */
  const updateMapping = useCallback((index: number, mappingUpdates: Partial<PointMapping>): void => {
    setState((prevState) => {
      const mappings = [...prevState.mappings];
      
      if (index >= 0 && index < mappings.length) {
        mappings[index] = {
          ...mappings[index],
          ...mappingUpdates,
        };
      }

      return {
        ...prevState,
        mappings,
      };
    });
  }, []);

  /**
   * Select a mapping for editing
   */
  const selectMapping = useCallback((mapping: PointMapping | null): void => {
    setState((prevState) => ({
      ...prevState,
      selectedMapping: mapping,
    }));
  }, []);

  /**
   * Clear all mappings
   */
  const clearMappings = useCallback((): void => {
    setState((prevState) => ({
      ...prevState,
      mappings: [],
      selectedMapping: null,
    }));
  }, []);

  /**
   * Set the filename for export
   */
  const setFilename = useCallback((filename: string): void => {
    setState((prevState) => ({
      ...prevState,
      filename,
    }));
  }, []);

  /**
   * Set loading state
   */
  const setLoading = useCallback((loading: boolean): void => {
    setState((prevState) => ({
      ...prevState,
      loading,
    }));
  }, []);

  /**
   * Set error state
   */
  const setError = useCallback((error: string | null): void => {
    setState((prevState) => ({
      ...prevState,
      error,
    }));
  }, []);

  /**
   * ENHANCED ACTIONS
   */

  /**
   * Set raw points
   */
  const setRawPoints = useCallback((points: BMSPoint[]): void => {
    setState((prevState) => ({
      ...prevState,
      rawPoints: points,
    }));
  }, []);

  /**
   * Set mapped points
   */
  const setMappedPoints = useCallback((points: any[]): void => {
    setState((prevState) => ({
      ...prevState,
      mappedPoints: points,
    }));
  }, []);

  /**
   * Set device types
   */
  const setDeviceTypes = useCallback((types: string[]): void => {
    setState((prevState) => ({
      ...prevState,
      deviceTypes: types,
    }));
  }, []);

  /**
   * Add a mapping task
   */
  const addMappingTask = useCallback((task: MappingTask): void => {
    setState((prevState) => ({
      ...prevState,
      tasks: [...prevState.tasks, task],
    }));
  }, []);

  /**
   * Update a mapping task
   */
  const updateMappingTask = useCallback((taskId: string, updates: Partial<MappingTask>): void => {
    setState((prevState) => {
      const tasks = [...prevState.tasks];
      const taskIndex = tasks.findIndex(task => task.taskId === taskId);
      
      if (taskIndex >= 0) {
        tasks[taskIndex] = {
          ...tasks[taskIndex],
          ...updates,
        };
      }

      return {
        ...prevState,
        tasks,
      };
    });
  }, []);

  /**
   * Clear all tasks
   */
  const clearTasks = useCallback((): void => {
    setState((prevState) => ({
      ...prevState,
      tasks: [],
    }));
  }, []);

  /**
   * BATCH PROCESSING ACTIONS
   */

  /**
   * Update batch processing progress
   */
  const updateBatchProgress = useCallback((progress: Partial<BatchProcessingState>): void => {
    setState((prevState) => ({
      ...prevState,
      batchProcessing: {
        ...prevState.batchProcessing,
        ...progress,
      },
    }));
  }, []);

  /**
   * Reset batch processing state
   */
  const resetBatchProgress = useCallback((): void => {
    setState((prevState) => ({
      ...prevState,
      batchProcessing: {
        isInBatchMode: false,
        totalBatches: 0,
        completedBatches: 0,
        progress: 0,
        taskId: null
      },
    }));
  }, []);

  /**
   * QUALITY ASSESSMENT ACTIONS
   */

  /**
   * Set quality assessment results
   */
  const setQualityResults = useCallback((results: MappingQualityResult | null): void => {
    setState((prevState) => ({
      ...prevState,
      qualityAssessment: {
        ...prevState.qualityAssessment,
        isAnalyzed: results !== null,
        qualityResults: results,
      },
    }));
  }, []);

  /**
   * Set improvement task IDs
   */
  const setImprovementTask = useCallback((originalTaskId: string | null, improvementTaskId: string | null): void => {
    setState((prevState) => ({
      ...prevState,
      qualityAssessment: {
        ...prevState.qualityAssessment,
        improvements: {
          ...prevState.qualityAssessment.improvements,
          originalTaskId,
          improvementTaskId,
        },
      },
    }));
  }, []);

  /**
   * Set improving state
   */
  const setIsImproving = useCallback((isImproving: boolean): void => {
    setState((prevState) => ({
      ...prevState,
      qualityAssessment: {
        ...prevState.qualityAssessment,
        improvements: {
          ...prevState.qualityAssessment.improvements,
          isImproving,
        },
      },
    }));
  }, []);

  /**
   * Set improved state
   */
  const setImproved = useCallback((improved: boolean): void => {
    setState((prevState) => ({
      ...prevState,
      qualityAssessment: {
        ...prevState.qualityAssessment,
        improvements: {
          ...prevState.qualityAssessment.improvements,
          improved,
        },
      },
    }));
  }, []);

  /**
   * FILTER ACTIONS
   */

  /**
   * Set a filter value
   */
  const setFilter = useCallback((filterName: 'deviceType' | 'qualityLevel' | 'searchTerm', value: string | null): void => {
    setState((prevState) => ({
      ...prevState,
      filters: {
        ...prevState.filters,
        [filterName]: value,
      },
    }));
  }, []);

  /**
   * Clear all filters
   */
  const clearFilters = useCallback((): void => {
    setState((prevState) => ({
      ...prevState,
      filters: {
        deviceType: null,
        qualityLevel: null,
        searchTerm: null,
      },
    }));
  }, []);

  /**
   * COMPUTED PROPERTIES
   */

  /**
   * Filtered mappings based on active filters
   */
  const filteredMappings = useMemo(() => {
    const { deviceType, qualityLevel, searchTerm } = state.filters;
    let filtered = state.mappedPoints;

    // Filter by device type
    if (deviceType) {
      filtered = filtered.filter(mapping => {
        // Support both nested and flat mapping structures
        const mappingDeviceType = mapping.original?.deviceType || mapping.deviceType || '';
        return mappingDeviceType.toLowerCase() === deviceType.toLowerCase();
      });
    }

    // Filter by quality level if quality assessment has been done
    if (qualityLevel && state.qualityAssessment.qualityResults) {
      const poorPoints = state.qualityAssessment.qualityResults.pointsWithPoorQuality.map(p => p.pointId);
      
      if (qualityLevel === 'poor') {
        filtered = filtered.filter(mapping => {
          const pointId = mapping.mapping?.pointId || mapping.pointId || '';
          return poorPoints.includes(pointId);
        });
      } else if (qualityLevel === 'good') {
        filtered = filtered.filter(mapping => {
          const pointId = mapping.mapping?.pointId || mapping.pointId || '';
          return !poorPoints.includes(pointId);
        });
      }
    }

    // Filter by search term
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(mapping => {
        // Support both nested and flat mapping structures
        const pointName = mapping.original?.pointName || mapping.pointName || '';
        const enosPoint = mapping.mapping?.enosPoint || mapping.enosPoint || '';
        return pointName.toLowerCase().includes(searchLower) || 
               enosPoint.toLowerCase().includes(searchLower);
      });
    }

    return filtered;
  }, [state.mappedPoints, state.filters, state.qualityAssessment.qualityResults]);

  /**
   * Has low quality mappings flag
   */
  const hasLowQualityMappings = useMemo(() => {
    if (!state.qualityAssessment.qualityResults) return false;
    
    const { qualitySummary } = state.qualityAssessment.qualityResults;
    return (qualitySummary.poor + qualitySummary.unacceptable) > 0;
  }, [state.qualityAssessment.qualityResults]);

  // Combine state and actions
  const value: MappingContextType = {
    // Original state
    ...state,
    
    // Original actions
    setMappings,
    addMapping,
    removeMapping,
    updateMapping,
    selectMapping,
    clearMappings,
    setFilename,
    setLoading,
    setError,
    
    // Enhanced actions
    setRawPoints,
    setMappedPoints,
    setDeviceTypes,
    addMappingTask,
    updateMappingTask,
    clearTasks,
    
    // Batch processing actions
    updateBatchProgress,
    resetBatchProgress,
    
    // Quality assessment actions
    setQualityResults,
    setImprovementTask,
    setIsImproving,
    setImproved,
    
    // Filter actions
    setFilter,
    clearFilters,
    
    // Computed properties
    filteredMappings,
    hasLowQualityMappings
  };

  return <MappingContext.Provider value={value}>{children}</MappingContext.Provider>;
}

/**
 * Hook for using the MappingContext
 */
export function useMappingContext(): MappingContextType {
  const context = useContext(MappingContext);

  if (!context) {
    throw new Error('useMappingContext must be used within a MappingProvider');
  }

  return context;
}

export default MappingContext; 