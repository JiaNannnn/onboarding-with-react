import * as React from 'react';
import { useState, useEffect, useRef } from 'react';
import { Card } from '../../components';
import { HotTable } from '@handsontable/react';
import { registerAllModules } from 'handsontable/registry';
import type { GridSettings } from 'handsontable/settings';
import Handsontable from 'handsontable';
import type { CellProperties } from 'handsontable/settings';
import 'handsontable/dist/handsontable.full.css';
import { useMappingContext } from '../../contexts/MappingContext';
import { BMSPoint, PointMapping, MapPointsResponse } from '../../types/apiTypes';
import { useBMSClient } from '../../hooks/useBMSClient';
import './MapPoints.css';

// Define a custom interface for the ref to avoid TypeScript errors
interface HotTableRefType {
  hotInstance?: Handsontable;
}

// Register all Handsontable modules
registerAllModules();

/**
 * MapPoints page component
 * Allows users to map grouped HVAC device points to EnOS model points
 */
const MapPoints: React.FC = () => {
  const [points, setPoints] = useState<BMSPoint[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isMapping, setIsMapping] = useState<boolean>(false);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  // Using a mutable ref object to track the hot instance
  const hotInstanceRef = useRef<Handsontable | null>(null);
  
  const { mappings, setMappings, setFilename } = useMappingContext();
  const bmsClient = useBMSClient();

  // Handle file upload
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setIsLoading(true);
    setSelectedFile(file);
    const fileExtension = file.name.split('.').pop()?.toLowerCase();

    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        let parsedData: BMSPoint[] = [];

        if (fileExtension === 'csv') {
          parsedData = parseCSV(content);
        } else if (fileExtension === 'json') {
          parsedData = JSON.parse(content);
          
          if (!Array.isArray(parsedData)) {
            throw new Error('JSON must contain an array of points');
          }
        } else {
          throw new Error('Unsupported file format. Please upload CSV or JSON files only.');
        }

        setPoints(parsedData);
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Failed to parse file');
        setPoints([]);
      } finally {
        setIsLoading(false);
      }
    };

    reader.onerror = () => {
      setError('Error reading file');
      setIsLoading(false);
    };

    if (fileExtension === 'csv' || fileExtension === 'json') {
      reader.readAsText(file);
    } else {
      setError('Unsupported file format. Please upload CSV or JSON files only.');
      setIsLoading(false);
    }
  };

  // Parse CSV content
  const parseCSV = (csvText: string): BMSPoint[] => {
    const lines = csvText.split('\n');
    if (lines.length <= 1) {
      throw new Error('CSV file appears to be empty or has only headers');
    }

    const headers = lines[0].split(',').map(header => header.trim());
    
    return lines.slice(1).filter(line => line.trim() !== '').map((line, index) => {
      // Handle potential commas inside quoted values
      const values: string[] = [];
      let isInQuotes = false;
      let currentValue = '';
      
      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') {
          isInQuotes = !isInQuotes;
          currentValue += char;
        } else if (char === ',' && !isInQuotes) {
          values.push(currentValue.trim());
          currentValue = '';
        } else {
          currentValue += char;
        }
      }
      
      // Add the last value
      values.push(currentValue.trim());
      
      // Create point object from CSV values
      const point: Record<string, any> = {};
      
      headers.forEach((header, idx) => {
        const value = values[idx] || '';
        
        // Remove quotes if they completely wrap the value
        let cleanValue = value;
        if (cleanValue.startsWith('"') && cleanValue.endsWith('"') && cleanValue.length >= 2) {
          cleanValue = cleanValue.substring(1, cleanValue.length - 1);
        }
        
        point[header] = cleanValue;
      });
      
      // Ensure minimum fields for BMSPoint
      return {
        id: point.id || point.pointId || `point-${index}`,
        pointName: point.pointName || point.objectName || '',
        pointType: point.pointType || point.objectType || '',
        unit: point.unit || '',
        description: point.description || '',
        deviceType: point.deviceType || '',
        deviceId: point.deviceId || ''
      } as BMSPoint;
    });
  };

  // Load data when component mounts
  useEffect(() => {
    // Set loading to false initially
    setIsLoading(false);
  }, []);
  
  // Update table data when pagination changes
  useEffect(() => {
    if (hotInstanceRef.current) {
      hotInstanceRef.current.loadData(getPagedData());
    }
  }, [currentPage, pageSize, points.length]);

  // Map points to EnOS using backend enos.json definitions
  const handleMapPoints = async () => {
    if (points.length === 0) {
      setError('Please upload points data first');
      return;
    }

    try {
      setIsMapping(true);
      setError(null);
      
      console.log(`Sending ${points.length} points to backend for EnOS mapping using AI`);

      const response = await bmsClient.mapPointsToEnOS(points, {
        targetSchema: 'enos',
        matchingStrategy: 'ai'
      }) as MapPointsResponse;
      
      if (response.success && response.mappings && response.mappings.length > 0) {
        // Use the mappings directly from the API response
        const tableData = response.mappings.map(mapping => ({
          id: mapping.pointId,
          deviceType: mapping.deviceType,
          deviceId: mapping.deviceId,
          pointName: mapping.pointName,
          pointType: mapping.pointType || '',
          unit: mapping.unit || '',
          description: mapping.error || '',  // Use error message as description if available
          enosPoint: mapping.enosPoint,
          confidence: mapping.confidence,
          status: mapping.status
        }));
        
        setPoints(tableData);
        console.log(`Mapped ${tableData.length} points successfully`);
        
        // Display mapping statistics
        const stats = response.stats;
        console.log(`Mapping stats: Total=${stats.total}, Mapped=${stats.mapped}, Errors=${stats.errors}`);
        
        if (stats.errors > 0) {
          setError(`${stats.errors} point(s) could not be mapped. Check the status column for details.`);
        }
      } else {
        throw new Error(response.error || 'Failed to map points with backend service');
      }
    } catch (err) {
      console.error('EnOS mapping error:', err);
      setError(err instanceof Error ? err.message : 'Failed to map points to EnOS');
    } finally {
      setIsMapping(false);
    }
  };

  // Export mappings to CSV and apply to EnOS
  const exportMappingsToCSV = async () => {
    if (mappings.length === 0) {
      setError('No mappings to export');
      return;
    }

    try {
      setIsExporting(true);
      setError(null);

      const filename = selectedFile ? selectedFile.name.replace(/\.[^/.]+$/, '') + '_mapped' : 'points_mapping';
      setFilename(filename);

      // Convert our PointMapping objects to the format expected by the API
      const mappingData = mappings.map(mapping => ({
        enosEntity: mapping.enosEntity,
        enosPoint: mapping.enosPoint,
        rawPoint: mapping.rawPoint,
        rawUnit: mapping.rawUnit || '',
        rawFactor: mapping.rawFactor || 1
      }));

      // First, save the mapping to CSV
      const saveResponse = await bmsClient.saveMappingToCSV(mappingData, filename);

      if (!saveResponse.success) {
        throw new Error(saveResponse.error || 'Failed to save mappings to CSV');
      }

      // Then, export to EnOS
      const exportResponse = await bmsClient.exportMappingToEnOS(mappingData);
      
      if (!exportResponse.success) {
        throw new Error(exportResponse.error || 'Failed to apply mappings to EnOS');
      }

      // Create a download link for the CSV
      if (saveResponse.filepath) {
        const downloadUrl = bmsClient.getFileDownloadURL(saveResponse.filepath);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.setAttribute('download', `${filename}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
      
      // Show success message
      console.log(`Mappings exported to CSV and applied to EnOS successfully`);
      setError(null);
    } catch (err) {
      console.error('Export error:', err);
      setError(err instanceof Error ? err.message : 'Failed to export mappings');
    } finally {
      setIsExporting(false);
    }
  };

  // Get table columns and settings
  const getSettings = (): GridSettings => {
    return {
      data: getPagedData(),
      rowHeaders: true,
      colHeaders: [
        'Device Type',
        'Device ID',
        'Point Name',
        'Point Type',
        'Unit',
        'Present Value',
        'Description',
        'Object Type',
        'Object Instance',
        'EnOS Point',
        'Confidence',
        'Status',
        'Error Message'
      ],
      columns: [
        { data: 'deviceType', readOnly: true },
        { data: 'deviceId', readOnly: true },
        { data: 'pointName', readOnly: true },
        { data: 'pointType', readOnly: true },
        { data: 'unit', readOnly: true },
        { 
          data: 'presentValue',
          readOnly: true,
          renderer: (instance, td, row, col, prop, value, cellProperties) => {
            td.innerHTML = value !== undefined ? String(value) : '-';
            return td;
          }
        },
        { data: 'description', readOnly: true },
        { data: 'objectType', readOnly: true },
        { data: 'objectInst', readOnly: true },
        { 
          data: 'enosPoint',
          readOnly: true,
          renderer: (instance, td, row, col, prop, value, cellProperties) => {
            if (!value) {
              td.innerHTML = '<span class="unmapped">Not mapped</span>';
              return td;
            }
            td.innerHTML = `<span class="mapped-point">${value}</span>`;
            return td;
          }
        },
        { 
          data: 'confidence',
          readOnly: true,
          renderer: (instance, td, row, col, prop, value, cellProperties) => {
            const confidence = parseFloat(value);
            if (isNaN(confidence)) {
              td.innerHTML = '-';
              return td;
            }
            const percentage = (confidence * 100).toFixed(1);
            const colorClass = confidence >= 0.7 ? 'high-confidence' : 
                             confidence >= 0.4 ? 'medium-confidence' : 
                             'low-confidence';
            td.innerHTML = `<span class="confidence-score ${colorClass}">${percentage}%</span>`;
            return td;
          }
        },
        {
          data: 'status',
          readOnly: true,
          renderer: (instance, td, row, col, prop, value, cellProperties) => {
            const statusClass = value === 'mapped' ? 'status-mapped' : 'status-error';
            td.innerHTML = `<span class="status-indicator ${statusClass}">${value}</span>`;
            return td;
          }
        },
        {
          data: 'error',
          readOnly: true,
          renderer: (instance, td, row, col, prop, value, cellProperties) => {
            if (!value) {
              td.innerHTML = '-';
              return td;
            }
            td.innerHTML = `<span class="error-message-cell">${value}</span>`;
            return td;
          }
        }
      ],
      stretchH: 'all',
      autoWrapRow: true,
      height: 'auto',
      licenseKey: 'non-commercial-and-evaluation',
      columnSorting: true,
      filters: true,
      dropdownMenu: true,
      hiddenColumns: {
        indicators: true
      },
      afterGetColHeader: function(col: number, TH: HTMLTableCellElement) {
        const menu = document.createElement('div');
        menu.className = 'column-menu';
        menu.innerHTML = '⋮';
        menu.addEventListener('click', function(e) {
          e.stopPropagation();
          if (hotInstanceRef.current) {
            const columnData = hotInstanceRef.current.getDataAtCol(col);
            const uniqueValues = [...new Set(columnData)].filter(Boolean);
            
            // Create filter menu
            const filterMenu = document.createElement('div');
            filterMenu.className = 'column-filter-menu';
            filterMenu.style.position = 'absolute';
            filterMenu.style.right = '0';
            filterMenu.style.top = '100%';
            filterMenu.style.backgroundColor = '#fff';
            filterMenu.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
            filterMenu.style.borderRadius = '4px';
            filterMenu.style.padding = '8px 0';
            filterMenu.style.zIndex = '1000';

            // Add filter options
            uniqueValues.forEach(value => {
              const option = document.createElement('div');
              option.className = 'filter-option';
              option.textContent = String(value);
              option.addEventListener('click', () => {
                if (hotInstanceRef.current) {
                  hotInstanceRef.current.getPlugin('filters').addCondition(col, 'eq', [value]);
                  hotInstanceRef.current.getPlugin('filters').filter();
                }
              });
              filterMenu.appendChild(option);
            });

            // Add clear filter option
            const clearOption = document.createElement('div');
            clearOption.className = 'filter-option clear-filter';
            clearOption.textContent = 'Clear filter';
            clearOption.addEventListener('click', () => {
              if (hotInstanceRef.current) {
                hotInstanceRef.current.getPlugin('filters').clearConditions(col);
                hotInstanceRef.current.getPlugin('filters').filter();
              }
            });
            filterMenu.appendChild(clearOption);

            // Show menu
            TH.appendChild(filterMenu);

            // Close menu when clicking outside
            const closeMenu = (e: MouseEvent) => {
              if (!filterMenu.contains(e.target as Node)) {
                filterMenu.remove();
                document.removeEventListener('click', closeMenu);
              }
            };
            document.addEventListener('click', closeMenu);
          }
        });
        TH.appendChild(menu);
      }
    };
  };

  // Calculate total pages for pagination
  const totalPoints = points.length;
  const totalPages = Math.max(1, Math.ceil(totalPoints / pageSize));

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(Math.min(Math.max(1, page), totalPages));
    if (hotInstanceRef.current) {
      hotInstanceRef.current.loadData(getPagedData());
    }
  };


  // Update page size
  const handlePageSizeChange = (size: number) => {
    setPageSize(size);
    setCurrentPage(1);
    if (hotInstanceRef.current) {
      hotInstanceRef.current.loadData(getPagedData());
    }
  };
  
  // Helper to get the current page of data
  const getPagedData = () => {
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return points.slice(startIndex, endIndex);
  };

  return (
    <div className="map-points-container">
      <h1>Map Points to EnOS</h1>
      
      <Card className="upload-card">
        <h2>Upload Points</h2>
        <div className="file-upload-container">
          <input
            type="file"
            id="file-upload"
            onChange={handleFileUpload}
            accept=".csv,.json"
            disabled={isLoading}
            className="file-upload-input"
          />
          <label htmlFor="file-upload" className="file-upload-label">
            {isLoading ? 'Loading...' : 'Choose File'}
          </label>
          <span className="file-name">
            {selectedFile ? selectedFile.name : 'No file selected'}
          </span>
        </div>
        {error && <div className="error-message">{error}</div>}
      </Card>

      {points.length > 0 && (
        <Card className="points-card">
          <div className="card-header">
            <h2>Points Data</h2>
            <div className="action-buttons">
              <button
                className="primary-button"
                onClick={handleMapPoints}
                disabled={isMapping || points.length === 0}
              >
                {isMapping ? 'Mapping...' : 'Map to EnOS'}
              </button>
              <button
                className="secondary-button"
                onClick={exportMappingsToCSV}
                disabled={isExporting || mappings.length === 0}
              >
                {isExporting ? 'Exporting...' : 'Export & Apply to EnOS'}
              </button>
            </div>
          </div>

          <div className="pagination-container">
            <div className="pagination-controls">
              <label>
                Show
                <select
                  value={pageSize}
                  onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                  disabled={isLoading}
                >
                  <option value="10">10</option>
                  <option value="25">25</option>
                  <option value="50">50</option>
                  <option value="100">100</option>
                </select>
                entries
              </label>
            </div>
            <div className="pagination-buttons">
              <button
                onClick={() => handlePageChange(1)}
                disabled={currentPage === 1}
                className="pagination-button"
              >
                First
              </button>
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="pagination-button"
              >
                Previous
              </button>
              <span className="pagination-info">
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="pagination-button"
              >
                Next
              </button>
              <button
                onClick={() => handlePageChange(totalPages)}
                disabled={currentPage === totalPages}
                className="pagination-button"
              >
                Last
              </button>
            </div>
          </div>

          <div className="table-container">
            <HotTable
              ref={(ref: any) => { 
                if (ref) {
                  hotInstanceRef.current = ref.hotInstance;
                }
              }}
              settings={getSettings()}
            />
          </div>
        </Card>
      )}
    </div>
  );
};

export default MapPoints;