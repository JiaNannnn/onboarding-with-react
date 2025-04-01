import { useState, useMemo } from 'react';
import { BMSPoint } from '../../types/apiTypes';
import { FilterState, SortState, TablePagination } from '../../components';

interface UsePointsFilteringOptions {
  initialSortState?: SortState;
  initialFilters?: FilterState[];
  initialPagination?: TablePagination;
  initialSearchTerm?: string;
  initialTypeFilter?: string;
}

/**
 * Custom hook for handling points filtering, sorting, and pagination
 */
export function usePointsFiltering(
  points: BMSPoint[],
  groups: Record<string, { points: BMSPoint[] }>,
  options: UsePointsFilteringOptions = {}
) {
  // State for filtering and sorting
  const [viewMode, setViewMode] = useState<'all' | 'ungrouped' | 'grouped'>('all');
  const [searchTerm, setSearchTerm] = useState(options.initialSearchTerm || '');
  const [typeFilter, setTypeFilter] = useState(options.initialTypeFilter || '');
  const [currentSort, setCurrentSort] = useState<SortState | undefined>(
    options.initialSortState || {
      columnId: 'pointName',
      direction: 'asc'
    }
  );
  const [filters, setFilters] = useState<FilterState[]>(options.initialFilters || []);
  const [tablePagination, setTablePagination] = useState<TablePagination>(
    options.initialPagination || {
      page: 1,
      pageSize: 10,
      enabled: true
    }
  );

  // Get all available point types
  const availablePointTypes = useMemo(() => {
    const types = new Set<string>();
    points.forEach(point => {
      if (point.pointType) {
        types.add(point.pointType);
      }
    });
    return Array.from(types).sort();
  }, [points]);

  // Helper function to get field value from point
  const getPointValue = (point: BMSPoint, field: string): any => {
    switch (field) {
      case 'pointName':
        return point.pointName;
      case 'pointType':
        return point.pointType;
      case 'unit':
        return point.unit;
      case 'description':
        return point.description;
      default:
        return (point as any)[field];
    }
  };

  // Filtered and sorted points
  const filteredPoints = useMemo(() => {
    let result = [...points];
    
    // Apply view mode filter
    if (viewMode === 'ungrouped') {
      const groupedPointIds = new Set<string>();
      Object.values(groups).forEach(group => {
        group.points.forEach(point => {
          groupedPointIds.add(point.id);
        });
      });
      result = result.filter(point => !groupedPointIds.has(point.id));
    } else if (viewMode === 'grouped') {
      const groupedPointIds = new Set<string>();
      Object.values(groups).forEach(group => {
        group.points.forEach(point => {
          groupedPointIds.add(point.id);
        });
      });
      result = result.filter(point => groupedPointIds.has(point.id));
    }
    
    // Apply type filter
    if (typeFilter) {
      result = result.filter(point => point.pointType === typeFilter);
    }
    
    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(point => {
        return (
          point.pointName.toLowerCase().includes(term) ||
          point.pointType.toLowerCase().includes(term) ||
          (point.description || '').toLowerCase().includes(term) ||
          (point.unit && point.unit.toLowerCase().includes(term))
        );
      });
    }
    
    // Apply custom filters
    if (filters.length > 0) {
      result = result.filter(point => {
        return filters.every(filter => {
          const value = String(getPointValue(point, filter.columnId)).toLowerCase();
          return value.includes(filter.value.toLowerCase());
        });
      });
    }
    
    // Apply sort
    if (currentSort) {
      result.sort((a, b) => {
        const aValue = getPointValue(a, currentSort.columnId);
        const bValue = getPointValue(b, currentSort.columnId);
        
        if (aValue === bValue) return 0;
        
        const result = aValue > bValue ? 1 : -1;
        return currentSort.direction === 'asc' ? result : -result;
      });
    }
    
    return result;
  }, [points, groups, viewMode, searchTerm, typeFilter, filters, currentSort]);

  // Handle sort change
  const handleSortChange = (sort: SortState) => {
    setCurrentSort(sort);
  };

  // Handle filter change
  const handleFilterChange = (newFilters: FilterState[]) => {
    setFilters(newFilters);
    // Reset to first page when filters change
    setTablePagination(prev => ({
      ...prev,
      page: 1
    }));
  };

  // Handle type filter change
  const handleTypeFilterChange = (value: string) => {
    setTypeFilter(value);
    setTablePagination(prev => ({
      ...prev,
      page: 1
    }));
  };

  // Handle search term change
  const handleSearchChange = (term: string) => {
    setSearchTerm(term);
    setTablePagination(prev => ({
      ...prev,
      page: 1
    }));
  };

  // Handle pagination change
  const handlePageChange = (page: number, pageSize: number) => {
    setTablePagination({
      page,
      pageSize,
      enabled: true
    });
  };

  // Calculate paginated data
  const paginatedPoints = useMemo(() => {
    if (!tablePagination.enabled) {
      return filteredPoints;
    }
    
    const start = (tablePagination.page - 1) * tablePagination.pageSize;
    return filteredPoints.slice(start, start + tablePagination.pageSize);
  }, [filteredPoints, tablePagination]);

  return {
    // State
    viewMode,
    searchTerm,
    typeFilter,
    currentSort,
    filters,
    tablePagination,
    
    // Computed values
    availablePointTypes,
    filteredPoints,
    paginatedPoints,
    
    // Actions
    setViewMode,
    handleSearchChange,
    handleTypeFilterChange,
    handleSortChange,
    handleFilterChange,
    handlePageChange,
    
    // Helper functions
    getPointValue
  };
}