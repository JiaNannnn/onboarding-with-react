import React, { createContext, useContext, useState, useCallback } from 'react';
import { Point } from './PointsContext';

// Define types for the context
export interface EnOSPoint {
  id: string;
  name: string;
  description?: string;
  pointType?: string;
  unit?: string;
  modelId?: string;
  assetId?: string;
  [key: string]: any;
}

export interface PointMapping {
  bmsPointId: string;
  enosPointId: string;
  confidence: number;
  mappingType: 'auto' | 'suggested' | 'manual' | 'unmapped';
  transformRule?: string;
}

export interface MappingContextType {
  bmsMappings: Record<string, PointMapping>;
  setBmsMappings: (mappings: Record<string, PointMapping>) => void;
  enosPoints: EnOSPoint[];
  setEnosPoints: (points: EnOSPoint[]) => void;
  loadedModels: string[];
  setLoadedModels: (models: string[]) => void;
  selectedModelId: string | null;
  setSelectedModelId: (modelId: string | null) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
  generateMappings: (bmsPoints: Point[]) => Promise<void>;
  updateMapping: (mapping: PointMapping) => void;
  removeMapping: (bmsPointId: string) => void;
  loadEnOSPoints: (modelId: string) => Promise<boolean>;
  saveMapping: (name: string) => Promise<boolean>;
  loadSavedMapping: (mappingId: string) => Promise<boolean>;
}

// Create the context
const MappingContext = createContext<MappingContextType | null>(null);

// Custom hook for using this context
export const useMappingContext = () => {
  const context = useContext(MappingContext);
  if (!context) {
    throw new Error('useMappingContext must be used within a MappingProvider');
  }
  return context;
};

// Provider component
export const MappingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [bmsMappings, setBmsMappings] = useState<Record<string, PointMapping>>({});
  const [enosPoints, setEnosPoints] = useState<EnOSPoint[]>([]);
  const [loadedModels, setLoadedModels] = useState<string[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Generate mappings between BMS points and EnOS points
  const generateMappings = useCallback(
    async (bmsPoints: Point[]) => {
      setLoading(true);
      setError(null);

      try {
        if (!selectedModelId) {
          throw new Error('No EnOS model selected');
        }

        // This would be replaced with an actual API call
        // Simulate an API call to generate mappings
        const response = await fetch('/api/v1/bms/generate-mappings', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            bmsPoints: bmsPoints,
            modelId: selectedModelId,
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to generate mappings: ${response.statusText}`);
        }

        const data = await response.json();

        if (!data.success) {
          throw new Error(data.error || 'Failed to generate mappings');
        }

        // Convert the API response to our mapping format
        const newMappings: Record<string, PointMapping> = {};

        data.mappings.forEach((mapping: any) => {
          newMappings[mapping.bmsPointId] = {
            bmsPointId: mapping.bmsPointId,
            enosPointId: mapping.enosPointId,
            confidence: mapping.confidence || 0,
            mappingType: mapping.mappingType || 'suggested',
            transformRule: mapping.transformRule,
          };
        });

        setBmsMappings(newMappings);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
        console.error('Error generating mappings:', err);
      } finally {
        setLoading(false);
      }
    },
    [selectedModelId]
  );

  // Update a specific mapping
  const updateMapping = useCallback((mapping: PointMapping) => {
    setBmsMappings((prevMappings) => ({
      ...prevMappings,
      [mapping.bmsPointId]: mapping,
    }));
  }, []);

  // Remove a mapping
  const removeMapping = useCallback((bmsPointId: string) => {
    setBmsMappings((prevMappings) => {
      const newMappings = { ...prevMappings };
      delete newMappings[bmsPointId];
      return newMappings;
    });
  }, []);

  // Load EnOS points for a specific model
  const loadEnOSPoints = useCallback(async (modelId: string) => {
    setLoading(true);
    setError(null);

    try {
      // This would be replaced with an actual API call
      // Simulate an API call to load EnOS points
      const response = await fetch(`/api/v1/enos/model-points?modelId=${modelId}`);

      if (!response.ok) {
        throw new Error(`Failed to load EnOS points: ${response.statusText}`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to load EnOS points');
      }

      setEnosPoints(data.points);

      // Add model to loaded models if not already loaded
      setLoadedModels((prevModels) =>
        prevModels.includes(modelId) ? prevModels : [...prevModels, modelId]
      );

      setSelectedModelId(modelId);

      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      console.error('Error loading EnOS points:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  // Save mapping configuration
  const saveMapping = useCallback(
    async (name: string) => {
      setLoading(true);
      setError(null);

      try {
        if (!selectedModelId) {
          throw new Error('No EnOS model selected');
        }

        if (Object.keys(bmsMappings).length === 0) {
          throw new Error('No mappings to save');
        }

        // This would be replaced with an actual API call
        // Simulate an API call to save mappings
        const response = await fetch('/api/v1/bms/save-mapping', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name,
            modelId: selectedModelId,
            mappings: Object.values(bmsMappings),
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to save mapping: ${response.statusText}`);
        }

        const data = await response.json();

        if (!data.success) {
          throw new Error(data.error || 'Failed to save mapping');
        }

        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
        console.error('Error saving mapping:', err);
        return false;
      } finally {
        setLoading(false);
      }
    },
    [selectedModelId, bmsMappings]
  );

  // Load a saved mapping
  const loadSavedMapping = useCallback(
    async (mappingId: string) => {
      setLoading(true);
      setError(null);

      try {
        // This would be replaced with an actual API call
        // Simulate an API call to load a saved mapping
        const response = await fetch(`/api/v1/bms/load-mapping?id=${mappingId}`);

        if (!response.ok) {
          throw new Error(`Failed to load mapping: ${response.statusText}`);
        }

        const data = await response.json();

        if (!data.success) {
          throw new Error(data.error || 'Failed to load mapping');
        }

        // First load the model points if not already loaded
        if (!loadedModels.includes(data.modelId)) {
          await loadEnOSPoints(data.modelId);
        } else {
          setSelectedModelId(data.modelId);
        }

        // Convert the API response to our mapping format
        const newMappings: Record<string, PointMapping> = {};

        data.mappings.forEach((mapping: any) => {
          newMappings[mapping.bmsPointId] = {
            bmsPointId: mapping.bmsPointId,
            enosPointId: mapping.enosPointId,
            confidence: mapping.confidence || 0,
            mappingType: mapping.mappingType || 'manual',
            transformRule: mapping.transformRule,
          };
        });

        setBmsMappings(newMappings);

        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
        console.error('Error loading saved mapping:', err);
        return false;
      } finally {
        setLoading(false);
      }
    },
    [loadedModels, loadEnOSPoints]
  );

  // Context value
  const value: MappingContextType = {
    bmsMappings,
    setBmsMappings,
    enosPoints,
    setEnosPoints,
    loadedModels,
    setLoadedModels,
    selectedModelId,
    setSelectedModelId,
    loading,
    setLoading,
    error,
    setError,
    generateMappings,
    updateMapping,
    removeMapping,
    loadEnOSPoints,
    saveMapping,
    loadSavedMapping,
  };

  return <MappingContext.Provider value={value}>{children}</MappingContext.Provider>;
};

export default MappingContext;
