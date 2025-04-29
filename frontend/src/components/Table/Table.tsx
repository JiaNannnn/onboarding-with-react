import React, { useState, useEffect, useCallback, ReactNode } from 'react';
import './Table.css';

/**
 * Column definition for the Table component
 */
export interface TableColumn<T> {
  /**
   * Unique identifier for the column
   */
  id: string;
  
  /**
   * Header text to display
   */
  header: string;
  
  /**
   * Function to access the cell value from row data
   */
  accessor: (row: T, index: number) => any;
  
  /**
   * Optional custom cell renderer
   */
  cell?: (value: any, row: T, index: number) => ReactNode;
  
  /**
   * Whether the column is sortable
   */
  sortable?: boolean;
  
  /**
   * Whether the column is filterable
   */
  filterable?: boolean;
  
  /**
   * Whether the column is editable
   */
  editable?: boolean;
  
  /**
   * Custom editor for the cell
   */
  editor?: (value: any, row: T, index: number, onSave: (value: any) => void) => ReactNode;
  
  /**
   * Width of the column (e.g., '150px', '20%')
   */
  width?: string;
  
  /**
   * Text alignment in the cell
   */
  align?: 'left' | 'center' | 'right';
  
  /**
   * Whether to enable text wrapping in the cell
   */
  wrap?: boolean;
  
  /**
   * Custom class name for the column
   */
  className?: string;
}

/**
 * Pagination options for the Table
 */
export interface TablePagination {
  /**
   * Current page (1-based)
   */
  page: number;
  
  /**
   * Number of rows per page
   */
  pageSize: number;
  
  /**
   * Total number of items (for server-side pagination)
   */
  totalItems?: number;
  
  /**
   * Whether pagination is enabled
   */
  enabled: boolean;
}

/**
 * Sort direction
 */
export type SortDirection = 'asc' | 'desc';

/**
 * Sort state
 */
export interface SortState {
  /**
   * Column ID being sorted
   */
  columnId: string;
  
  /**
   * Sort direction
   */
  direction: SortDirection;
}

/**
 * Filter state
 */
export interface FilterState {
  /**
   * Column ID being filtered
   */
  columnId: string;
  
  /**
   * Filter value
   */
  value: string;
}

/**
 * Table component props
 */
export interface TableProps<T> {
  /**
   * Columns definition
   */
  columns: TableColumn<T>[];
  
  /**
   * Data to display in the table
   */
  data: T[];
  
  /**
   * Loading state
   */
  loading?: boolean;
  
  /**
   * Error message
   */
  error?: string;
  
  /**
   * Whether to show a row selection checkbox
   */
  selectable?: boolean;
  
  /**
   * Whether to highlight rows on hover
   */
  highlightOnHover?: boolean;
  
  /**
   * Whether to stripe alternate rows
   */
  striped?: boolean;
  
  /**
   * Whether to add borders between cells
   */
  bordered?: boolean;
  
  /**
   * Whether to make the table compact
   */
  compact?: boolean;
  
  /**
   * Whether to make the table scrollable
   */
  scrollable?: boolean;
  
  /**
   * Pagination options
   */
  pagination?: TablePagination;
  
  /**
   * Default sort
   */
  defaultSort?: SortState;
  
  /**
   * Default filter
   */
  defaultFilter?: FilterState[];
  
  /**
   * Whether to enable client-side sorting
   */
  enableClientSort?: boolean;
  
  /**
   * Whether to enable client-side filtering
   */
  enableClientFilter?: boolean;
  
  /**
   * Whether to resize columns
   */
  resizableColumns?: boolean;
  
  /**
   * Custom no data message
   */
  noDataMessage?: string;
  
  /**
   * Custom loading message
   */
  loadingMessage?: string;
  
  /**
   * Custom row key function
   */
  rowKey?: (row: T, index: number) => string;
  
  /**
   * Callback for row selection change
   */
  onSelectionChange?: (selectedRows: T[]) => void;
  
  /**
   * Callback for row click
   */
  onRowClick?: (row: T, index: number) => void;
  
