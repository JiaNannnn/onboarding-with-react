import { useState } from 'react';
import { BMSPoint, PointGroup } from '../../types/apiTypes';
import { useBMSClient } from '../useBMSClient';

type AIStrategy = 'default' | 'ai' | 'ontology';

interface UseAIGroupingOptions {
  onStartGrouping?: () => void;
  onGroupingSuccess?: (groups: Record<string, PointGroup>) => void;
  onGroupingError?: (error: string) => void;
  onGroupingComplete?: () => void;
}

/**
 * Hook for handling AI-assisted grouping of points
 */
export function useAIGrouping(options: UseAIGroupingOptions = {}) {
  const [aiStrategy, setAiStrategy] = useState<AIStrategy>('default');
  const [isProcessingAI, setIsProcessingAI] = useState<boolean>(false);
  const [aiGroupingError, setAiGroupingError] = useState<string | null>(null);
  const [aiGroupingMethod, setAiGroupingMethod] = useState<string | null>(null);
  
  // Use the BMSClient hook
  const bmsClient = useBMSClient({
    apiGateway: process.env.REACT_APP_API_URL || process.env.REACT_APP_BMS_API_URL || 'http://localhost:5000',
    accessKey: '',
    secretKey: '',
    orgId: '',
    assetId: ''
  });

  // Handle AI-assisted grouping
  const handleAIGrouping = async (points: BMSPoint[]) => {
    // Check if there are points available
    if (points.length === 0) {
      const errorMessage = 'No points available for AI grouping. Please upload points first.';
      setAiGroupingError(errorMessage);
      if (options.onGroupingError) options.onGroupingError(errorMessage);
      return;
    }
    
    // Set processing state
    setIsProcessingAI(true);
    setAiGroupingError(null);
    setAiGroupingMethod(null);
    
    // Notify start of grouping
    if (options.onStartGrouping) options.onStartGrouping();
    
    try {
      console.log(`Starting AI grouping with ${points.length} points...`);
      
      // Call API to group points using the new hook-based approach
      const response = await bmsClient.groupPointsWithAI(points);
      
      console.log('AI grouping response:', response);
      
      if (response.success && response.grouped_points) {
        // Transform the AI grouped points to our format
        const newGroups: Record<string, PointGroup> = {};
        
        Object.entries(response.grouped_points).forEach(([key, value]) => {
          const groupId = `group-${Date.now()}-${key}`;
          newGroups[groupId] = {
            id: groupId,
            name: value.name,
            description: value.description,
            points: value.points,
            subgroups: {} // Initialize empty subgroups
          };
        });
        
        // Log created groups
        console.log(`Created ${Object.keys(newGroups).length} groups from AI grouping`);
        
        // Check if the API used a fallback method
        if (response.method && response.method !== aiStrategy) {
          setAiGroupingError(`AI grouping used fallback ${response.method} method instead.`);
          console.log(`API used fallback method: ${response.method}`);
        }
        
        // Store the method used for display
        if (response.method) {
          setAiGroupingMethod(response.method);
        }
        
        // Call success callback with the new groups
        if (options.onGroupingSuccess) {
          options.onGroupingSuccess(newGroups);
        }
      } else {
        // Handle failed response
        const errorMsg = response.error || 'Failed to group points with AI';
        console.error('AI grouping failed:', errorMsg);
        setAiGroupingError(errorMsg);
        if (options.onGroupingError) options.onGroupingError(errorMsg);
      }
    } catch (err) {
      // Handle exceptions
      const errorMessage = err instanceof Error ? err.message : 'Unknown error during AI grouping';
      console.error('Error in AI grouping:', errorMessage, err);
      const fullErrorMessage = `AI grouping failed: ${errorMessage}. Check that the backend server is running.`;
      setAiGroupingError(fullErrorMessage);
      if (options.onGroupingError) options.onGroupingError(fullErrorMessage);
    } finally {
      setIsProcessingAI(false);
      if (options.onGroupingComplete) options.onGroupingComplete();
    }
  };

  return {
    aiStrategy,
    isProcessingAI,
    aiGroupingError,
    aiGroupingMethod,
    setAiStrategy,
    handleAIGrouping
  };
}