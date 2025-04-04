import React from 'react';
import { Table, TableColumn, SortState, FilterState, TablePagination } from '../../components';
import { BMSPoint } from '../../types/apiTypes';
import './PointsTable.css';

interface PointsTableProps {
  points: BMSPoint[];
  selectedPoints: BMSPoint[];
  groups: Record<string, { points: BMSPoint[]; name: string }>;
  isLoading: boolean;
  error?: string;
  currentSort?: SortState;
  filters: FilterState[];
  pagination: TablePagination;
  typeFilter: string;
  availablePointTypes: string[];
  searchTerm: string;
  viewMode: 'all' | 'ungrouped' | 'grouped';
  isProcessingAI: boolean;
  onPointSelect: (point: BMSPoint) => void;
  onSortChange: (sort: SortState) => void;
  onFilterChange: (filters: FilterState[]) => void;
  onPageChange: (page: number, pageSize: number) => void;
  onTypeFilterChange: (typeFilter: string) => void;
  onSearchChange: (searchTerm: string) => void;
  onViewModeChange: (viewMode: 'all' | 'ungrouped' | 'grouped') => void;
  onPointDragStart: (e: React.DragEvent, pointId: string) => void;
  onRemovePointFromGroup: (groupId: string, pointId: string) => void;
}

/**
 * Table component for displaying and managing points
 */
