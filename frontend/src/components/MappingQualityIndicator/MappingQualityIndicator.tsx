import React from 'react';
import './MappingQualityIndicator.css';

/**
 * Quality level type
 */
export type QualityLevel = 'excellent' | 'good' | 'fair' | 'poor' | 'unacceptable';

/**
 * Props for quality indicator
 */
interface MappingQualityIndicatorProps {
  qualityLevel: QualityLevel;
  percentage?: number;
  count?: number;
  total?: number;
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
  showDetails?: boolean;
}

/**
 * Mapping quality indicator component for displaying mapping quality visually
 */
const MappingQualityIndicator: React.FC<MappingQualityIndicatorProps> = ({
  qualityLevel,
  percentage,
  count,
  total,
  size = 'medium',
  showLabel = true,
  showDetails = false
}) => {
  // Get text and color for quality level
  const getQualityInfo = (level: QualityLevel) => {
    switch (level) {
      case 'excellent':
        return { text: 'Excellent', color: '#4CAF50', icon: '✓✓' };
      case 'good':
        return { text: 'Good', color: '#8BC34A', icon: '✓' };
      case 'fair':
        return { text: 'Fair', color: '#FFC107', icon: '⚠' };
      case 'poor':
        return { text: 'Poor', color: '#FF9800', icon: '⚠⚠' };
      case 'unacceptable':
        return { text: 'Unacceptable', color: '#F44336', icon: '✗' };
      default:
        return { text: 'Unknown', color: '#9E9E9E', icon: '?' };
    }
  };

  const { text, color, icon } = getQualityInfo(qualityLevel);

  // Calculate size class
  const sizeClass = `quality-indicator-${size}`;

  return (
    <div className={`quality-indicator ${sizeClass}`}>
      <div 
        className="quality-badge"
        style={{ backgroundColor: color }}
      >
        <span className="quality-icon">{icon}</span>
      </div>
      
      {showLabel && (
        <span 
          className="quality-label"
          style={{ color }}
        >
          {text}
        </span>
      )}
      
      {showDetails && (percentage !== undefined || count !== undefined) && (
        <div className="quality-details">
          {percentage !== undefined && (
            <div className="quality-percentage">
              {percentage.toFixed(1)}%
            </div>
          )}
          
          {count !== undefined && total !== undefined && (
            <div className="quality-count">
              {count} of {total}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MappingQualityIndicator;