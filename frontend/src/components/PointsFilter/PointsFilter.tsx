import React, { useState, useEffect } from 'react';
import './PointsFilter.css';

export interface PointsFilterProps {
  /**
   * Available point types for filtering
   */
  pointTypes: string[];
  
  /**
   * Currently selected point types for filtering
   */
  selectedTypes?: string[];
  
  /**
   * Search term for text-based filtering
   */
  searchTerm?: string;
  
  /**
   * Placeholder text for the search input
   */
  searchPlaceholder?: string;
  
  /**
   * Whether the component is in a loading state
   */
  loading?: boolean;
  
  /**
   * Whether the filter is disabled
   */
  disabled?: boolean;
  
  /**
   * Additional CSS class name
   */
  className?: string;
  
  /**
   * Callback when search term changes
   */
  onSearchChange?: (searchTerm: string) => void;
  
  /**
   * Callback when selected types change
   */
  onTypeSelectionChange?: (selectedTypes: string[]) => void;
  
  /**
   * Callback when filter is applied
   */
  onApplyFilter?: (searchTerm: string, selectedTypes: string[]) => void;
  
  /**
   * Callback when filter is reset
   */
  onResetFilter?: () => void;
}

/**
 * PointsFilter component
 * 
 * A component for filtering BMS points by type and search term
 */
const PointsFilter: React.FC<PointsFilterProps> = ({
  pointTypes,
  selectedTypes = [],
  searchTerm = '',
  searchPlaceholder = 'Search points...',
  loading = false,
  disabled = false,
  className = '',
  onSearchChange,
  onTypeSelectionChange,
  onApplyFilter,
  onResetFilter,
}) => {
  // Local state for filter values
  const [localSearchTerm, setLocalSearchTerm] = useState(searchTerm);
  const [localSelectedTypes, setLocalSelectedTypes] = useState<string[]>(selectedTypes);
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Update local state when props change
  useEffect(() => {
    setLocalSearchTerm(searchTerm);
  }, [searchTerm]);
  
  useEffect(() => {
    setLocalSelectedTypes(selectedTypes);
  }, [selectedTypes]);
  
  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setLocalSearchTerm(value);
    
    if (onSearchChange) {
      onSearchChange(value);
    }
  };
  
  // Handle type selection change
  const handleTypeChange = (type: string) => {
    const updatedTypes = localSelectedTypes.includes(type)
      ? localSelectedTypes.filter(t => t !== type)
      : [...localSelectedTypes, type];
    
    setLocalSelectedTypes(updatedTypes);
    
    if (onTypeSelectionChange) {
      onTypeSelectionChange(updatedTypes);
    }
  };
  
  // Handle select all types
  const handleSelectAllTypes = () => {
    setLocalSelectedTypes(pointTypes);
    
    if (onTypeSelectionChange) {
      onTypeSelectionChange(pointTypes);
    }
  };
  
  // Handle clear all types
  const handleClearTypes = () => {
    setLocalSelectedTypes([]);
    
    if (onTypeSelectionChange) {
      onTypeSelectionChange([]);
    }
  };
  
  // Handle apply filter
  const handleApplyFilter = () => {
    if (onApplyFilter) {
      onApplyFilter(localSearchTerm, localSelectedTypes);
    }
    setIsExpanded(false);
  };
  
  // Handle reset filter
  const handleResetFilter = () => {
    setLocalSearchTerm('');
    setLocalSelectedTypes([]);
    
    if (onResetFilter) {
      onResetFilter();
    }
  };
  
  // Combine class names
  const rootClassName = [
    'bms-points-filter',
    disabled ? 'bms-points-filter--disabled' : '',
    isExpanded ? 'bms-points-filter--expanded' : '',
    className,
  ].filter(Boolean).join(' ');
  
  return (
    <div className={rootClassName}>
      <div className="bms-points-filter__header">
        <div className="bms-points-filter__search">
          <input
            type="text"
            className="bms-points-filter__search-input"
            placeholder={searchPlaceholder}
            value={localSearchTerm}
            onChange={handleSearchChange}
            disabled={disabled || loading}
          />
          {localSearchTerm && (
            <button
              className="bms-points-filter__search-clear"
              onClick={() => setLocalSearchTerm('')}
              disabled={disabled || loading}
            >
              ×
            </button>
          )}
        </div>
        
        <button
          className={`bms-points-filter__toggle ${isExpanded ? 'bms-points-filter__toggle--active' : ''}`}
          onClick={() => setIsExpanded(!isExpanded)}
          disabled={disabled || loading}
        >
          <span className="bms-points-filter__toggle-text">
            {isExpanded ? 'Hide Filters' : 'Show Filters'}
          </span>
          <span className="bms-points-filter__toggle-icon"></span>
        </button>
      </div>
      
      {isExpanded && (
        <div className="bms-points-filter__content">
          <div className="bms-points-filter__section">
            <div className="bms-points-filter__section-header">
              <h3 className="bms-points-filter__section-title">Point Types</h3>
              <div className="bms-points-filter__section-actions">
                <button
                  className="bms-points-filter__action-btn"
                  onClick={handleSelectAllTypes}
                  disabled={disabled || loading}
                >
                  Select All
                </button>
                <button
                  className="bms-points-filter__action-btn"
                  onClick={handleClearTypes}
                  disabled={disabled || loading}
                >
                  Clear
                </button>
              </div>
            </div>
            
            <div className="bms-points-filter__types-list">
              {pointTypes.map(type => (
                <div key={type} className="bms-points-filter__type-item">
                  <label className="bms-points-filter__checkbox">
                    <input
                      type="checkbox"
                      checked={localSelectedTypes.includes(type)}
                      onChange={() => handleTypeChange(type)}
                      disabled={disabled || loading}
                    />
                    <span className="bms-points-filter__checkbox-label">{type}</span>
                  </label>
                </div>
              ))}
            </div>
          </div>
          
          <div className="bms-points-filter__actions">
            <button 
              className="bms-points-filter__apply-btn"
              onClick={handleApplyFilter}
              disabled={disabled || loading}
            >
              Apply Filters
            </button>
            <button
              className="bms-points-filter__reset-btn"
              onClick={handleResetFilter}
              disabled={disabled || loading}
            >
              Reset
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PointsFilter; 