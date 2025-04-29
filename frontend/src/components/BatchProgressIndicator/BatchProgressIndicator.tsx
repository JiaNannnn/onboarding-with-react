import React from 'react';
import './BatchProgressIndicator.css';

/**
 * Props for the batch progress indicator
 */
interface BatchProgressIndicatorProps {
  isInBatchMode: boolean;
  totalBatches: number;
  completedBatches: number;
  progress: number;
  taskId?: string | null;
  status?: 'pending' | 'processing' | 'completed' | 'failed';
  showDetails?: boolean;
  variant?: 'horizontal' | 'circular';
  size?: 'small' | 'medium' | 'large';
}

/**
 * Component for displaying batch processing progress
 */
const BatchProgressIndicator: React.FC<BatchProgressIndicatorProps> = ({
  isInBatchMode,
  totalBatches,
  completedBatches,
  progress,
  taskId = null,
  status = 'processing',
  showDetails = true,
  variant = 'horizontal',
  size = 'medium'
}) => {
  // If not in batch mode or no batches, show nothing
  if (!isInBatchMode || totalBatches <= 0) {
    return null;
  }

  // Calculate progress percentage
  const progressPercent = Math.round(progress * 100);
  
  // Determine color based on status
  const getStatusColor = () => {
    switch (status) {
      case 'pending': return '#FFC107';  // Amber
      case 'processing': return '#2196F3';  // Blue
      case 'completed': return '#4CAF50';  // Green
      case 'failed': return '#F44336';  // Red
      default: return '#2196F3';  // Default blue
    }
  };
  
  const statusColor = getStatusColor();
  
  // Determine size classes
  const sizeClass = `batch-progress-${size}`;
  
  if (variant === 'horizontal') {
    return (
      <div className={`batch-progress-container ${sizeClass}`}>
        <div className="batch-progress-bar-container">
          <div 
            className="batch-progress-bar"
            style={{ 
              width: `${progressPercent}%`, 
              backgroundColor: statusColor 
            }}
          />
        </div>
        
        {showDetails && (
          <div className="batch-progress-details">
            <div className="batch-progress-text">
              {status === 'processing' ? 'Processing' : status}
              {status === 'processing' && `: ${progressPercent}%`}
            </div>
            <div className="batch-progress-counts">
              Batch {completedBatches} of {totalBatches}
            </div>
            {taskId && <div className="batch-progress-task-id">Task: {taskId}</div>}
          </div>
        )}
      </div>
    );
  } else {
    // Circular progress indicator (SVG-based)
    const radius = size === 'small' ? 15 : size === 'medium' ? 20 : 25;
    const strokeWidth = size === 'small' ? 3 : size === 'medium' ? 4 : 5;
    const viewBoxSize = 2 * (radius + strokeWidth);
    const center = viewBoxSize / 2;
    const normalizedRadius = radius - strokeWidth / 2;
    const circumference = normalizedRadius * 2 * Math.PI;
    const strokeDashoffset = circumference - progress * circumference;
    
    return (
      <div className={`batch-progress-circular-container ${sizeClass}`}>
        <svg
          height={viewBoxSize}
          width={viewBoxSize}
          viewBox={`0 0 ${viewBoxSize} ${viewBoxSize}`}
        >
          <circle
            stroke="#e6e6e6"
            fill="transparent"
            strokeWidth={strokeWidth}
            r={normalizedRadius}
            cx={center}
            cy={center}
          />
          <circle
            stroke={statusColor}
            fill="transparent"
            strokeWidth={strokeWidth}
            strokeDasharray={`${circumference} ${circumference}`}
            style={{ strokeDashoffset }}
            strokeLinecap="round"
            r={normalizedRadius}
            cx={center}
            cy={center}
            transform={`rotate(-90, ${center}, ${center})`}
          />
          {size === 'large' && (
            <text
              x={center}
              y={center}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="10"
              fill="#333"
            >
              {progressPercent}%
            </text>
          )}
        </svg>
        
        {showDetails && (
          <div className="batch-progress-circular-details">
            <div className="batch-progress-text">
              {status === 'processing' ? 'Processing' : status}
            </div>
            <div className="batch-progress-counts">
              {completedBatches} of {totalBatches}
            </div>
          </div>
        )}
      </div>
    );
  }
};

export default BatchProgressIndicator;