const PointsTable: React.FC<PointsTableProps> = ({
  points,
  selectedPoints,
  groups,
  isLoading,
  error,
  currentSort,
  filters,
  pagination,
  typeFilter,
  availablePointTypes,
  searchTerm,
  viewMode,
  isProcessingAI,
  onPointSelect,
  onSortChange,
  onFilterChange,
  onPageChange,
  onTypeFilterChange,
  onSearchChange,
  onViewModeChange,
  onPointDragStart,
  onRemovePointFromGroup
}) => {
  // Empty state rendering
  const renderEmptyState = () => {
    if (isLoading || isProcessingAI) {
      return null; // Don't show empty state while loading
    }
    
    let message = '';
    
    if (points.length === 0) {
      message = 'No points available. Upload points using the "Upload Points" button.';
    } else if (points.length === 0) {
      if (searchTerm) {
        message = `No points match your search "${searchTerm}". Try changing your search terms.`;
      } else if (typeFilter) {
        message = `No points with type "${typeFilter}" found. Try selecting a different type.`;
      } else if (viewMode === 'ungrouped') {
        message = 'All points are assigned to groups.';
      } else if (viewMode === 'grouped') {
        message = 'No points are currently assigned to any group.';
      } else {
        message = 'No points match the current filter criteria.';
      }
    }
    
    if (!message) return null;
    
    return (
      <div className="points-table__empty-state">
        <div className="points-table__empty-icon">📊</div>
        <div className="points-table__empty-message">{message}</div>
      </div>
    );
  };

  // Table columns configuration
  const columns: TableColumn<BMSPoint>[] = [
    {
      id: 'select',
      header: '',
      accessor: () => '',
      cell: (_, row) => (
        <input
          type="checkbox"
          checked={selectedPoints.some(p => p.id === row.id)}
          onChange={(e) => {
            e.stopPropagation();
            onPointSelect(row);
          }}
          disabled={isLoading || isProcessingAI}
        />
      ),
      width: '40px'
    },
    {
      id: 'pointName',
      header: 'Point Name',
      accessor: (row) => row.pointName,
      cell: (value, row) => (
        <div
          draggable
          onDragStart={(e) => onPointDragStart(e, row.id)}
          className="points-table__draggable"
          title={value}
        >
          {value}
        </div>
      ),
      sortable: true,
      filterable: true,
      width: '200px'
    },
    {
      id: 'rawPointName',
      header: 'Raw Point Name',
      accessor: (row) => {
        // Extract just the point name without device prefixes
        const pointNameParts = row.pointName.split('.');
        return pointNameParts.length > 1 ? pointNameParts[pointNameParts.length - 1] : row.pointName;
      },
      cell: (value) => (
        <div title={value}>
          {value}
        </div>
      ),
      sortable: true,
      filterable: true,
      width: '150px'
    },
    {
      id: 'pointType',
      header: 'Type',
      accessor: (row) => row.pointType,
      cell: (value) => (
        <div data-type={value?.toUpperCase()}>
          <span className="points-table__type-badge">
            {value || 'Unknown'}
          </span>
        </div>
      ),
      sortable: true,
      filterable: true,
      width: '120px'
    },
    {
      id: 'unit',
      header: 'Unit',
      accessor: (row) => row.unit || '-',
      cell: (value) => (
        value && value !== '-' ? (
          <span className="points-table__unit">{value}</span>
        ) : (
          <span className="points-table__empty-value">-</span>
        )
      ),
      sortable: true,
      filterable: true,
      width: '80px'
    },
    {
      id: 'description',
      header: 'Description',
      accessor: (row) => row.description,
      cell: (value) => (
        <div className="points-table__description" title={value}>
          {value || <span className="points-table__empty-value">No description</span>}
        </div>
      ),
      sortable: true,
      filterable: true,
      width: '200px'
    },
    {
      id: 'enosPoints',
      header: 'EnOS Points',
      accessor: (row) => row.enosPoints,
      cell: (value, row) => (
        <div className="points-table__enos-points" title={value}>
          {value ? (
            <div className="points-table__mapping">
              <span className="points-table__enos-point">{value}</span>
            </div>
          ) : (
            <span className="points-table__empty-value">Not mapped</span>
          )}
        </div>
      ),
      sortable: true,
      filterable: true,
      width: '180px'
    },
    {
      id: 'group',
      header: 'Group',
      accessor: (row) => {
        // Find the group this point belongs to
        for (const [, group] of Object.entries(groups)) {
          if (group.points.some(p => p.id === row.id)) {
            return group.name;
          }
        }
        return 'Ungrouped';
      },
      sortable: true,
      filterable: true,
      cell: (_, row) => {
        // Find the group this point belongs to
        const groupEntry = Object.entries(groups).find(
          ([, group]) => group.points.some(p => p.id === row.id)
        );
        
        if (groupEntry) {
          const [groupId, group] = groupEntry;
          return (
            <div className="points-table__group-tag">
              <span>{group.name}</span>
              <button 
                className="points-table__remove-button"
                onClick={(e) => {
                  e.stopPropagation();
                  onRemovePointFromGroup(groupId, row.id);
                }}
                title="Remove from group"
              >
                &times;
              </button>
            </div>
          );
        }
        
        return <span className="points-table__no-group">Ungrouped</span>;
      },
      width: '150px'
    }
  ];
  
  return (
    <div className="points-table">
      <div className="points-table__toolbar">
        <div className="points-table__filters">
          <div className="points-table__search">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search points..."
              className="points-table__search-input"
              disabled={isLoading || isProcessingAI}
            />
          </div>
          
          <div className="points-table__type-filter">
            <select
              value={typeFilter}
              onChange={(e) => onTypeFilterChange(e.target.value)}
              className="points-table__type-select"
              disabled={isLoading || isProcessingAI}
            >
              <option value="">All Types</option>
              {availablePointTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          
          <div className="points-table__view-filter">
            <select 
              value={viewMode}
              onChange={(e) => onViewModeChange(e.target.value as 'all' | 'ungrouped' | 'grouped')}
              className="points-table__view-select"
              disabled={isLoading || isProcessingAI}
            >
              <option value="all">All Points</option>
              <option value="ungrouped">Ungrouped Points</option>
              <option value="grouped">Grouped Points</option>
            </select>
          </div>
        </div>
      </div>
      
      <div className="points-table__count">
        {selectedPoints.length} point{selectedPoints.length !== 1 ? 's' : ''} selected
      </div>
      
      {points.length === 0 ? (
        renderEmptyState()
      ) : (
        <div className="points-table__container">
          <Table
            columns={columns}
            data={points}
            loading={isLoading || isProcessingAI}
            error={error}
            selectable={true}
            highlightOnHover={true}
            striped={true}
            bordered={false}
            scrollable={true}
            rowKey={(row) => row.id}
            onRowClick={onPointSelect}
            enableClientSort={true}
            enableClientFilter={true}
            defaultSort={currentSort}
            onSortChange={onSortChange}
            onFilterChange={onFilterChange}
            pagination={pagination}
            onPageChange={onPageChange}
          />
        </div>
      )}
    </div>
  );
};

export default PointsTable;