  /**
   * Callback for cell click
   */
  onCellClick?: (value: any, row: T, columnId: string, index: number) => void;
  
  /**
   * Callback for sort change
   */
  onSortChange?: (sort: SortState) => void;
  
  /**
   * Callback for filter change
   */
  onFilterChange?: (filters: FilterState[]) => void;
  
  /**
   * Callback for pagination change
   */
  onPageChange?: (page: number, pageSize: number) => void;
  
  /**
   * Callback for row data change (editing)
   */
  onRowChange?: (newRow: T, oldRow: T, index: number) => void;
  
  /**
   * Custom row class name function
   */
  rowClassName?: (row: T, index: number) => string;
  
  /**
   * Custom cell class name function
   */
  cellClassName?: (value: any, row: T, columnId: string, index: number) => string;
  
  /**
   * Custom empty row component
   */
  emptyRowsComponent?: ReactNode;
  
  /**
   * Class name for the table container
   */
  className?: string;
}

/**
 * Cell edit state
 */
interface CellEditState {
  rowIndex: number;
  columnId: string;
  value: any;
}

/**
 * Table component
 */
function Table<T>({
  columns,
  data,
  loading = false,
  error,
  selectable = false,
  highlightOnHover = true,
  striped = true,
  bordered = false,
  compact = false,
  scrollable = false,
  pagination,
  defaultSort,
  defaultFilter,
  enableClientSort = true,
  enableClientFilter = true,
  resizableColumns = false,
  noDataMessage = 'No data available',
  loadingMessage = 'Loading...',
  rowKey = (_, index) => `row-${index}`,
  onSelectionChange,
  onRowClick,
  onCellClick,
  onSortChange,
  onFilterChange,
  onPageChange,
  onRowChange,
  rowClassName,
  cellClassName,
  emptyRowsComponent,
  className = '',
}: TableProps<T>): JSX.Element {
  const [selectedRows, setSelectedRows] = useState<T[]>([]);
  const [sortState, setSortState] = useState<SortState | undefined>(defaultSort);
  const [filterState, setFilterState] = useState<FilterState[]>(defaultFilter || []);
  const [editingCell, setEditingCell] = useState<CellEditState | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(pagination?.page || 1);
  const [currentPageSize, setCurrentPageSize] = useState<number>(pagination?.pageSize || 10);
  
  // Process data based on filters, sorting, and pagination
  const processedData = useCallback(() => {
    let result = [...data];
    
    // Apply client-side filtering
    if (enableClientFilter && filterState.length > 0) {
      filterState.forEach(filter => {
        const column = columns.find(col => col.id === filter.columnId);
        if (column) {
          result = result.filter(row => {
            const value = column.accessor(row, 0);
            if (value == null) return false;
            
            return String(value).toLowerCase().includes(filter.value.toLowerCase());
          });
        }
      });
    }
    
    // Apply client-side sorting
    if (enableClientSort && sortState) {
      const column = columns.find(col => col.id === sortState.columnId);
      if (column) {
        result.sort((a, b) => {
          const valueA = column.accessor(a, 0);
          const valueB = column.accessor(b, 0);
          
          if (valueA === valueB) return 0;
          
          const comparison = valueA > valueB ? 1 : -1;
          
          return sortState.direction === 'asc' ? comparison : -comparison;
        });
      }
    }
    
    // Apply client-side pagination
    if (pagination?.enabled) {
      const startIndex = (currentPage - 1) * currentPageSize;
      const endIndex = Math.min(startIndex + currentPageSize, result.length);
      return result.slice(startIndex, endIndex);
    }
    
    return result;
  }, [data, columns, filterState, sortState, enableClientFilter, enableClientSort, pagination, currentPage, currentPageSize]);
  
  // Update internal state when props change for pagination
  // Make sure our pagination state stays in sync with parent component
  useEffect(() => {
    if (pagination) {
      // Use a single condition to avoid race conditions between page and pageSize updates
      const pageChanged = pagination.page !== currentPage;
      const pageSizeChanged = pagination.pageSize !== currentPageSize;
      
      if (pageChanged || pageSizeChanged) {
        if (pageChanged) {
          setCurrentPage(pagination.page);
        }
        if (pageSizeChanged) {
          setCurrentPageSize(pagination.pageSize);
        }
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pagination?.page, pagination?.pageSize, currentPage, currentPageSize]);
  
  // Reset to page 1 if data length changes dramatically (e.g., on filter change or new data load)
  useEffect(() => {
    if (pagination?.enabled) {
      const totalPages = Math.ceil(data.length / currentPageSize);
      
      // If current page is out of bounds due to data length change,
      // reset to page 1 (or the max available page)
      if ((currentPage > totalPages && totalPages > 0) || 
          (data.length > 0 && totalPages === 0)) {
        // Use the valid page number
        const validPage = Math.max(1, Math.min(currentPage, totalPages || 1));
        
        // Only update if necessary - prevent triggering the callback unnecessarily
        if (validPage !== currentPage) {
          setCurrentPage(validPage);
          
          // Ensure callback uses the proper page number
          if (onPageChange) {
            // Use direct call, not setTimeout to prevent race conditions
            onPageChange(validPage, currentPageSize);
          }
        }
      }
    }
  }, [data.length, currentPage, currentPageSize, pagination?.enabled, onPageChange]);
  
  // Update selected rows when data changes
  useEffect(() => {
    if (selectedRows.length > 0) {
      const newSelectedRows = selectedRows.filter(selectedRow => 
        data.some(row => JSON.stringify(row) === JSON.stringify(selectedRow))
      );
      
      setSelectedRows(newSelectedRows);
      if (onSelectionChange) {
        onSelectionChange(newSelectedRows);
      }
    }
  }, [data, selectedRows, onSelectionChange]);
  
  // Handle row selection
  const handleRowSelection = (row: T, isSelected: boolean) => {
    let newSelectedRows: T[];
    
    if (isSelected) {
      newSelectedRows = [...selectedRows, row];
    } else {
      newSelectedRows = selectedRows.filter(r => JSON.stringify(r) !== JSON.stringify(row));
    }
    
    setSelectedRows(newSelectedRows);
    
    if (onSelectionChange) {
      onSelectionChange(newSelectedRows);
    }
  };
  
  // Handle header selection (select all)
  const handleHeaderSelection = (isSelected: boolean) => {
    const newSelectedRows = isSelected ? [...data] : [];
    setSelectedRows(newSelectedRows);
    
    if (onSelectionChange) {
      onSelectionChange(newSelectedRows);
    }
  };
  
  // Handle column sort
  const handleSort = (columnId: string) => {
    const column = columns.find(col => col.id === columnId);
    
    if (!column?.sortable) return;
    
    let direction: SortDirection = 'asc';
    
    if (sortState?.columnId === columnId) {
      if (sortState.direction === 'asc') {
        direction = 'desc';
      } else {
        // If it's already desc, remove sorting
        setSortState(undefined);
        if (onSortChange) {
          onSortChange({ columnId, direction: 'asc' });
        }
        return;
      }
    }
    
    const newSortState: SortState = { columnId, direction };
    setSortState(newSortState);
    
    if (onSortChange) {
      onSortChange(newSortState);
    }
  };
  
  // Handle filtering
  const handleFilter = (columnId: string, value: string) => {
    let newFilterState: FilterState[];
    
    if (value === '') {
      // Remove filter for this column
      newFilterState = filterState.filter(f => f.columnId !== columnId);
    } else {
      // Update or add filter
      const existingFilterIndex = filterState.findIndex(f => f.columnId === columnId);
      
      if (existingFilterIndex >= 0) {
        newFilterState = [...filterState];
        newFilterState[existingFilterIndex] = { columnId, value };
      } else {
        newFilterState = [...filterState, { columnId, value }];
      }
    }
    
    setFilterState(newFilterState);
    
    if (onFilterChange) {
      onFilterChange(newFilterState);
    }
  };
  
  // Handle page change with validation - fully synchronous
  const handlePageChange = (page: number) => {
    // Calculate total pages to ensure the page is valid
    const totalItems = pagination?.totalItems ?? data.length;
    const totalPages = Math.max(1, Math.ceil(totalItems / currentPageSize));
    
    // Ensure the page is within valid bounds
    const validPage = Math.max(1, Math.min(page, totalPages));
    
    // Only update if it's actually changed to prevent loop
    if (validPage !== currentPage) {
      // Update internal state first
      setCurrentPage(validPage);
      
      // Notify parent without setTimeout - this fixes the coordination issue
      if (onPageChange) {
        onPageChange(validPage, currentPageSize);
      }
    }
  };
  
  // Handle page size change
  const handlePageSizeChange = (size: number) => {
    setCurrentPageSize(size);
    setCurrentPage(1); // Reset to first page
    
    if (onPageChange) {
      onPageChange(1, size);
    }
  };
  
  // Start cell editing
  const startEditing = (rowIndex: number, columnId: string, value: any) => {
    setEditingCell({ rowIndex, columnId, value });
  };
  
  // Save cell edit
  const saveEdit = (newValue: any) => {
    if (!editingCell) return;
    
    const { rowIndex, columnId } = editingCell;
    const column = columns.find(col => col.id === columnId);
    
    if (!column) return;
    
    const newData = [...data];
    const oldRow = { ...newData[rowIndex] };
    
    // Update the value using property path
    const keys = columnId.split('.');
    let current = newData[rowIndex] as any;
    
    // Navigate to the last object in the path
    for (let i = 0; i < keys.length - 1; i++) {
      if (!current[keys[i]]) current[keys[i]] = {};
      current = current[keys[i]];
    }
    
    // Set the value
    current[keys[keys.length - 1]] = newValue;
    
    if (onRowChange) {
      onRowChange(newData[rowIndex], oldRow, rowIndex);
    }
    
    setEditingCell(null);
  };
  
  // Cancel cell editing
  const cancelEdit = () => {
    setEditingCell(null);
  };
  
  // Calculate table classes
  const tableClasses = [
    'bms-table',
    striped ? 'bms-table--striped' : '',
    bordered ? 'bms-table--bordered' : '',
    compact ? 'bms-table--compact' : '',
    scrollable ? 'bms-table--scrollable' : '',
    className,
  ].filter(Boolean).join(' ');
  
  // Render table header
  const renderHeader = () => {
    return (
      <thead className="bms-table__header">
        <tr>
          {selectable && (
            <th className="bms-table__select-cell">
              <input
                type="checkbox"
                checked={data.length > 0 && selectedRows.length === data.length}
                onChange={(e) => handleHeaderSelection(e.target.checked)}
              />
            </th>
          )}
          
          {columns.map((column) => {
            const isSorted = sortState?.columnId === column.id;
            const headerClasses = [
              'bms-table__header-cell',
              column.sortable ? 'bms-table__header-cell--sortable' : '',
              isSorted ? `bms-table__header-cell--sorted-${sortState?.direction}` : '',
              column.align ? `bms-table__header-cell--${column.align}` : '',
              column.className || '',
            ].filter(Boolean).join(' ');
            
            return (
              <th
                key={column.id}
                className={headerClasses}
                style={{ width: column.width }}
                onClick={() => column.sortable && handleSort(column.id)}
              >
                <div className="bms-table__header-content">
                  <span>{column.header}</span>
                  
                  {column.sortable && (
                    <span className="bms-table__sort-icon">
                      {isSorted && sortState?.direction === 'asc' && '▲'}
                      {isSorted && sortState?.direction === 'desc' && '▼'}
                      {!isSorted && '⇅'}
                    </span>
                  )}
                </div>
                
                {column.filterable && (
                  <div className="bms-table__filter">
                    <input
                      type="text"
                      placeholder="Filter..."
                      onChange={(e) => handleFilter(column.id, e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      value={filterState.find(f => f.columnId === column.id)?.value || ''}
                    />
                  </div>
                )}
              </th>
            );
          })}
        </tr>
      </thead>
    );
  };
  
  // Render table body
  const renderBody = () => {
    const displayData = processedData();
    
    if (loading) {
      return (
        <tbody>
          <tr>
            <td
              colSpan={columns.length + (selectable ? 1 : 0)}
              className="bms-table__loading-cell"
            >
              {loadingMessage}
            </td>
          </tr>
        </tbody>
      );
    }
    
    if (error) {
      return (
        <tbody>
          <tr>
            <td
              colSpan={columns.length + (selectable ? 1 : 0)}
              className="bms-table__error-cell"
            >
              {error}
            </td>
          </tr>
        </tbody>
      );
    }
    
    if (displayData.length === 0) {
      return (
        <tbody>
          <tr>
            <td
              colSpan={columns.length + (selectable ? 1 : 0)}
              className="bms-table__empty-cell"
            >
              {emptyRowsComponent || noDataMessage}
            </td>
          </tr>
        </tbody>
      );
    }
    
    return (
      <tbody>
        {displayData.map((row, rowIndex) => {
          const isSelected = selectedRows.some(
            selectedRow => JSON.stringify(selectedRow) === JSON.stringify(row)
          );
          
          const rowClasses = [
            'bms-table__row',
            isSelected ? 'bms-table__row--selected' : '',
            highlightOnHover ? 'bms-table__row--hover' : '',
            rowClassName ? rowClassName(row, rowIndex) : '',
          ].filter(Boolean).join(' ');
          
          return (
            <tr
              key={rowKey(row, rowIndex)}
              className={rowClasses}
              onClick={() => onRowClick && onRowClick(row, rowIndex)}
            >
              {selectable && (
                <td className="bms-table__select-cell">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={(e) => handleRowSelection(row, e.target.checked)}
                    onClick={(e) => e.stopPropagation()}
                  />
                </td>
              )}
              
              {columns.map((column) => {
                const value = column.accessor(row, rowIndex);
                const isEditing = editingCell && 
                  editingCell.rowIndex === rowIndex && 
                  editingCell.columnId === column.id;
                
                const cellClasses = [
                  'bms-table__cell',
                  column.align ? `bms-table__cell--${column.align}` : '',
                  column.wrap ? 'bms-table__cell--wrap' : '',
                  isEditing ? 'bms-table__cell--editing' : '',
                  cellClassName ? cellClassName(value, row, column.id, rowIndex) : '',
                  column.className || '',
                ].filter(Boolean).join(' ');
                
                return (
                  <td
                    key={column.id}
                    className={cellClasses}
                    onClick={(e) => {
                      e.stopPropagation();
                      
                      if (onCellClick) {
                        onCellClick(value, row, column.id, rowIndex);
                      }
                      
                      if (column.editable && !isEditing) {
                        startEditing(rowIndex, column.id, value);
                      }
                    }}
                  >
                    {isEditing ? (
                      <div className="bms-table__editor">
                        {column.editor ? (
                          column.editor(value, row, rowIndex, saveEdit)
                        ) : (
                          <div className="bms-table__default-editor">
                            <input
                              type="text"
                              defaultValue={value}
                              autoFocus
                              onBlur={(e) => saveEdit(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  saveEdit(e.currentTarget.value);
                                } else if (e.key === 'Escape') {
                                  cancelEdit();
                                }
                              }}
                            />
                          </div>
                        )}
                      </div>
                    ) : (
                      <>
                        {column.cell ? column.cell(value, row, rowIndex) : value}
                        {column.editable && (
                          <div className="bms-table__edit-indicator">✎</div>
                        )}
                      </>
                    )}
                  </td>
                );
              })}
            </tr>
          );
        })}
      </tbody>
    );
  };
  
  // Render pagination
  const renderPagination = () => {
    if (!pagination?.enabled) return null;
    
    const totalItems = pagination.totalItems ?? data.length;
    const totalPages = Math.max(1, Math.ceil(totalItems / currentPageSize));
    
    // Ensure current page is within valid range
    const validCurrentPage = Math.min(Math.max(1, currentPage), totalPages);
    
    // Instead of using setTimeout, we'll update the internal state directly
    // This avoids potential race conditions with the parent component's state
    if (validCurrentPage !== currentPage) {
      // Update internal state only - don't trigger the callback here
      // The callback will be triggered by the parent component when needed
      setCurrentPage(validCurrentPage);
    }
    
    // Generate page numbers to display
    const getPageNumbers = () => {
      const pages: (number | string)[] = [];
      const maxPages = 7; // Max number of page buttons to show
      
      if (totalPages <= maxPages) {
        // Show all pages
        for (let i = 1; i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        // Always show first page
        pages.push(1);
        
        // Show ellipsis if needed
        if (validCurrentPage > 3) {
          pages.push('...');
        }
        
        // Calculate range around current page
        let start = Math.max(2, validCurrentPage - 1);
        let end = Math.min(totalPages - 1, validCurrentPage + 1);
        
        // Adjust range to always show at least 3 pages when possible
        if (validCurrentPage <= 3) {
          // Near the beginning, show more pages after current
          end = Math.min(5, totalPages - 1);
        } else if (validCurrentPage >= totalPages - 2) {
          // Near the end, show more pages before current
          start = Math.max(2, totalPages - 4);
        }
        
        for (let i = start; i <= end; i++) {
          pages.push(i);
        }
        
        // Show ellipsis if needed
        if (validCurrentPage < totalPages - 2) {
          pages.push('...');
        }
        
        // Always show last page
        if (totalPages > 1) {
          pages.push(totalPages);
        }
      }
      
      return pages;
    };
    
    // Calculate display range
    const startItem = Math.min((validCurrentPage - 1) * currentPageSize + 1, totalItems);
    const endItem = Math.min(validCurrentPage * currentPageSize, totalItems);
    
    return (
      <div className="bms-table__pagination">
        <div className="bms-table__pagination-info">
          {totalItems > 0 ? (
            <>Showing {startItem} to {endItem} of {totalItems} entries</>
          ) : (
            <>No entries to display</>
          )}
        </div>
        
        <div className="bms-table__pagination-controls">
          <button
            className="bms-table__pagination-button"
            onClick={() => handlePageChange(1)}
            disabled={validCurrentPage === 1 || totalItems === 0}
          >
            &laquo;
          </button>
          
          <button
            className="bms-table__pagination-button"
            onClick={() => handlePageChange(validCurrentPage - 1)}
            disabled={validCurrentPage === 1 || totalItems === 0}
          >
            &lsaquo;
          </button>
          
          {getPageNumbers().map((page, index) => (
            typeof page === 'number' ? (
              <button
                key={index}
                className={`bms-table__pagination-button ${page === validCurrentPage ? 'bms-table__pagination-button--active' : ''}`}
                onClick={(e) => {
                  // Prevent default to avoid any browser-specific issues
                  e.preventDefault();
                  // Only trigger page change if it's different from current page
                  if (page !== validCurrentPage) {
                    handlePageChange(page);
                  }
                }}
                disabled={totalItems === 0}
              >
                {page}
              </button>
            ) : (
              <span key={index} className="bms-table__pagination-ellipsis">
                {page}
              </span>
            )
          ))}
          
          <button
            className="bms-table__pagination-button"
            onClick={() => handlePageChange(validCurrentPage + 1)}
            disabled={validCurrentPage === totalPages || totalItems === 0}
          >
            &rsaquo;
          </button>
          
          <button
            className="bms-table__pagination-button"
            onClick={() => handlePageChange(totalPages)}
            disabled={validCurrentPage === totalPages || totalItems === 0}
          >
            &raquo;
          </button>
        </div>
        
        <div className="bms-table__pagination-sizes">
          <select
            value={currentPageSize}
            onChange={(e) => handlePageSizeChange(Number(e.target.value))}
            disabled={totalItems === 0}
          >
            <option value={5}>5 per page</option>
            <option value={10}>10 per page</option>
            <option value={25}>25 per page</option>
            <option value={50}>50 per page</option>
            <option value={100}>100 per page</option>
          </select>
        </div>
      </div>
    );
  };
  
  return (
    <div className="bms-table-container">
      <div className={scrollable ? 'bms-table-scroll' : ''}>
        <table className={tableClasses}>
          {renderHeader()}
          {renderBody()}
        </table>
      </div>
      {renderPagination()}
    </div>
  );
}

export default Table; 