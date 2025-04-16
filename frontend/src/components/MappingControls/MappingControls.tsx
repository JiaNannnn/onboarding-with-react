import React, { useState } from 'react';
import BatchProgressIndicator from '../BatchProgressIndicator';
import MappingQualityIndicator from '../MappingQualityIndicator';
import './MappingControls.css';

/**
 * Props for the MappingControls component
 */
export interface MappingControlsProps {
  // Main actions
  onMapPoints: () => void;
  onImproveMapping: () => void;
  onExportMapping: () => void;
  onExportToEnOS?: () => void;
  
  // State indicators
  isLoading: boolean;
  isMapping: boolean;
  isImproving: boolean;
  isExporting: boolean;
  
  // Batch processing state
  batchProgress: {
    isInBatchMode: boolean;
    totalBatches: number;
    completedBatches: number;
    progress: number;
    taskId: string | null;
  };
  
  // Quality assessment
  hasQualityAnalysis: boolean;
  hasLowQualityMappings: boolean;
  qualityStats?: {
    excellent: { count: number; percentage: number };
    good: { count: number; percentage: number };
    fair: { count: number; percentage: number };
    poor: { count: number; percentage: number };
    unacceptable: { count: number; percentage: number };
    needsImprovement: { count: number; percentage: number };
    total: number;
  } | null;
  
  // Filtering and control options
  deviceTypes: string[];
  onFilterByDeviceType?: (deviceType: string | null) => void;
  activeDeviceTypeFilter: string | null;
  
  // Point counts
  pointsCount?: number;
  mappedPointsCount?: number;
  
  // Customization
  showQualityDetails?: boolean;
  showBatchDetails?: boolean;
  buttonSize?: 'small' | 'medium' | 'large';
  customClass?: string;
}

/**
 * Component for controlling mapping operations and displaying progress/quality
 */
const MappingControls: React.FC<MappingControlsProps> = ({
  // Main actions
  onMapPoints,
  onImproveMapping,
  onExportMapping,
  onExportToEnOS,
  
  // State indicators
  isLoading,
  isMapping,
  isImproving,
  isExporting,
  
  // Batch processing state
  batchProgress,
  
  // Quality assessment
  hasQualityAnalysis,
  hasLowQualityMappings,
  qualityStats,
  
  // Filtering and control options
  deviceTypes,
  onFilterByDeviceType,
  activeDeviceTypeFilter,
  
  // Customization
  showQualityDetails = true,
  showBatchDetails = true,
  buttonSize = 'medium',
  customClass = '',
  
  // Point counts
  pointsCount,
  mappedPointsCount
}) => {
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  
  const buttonSizeClass = `button-${buttonSize}`;
  
  const isProcessing = isMapping || isImproving || isExporting;
  
  return (
    <div className={`mapping-controls ${customClass}`}>
      <div className="mapping-actions">
        <div className="primary-actions">
          <button
            className={`mapping-button map-button ${buttonSizeClass}`}
            onClick={onMapPoints}
            disabled={isLoading || isProcessing}
          >
            {isMapping ? 'Mapping...' : 'Map to EnOS'}
          </button>
          
          {hasQualityAnalysis && (
            <button
              className={`mapping-button improve-button ${buttonSizeClass}`}
              onClick={onImproveMapping}
              disabled={isLoading || isProcessing || !hasQualityAnalysis}
            >
              {isImproving ? 'Improving...' : 'Improve All Mappings'}
            </button>
          )}
          
          <button
            className={`mapping-button export-button ${buttonSizeClass}`}
            onClick={onExportMapping}
            disabled={isLoading || isProcessing}
          >
            {isExporting ? 'Exporting...' : 'Export Mappings'}
          </button>
          
          {onExportToEnOS && (
            <button
              className={`mapping-button export-to-enos-button ${buttonSizeClass}`}
              onClick={onExportToEnOS}
              disabled={isLoading || isProcessing}
            >
              Export to EnOS
            </button>
          )}
        </div>
        
        <div className="advanced-options-toggle">
          <button
            className="toggle-button"
            onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
          >
            {showAdvancedOptions ? 'Hide Options' : 'Show Options'}
          </button>
        </div>
      </div>
      
      {showAdvancedOptions && (
        <div className="advanced-options">
          {deviceTypes.length > 0 && onFilterByDeviceType && (
            <div className="device-type-filter">
              <label>Filter by Device Type:</label>
              <select
                value={activeDeviceTypeFilter || ''}
                onChange={(e) => onFilterByDeviceType(e.target.value || null)}
                disabled={isProcessing}
              >
                <option value="">All Device Types</option>
                {deviceTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      )}
      
      {/* Progress and quality indicators */}
      <div className="mapping-indicators">
        {/* Batch processing progress */}
        {batchProgress.isInBatchMode && batchProgress.totalBatches > 0 && (
          <div className="batch-indicator">
            <BatchProgressIndicator
              isInBatchMode={batchProgress.isInBatchMode}
              totalBatches={batchProgress.totalBatches}
              completedBatches={batchProgress.completedBatches}
              progress={batchProgress.progress}
              taskId={batchProgress.taskId}
              showDetails={showBatchDetails}
              size={buttonSize}
            />
          </div>
        )}
        
        {/* Quality indicators */}
        {hasQualityAnalysis && qualityStats && showQualityDetails && (
          <div className="quality-indicators">
            <div className="quality-summary">
              <h4>Mapping Quality</h4>
              <div className="quality-indicators-grid">
                <div className="quality-indicator-item">
                  <MappingQualityIndicator
                    qualityLevel="excellent"
                    percentage={qualityStats.excellent.percentage}
                    count={qualityStats.excellent.count}
                    total={qualityStats.total}
                    size={buttonSize}
                    showDetails={true}
                  />
                </div>
                <div className="quality-indicator-item">
                  <MappingQualityIndicator
                    qualityLevel="good"
                    percentage={qualityStats.good.percentage}
                    count={qualityStats.good.count}
                    total={qualityStats.total}
                    size={buttonSize}
                    showDetails={true}
                  />
                </div>
                <div className="quality-indicator-item">
                  <MappingQualityIndicator
                    qualityLevel="fair"
                    percentage={qualityStats.fair.percentage}
                    count={qualityStats.fair.count}
                    total={qualityStats.total}
                    size={buttonSize}
                    showDetails={true}
                  />
                </div>
                <div className="quality-indicator-item">
                  <MappingQualityIndicator
                    qualityLevel="poor"
                    percentage={qualityStats.poor.percentage}
                    count={qualityStats.poor.count}
                    total={qualityStats.total}
                    size={buttonSize}
                    showDetails={true}
                  />
                </div>
                <div className="quality-indicator-item">
                  <MappingQualityIndicator
                    qualityLevel="unacceptable"
                    percentage={qualityStats.unacceptable.percentage}
                    count={qualityStats.unacceptable.count}
                    total={qualityStats.total}
                    size={buttonSize}
                    showDetails={true}
                  />
                </div>
              </div>
              
              {hasLowQualityMappings && (
                <div className="quality-improvement-message">
                  <p>
                    <strong>{qualityStats.needsImprovement.count}</strong> points ({qualityStats.needsImprovement.percentage.toFixed(1)}%) 
                    could be improved. Click "Improve Mappings" to enhance them.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MappingControls;