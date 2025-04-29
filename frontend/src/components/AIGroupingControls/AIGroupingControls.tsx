import React from 'react';
import { Button } from '../../components';
import './AIGroupingControls.css';

type AIStrategy = 'default' | 'ai' | 'ontology';

interface AIGroupingControlsProps {
  aiStrategy: AIStrategy;
  isProcessingAI: boolean;
  aiGroupingError: string | null;
  aiGroupingMethod: string | null;
  pointsCount: number;
  isLoading: boolean;
  hasGroups: boolean;
  onStrategyChange: (strategy: AIStrategy) => void;
  onStartGrouping: () => void;
}

/**
 * Controls for AI-assisted grouping of points
 */
const AIGroupingControls: React.FC<AIGroupingControlsProps> = ({
  aiStrategy,
  isProcessingAI,
  aiGroupingError,
  aiGroupingMethod,
  pointsCount,
  isLoading,
  hasGroups,
  onStrategyChange,
  onStartGrouping
}) => {
  return (
    <div className="ai-grouping-controls">
      <div className="ai-grouping-controls__options">
        <select 
          value={aiStrategy}
          onChange={(e) => onStrategyChange(e.target.value as AIStrategy)}
          className="ai-grouping-controls__strategy-select"
          disabled={isProcessingAI}
        >
          <option value="default">Default Grouping</option>
          <option value="ai">AI-Assisted Grouping</option>
          <option value="ontology">Ontology-Based Grouping</option>
        </select>
        
        <Button
          onClick={onStartGrouping}
          disabled={isProcessingAI || pointsCount === 0 || isLoading}
          className="ai-grouping-controls__start-button"
        >
          {isProcessingAI ? 'Processing...' : aiGroupingError ? 'Retry AI Grouping' : 'Group All Points with AI'}
        </Button>
      </div>
      
      {aiGroupingError && (
        <div className="ai-grouping-controls__error">
          {aiGroupingError}
          {aiGroupingError.includes('fallback') && (
            <span> Your data was still grouped, but using a simpler method.</span>
          )}
        </div>
      )}
      
      {aiStrategy === 'ai' && !aiGroupingError && hasGroups && (
        <div className="ai-grouping-controls__info">
          <span className="ai-grouping-controls__info-icon">ℹ️</span>
          <span>Points grouped using {aiGroupingMethod === 'ai-cached' ? 'cached AI' : 
                aiGroupingMethod === 'default' ? 'pattern-based' : 'AI'} analysis.</span>
          {aiGroupingMethod === 'ai-cached' && (
            <span className="ai-grouping-controls__cache-info"> (Using cached results for faster performance)</span>
          )}
        </div>
      )}
    </div>
  );
};

export default AIGroupingControls;