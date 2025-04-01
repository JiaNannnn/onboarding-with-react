import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { PointMapping } from '../types/apiTypes';

/**
 * MappingContext state type definition
 */
interface MappingContextState {
  mappings: PointMapping[];
  selectedMapping: PointMapping | null;
  filename: string;
  loading: boolean;
  error: string | null;
}

/**
 * MappingContext actions type definition
 */
interface MappingContextActions {
  setMappings: (mappings: PointMapping[]) => void;
  addMapping: (mapping: PointMapping) => void;
  removeMapping: (index: number) => void;
  updateMapping: (index: number, mapping: Partial<PointMapping>) => void;
  selectMapping: (mapping: PointMapping | null) => void;
  clearMappings: () => void;
  setFilename: (filename: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

/**
 * Combined MappingContext type
 */
type MappingContextType = MappingContextState & MappingContextActions;

/**
 * Default state for MappingContext
 */
const defaultMappingState: MappingContextState = {
  mappings: [],
  selectedMapping: null,
  filename: 'mapping',
  loading: false,
  error: null,
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
  const [state, setState] = useState<MappingContextState>(defaultMappingState);

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

  // Combine state and actions
  const value: MappingContextType = {
    ...state,
    setMappings,
    addMapping,
    removeMapping,
    updateMapping,
    selectMapping,
    clearMappings,
    setFilename,
    setLoading,
    setError,
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