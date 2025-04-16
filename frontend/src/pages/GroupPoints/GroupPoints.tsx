import * as React from 'react';
import { Card } from '../../components';
import { HotTable } from '@handsontable/react';
import { registerAllModules } from 'handsontable/registry';
import type { GridSettings } from 'handsontable/settings';
import 'handsontable/dist/handsontable.full.css';
import './GroupPoints.css';
import { BMSPointRaw } from '../../types/apiTypes';
import { api } from '../../api/apiClient';

// Register all Handsontable modules
registerAllModules();

interface Point extends BMSPointRaw {
  deviceType?: string;
  deviceId?: string;
  objectType?: string;
  otDeviceInst?: string;
  objectInst?: string;
  objectIdentifier?: string;
  objectName?: string;
  deviceInstance?: string;
  deviceAddress?: string;
  source?: string;
  assetId?: string;
  presentValue?: string | number;
  covIncrement?: string | number;
}

// Define the server response types
interface AIGroupingResponse {
  success: boolean;
  error?: string;
  grouped_points?: {
    [deviceType: string]: {
      [deviceId: string]: string[];
    };
  };
}

const GroupPoints: React.FC = () => {
  const [points, setPoints] = React.useState<Point[]>([]);
  const [isLoading, setIsLoading] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);
  const [fileType, setFileType] = React.useState<string | null>(null);
  const [currentPage, setCurrentPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(10);
  const [isGrouping, setIsGrouping] = React.useState(false);
  const [isExporting, setIsExporting] = React.useState(false);
  const hotTableRef = React.useRef<any>(null);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setIsLoading(true);
    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    setFileType(fileExtension || null);

    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        let parsedData: Point[] = [];

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

        // Validation and cleanup
        parsedData = parsedData.map((point, index) => ({
          id: point.id || point.pointId || `point-${index}`,
          pointId: point.pointId || '',
          pointName: point.pointName || point.objectName || '',
          pointType: point.pointType || point.objectType || '',
          objectType: point.objectType || point.pointType || '',
          objectName: point.objectName || point.pointName || '',
          objectInst: point.objectInst || '',
          objectIdentifier: point.objectIdentifier || '',
          otDeviceInst: point.otDeviceInst || point.deviceInstance || '',
          deviceInstance: point.deviceInstance || point.otDeviceInst || '',
          deviceAddress: point.deviceAddress || '',
          presentValue: point.presentValue || '',
          unit: point.unit || '',
          covIncrement: point.covIncrement || '',
          description: point.description || '',
          timestamp: point.timestamp || '',
          assetId: point.assetId || '',
          source: point.source || '',
          deviceType: point.deviceType || '',
          deviceId: point.deviceId || ''
        }));

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

  const parseCSV = (csvText: string): Point[] => {
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
      
      // Generate id if missing
      if (!point.id) {
        point.id = point.pointId || `point-${index}`;
      }
      
      return point as Point;
    });
  };

  const getColumnsArray = (): string[] => {
    return [
      'pointName',
      'pointType',
      'objectType',
      'presentValue',
      'unit',
      'description',
      'deviceInstance',
      'deviceAddress',
      'otDeviceInst',
      'objectInst',
      'objectIdentifier',
      'objectName',
      'covIncrement',
      'timestamp',
      'assetId',
      'source',
      'pointId',
      'id',
      'deviceType',
      'deviceId'
    ];
  };

  const getColumns = () => {
    const priorityColumns = getColumnsArray();
    return priorityColumns.map(key => ({
      data: key as keyof Point,
      title: key.charAt(0).toUpperCase() + key.slice(1),
      width: key === 'objectIdentifier' ? 180 : undefined,
    }));
  };

  const paginate = (items: any[], page: number, pageSize: number) => {
    const startIndex = (page - 1) * pageSize;
    const endIndex = Math.min(startIndex + pageSize, items.length);
    return items.slice(startIndex, endIndex);
  };

  const totalPages = Math.ceil(points.length / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, points.length);
  const currentPageData = points.slice(startIndex, endIndex);

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  const handlePageSizeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const newSize = Number(event.target.value);
    setPageSize(newSize);
    setCurrentPage(1);
  };

  const settings: GridSettings = {
    data: currentPageData,
    columns: getColumns(),
    colHeaders: true,
    rowHeaders: true,
    height: 'auto',
    width: '100%',
    licenseKey: 'non-commercial-and-evaluation',
    stretchH: 'all' as const,
    autoWrapRow: true,
    manualRowResize: true,
    manualColumnResize: true,
    filters: true,
    dropdownMenu: true,
    multiColumnSorting: true,
    columnSorting: true,
    readOnly: true
  };

  const exportToCSV = () => {
    try {
      setIsExporting(true);
      setError(null);
      
      // Get column headers as strings
      const columnHeaders = getColumnsArray();
      
      // Create CSV header
      let csvContent = columnHeaders.join(',') + '\n';
      
      // Add rows
      points.forEach(point => {
        const row = columnHeaders.map(columnKey => {
          const value = point[columnKey as keyof Point];
          // Handle values that might contain commas or quotes
          if (value === null || value === undefined) return '';
          const stringValue = String(value);
          return stringValue.includes(',') || stringValue.includes('"') ? 
            `"${stringValue.replace(/"/g, '""')}"` : stringValue;
        });
        csvContent += row.join(',') + '\n';
      });
      // Create downloadable link
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      
      // Set filename with date and indication of grouping
      const date = new Date().toISOString().split('T')[0];
      const filename = `grouped-points-${date}.csv`;
      
      link.setAttribute('href', url);
      link.setAttribute('download', filename);
      link.style.display = 'none';
      document.body.appendChild(link);
      
      link.click();
      
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('CSV Export error:', err);
      setError(err instanceof Error ? err.message : 'Failed to export data to CSV');
    } finally {
      setIsExporting(false);
    }
  };

  /**
   * Exports point data to EnOS format with appropriate device-specific prefixes
   * Generates point names in format: PREFIX_raw_pointname
   * Example: PUMP_raw_status_value
   */
  const exportToEnOS = () => {
    try {
      setIsExporting(true);
      setError(null);
      
      // Format points for EnOS export with mappings
      const enosExportData = points.map(point => {
        // Initialize variables with safe defaults
        let enosPointName = "";
        let mappingStatus = "unmapped";
        
        // Extract and normalize device type (safely handle undefined)
        const deviceType = (point.deviceType || "").toUpperCase().trim();
        let prefix = "UNKNOWN";
        
        // Standard device type to prefix mapping
        // This ensures consistent naming across the application
        const prefixMap: {[key: string]: string} = {
          // Air handling units
          "AHU": "AHU",
          
          // Fan coil units
          "FCU": "FCU", 
          "FAN COIL UNIT": "FCU",
          
          // Chillers - standardized to CHI prefix
          "CHILLER": "CHI",
          "CH": "CHI",
          
          // All pump types - standardized to PUMP prefix
          "PUMP": "PUMP",
          "CWP": "PUMP",
          "CHWP": "PUMP",
          "CHILLED WATER PUMP": "PUMP",
          "HWP": "PUMP",
          "HOT WATER PUMP": "PUMP",
          "CONDENSER WATER PUMP": "PUMP",
          
          // Cooling towers
          "CT": "CT",
          "COOLING TOWER": "CT",
          
          // Other standard device types
          "VAV": "VAV",
          "VRF": "VRF"
        };
        
        // Hierarchical prefix determination logic:
        // 1. First try exact match in the prefixMap
        // 2. Then check for partial string matches for key device types
        // 3. Finally fall back to a substring approach
        if (prefixMap[deviceType]) {
          // Direct match from the mapping table
          prefix = prefixMap[deviceType];
        } else {
          // Pattern matching for known device types that might have variations
          // For example: "CHWP-01" or "Primary CHWP" should map to "PUMP"
          const isPump = /(PUMP|CWP|CHWP|HWP)/i.test(deviceType);
          const isChiller = /(CHILL|CH-)/i.test(deviceType);
          
          if (isPump) {
            prefix = "PUMP";
          } else if (isChiller) {
            prefix = "CHI";
          } else if (deviceType.length > 0) {
            // Last resort: use first 3 chars if available
            // Safely handle shorter strings with Math.min
            prefix = deviceType.substring(0, Math.min(3, deviceType.length));
          }
        }
        
        // Safe handling of point name
        const pointName = (point.pointName || "").toString();
        
        // Normalize point name for use as suffix:
        // 1. Replace spaces and dots with underscores
        // 2. Remove any non-alphanumeric characters
        // 3. Convert to lowercase for consistency
        let pointSuffix = pointName
          .replace(/[\s.]/g, '_')
          .replace(/[^a-zA-Z0-9_]/g, '')
          .toLowerCase();
        
        // Prevent excessively long point names
        const MAX_SUFFIX_LENGTH = 30;
        if (pointSuffix.length > MAX_SUFFIX_LENGTH) {
          pointSuffix = pointSuffix.substring(0, MAX_SUFFIX_LENGTH);
        }
        
        // Only create a valid EnOS point name if we have both prefix and suffix
        if (prefix && pointSuffix) {
          enosPointName = `${prefix}_raw_${pointSuffix}`;
          mappingStatus = "unmapped_exported";
        }
        
        // Create export record with validated fields
        return {
          "pointId": point.pointId || "",
          "pointName": point.pointName || "",
          "deviceId": point.deviceId || "",
          "deviceType": point.deviceType || "UNKNOWN",
          "pointType": point.pointType || "",
          "unit": point.unit || "",
          "enosPoint": enosPointName,
          "status": mappingStatus,
          "confidence": 0.1
        };
      });
      
      // Create CSV header for EnOS format
      const enosColumns = [
        "pointId", "pointName", "deviceId", "deviceType", 
        "pointType", "unit", "enosPoint", "status", "confidence"
      ];
      
      let csvContent = enosColumns.join(',') + '\n';
      
      // Add rows
      enosExportData.forEach(record => {
        const row = enosColumns.map(columnKey => {
          const value = record[columnKey as keyof typeof record];
          // Handle values that might contain commas or quotes
          if (value === null || value === undefined) return '';
          const stringValue = String(value);
          return stringValue.includes(',') || stringValue.includes('"') ? 
            `"${stringValue.replace(/"/g, '""')}"` : stringValue;
        });
        csvContent += row.join(',') + '\n';
      });
      
      // Create downloadable link
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      
      // Set filename with date
      const date = new Date().toISOString().split('T')[0];
      const filename = `enos-export-${date}.csv`;
      
      link.setAttribute('href', url);
      link.setAttribute('download', filename);
      link.style.display = 'none';
      document.body.appendChild(link);
      
      link.click();
      
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      // Show success message
      console.log(`Exported ${enosExportData.length} points to EnOS format`);
      
    } catch (err) {
      console.error('EnOS Export error:', err);
      setError(err instanceof Error ? err.message : 'Failed to export data to EnOS format');
    } finally {
      setIsExporting(false);
    }
  };

  const handleAIGrouping = async () => {
    if (points.length === 0) {
      setError('Please upload points data first');
      return;
    }

    try {
      setIsGrouping(true);
      setError(null);

      // Extract point names from the points array
      const pointNames = points.map(point => point.pointName);

      // Use the API client with the correct endpoint path
      const serverResponse = await api.post<AIGroupingResponse>('api/bms/ai-grouping', { points: pointNames });
      console.log('Server response:', serverResponse);

      if (serverResponse.success && serverResponse.grouped_points) {
        // Transform the grouped points back to our format
        const transformedPoints = points.map(point => {
          // Find which group this point belongs to
          const groupedPoints = serverResponse.grouped_points || {};
          for (const [deviceType, devices] of Object.entries(groupedPoints)) {
            for (const [deviceId, devicePoints] of Object.entries(devices)) {
              if (Array.isArray(devicePoints) && devicePoints.includes(point.pointName)) {
                return {
                  ...point,
                  deviceType,
                  deviceId
                };
              }
            }
          }
          return point;
        });

        setPoints(transformedPoints);
        setCurrentPage(1);
      } else {
        throw new Error(serverResponse.error || 'Invalid response format from AI grouping');
      }
    } catch (err) {
      console.error('AI Grouping error:', err);
      setError(err instanceof Error ? err.message : 'Failed to perform AI grouping');
    } finally {
      setIsGrouping(false);
    }
  };

  return (
    <div className="group-points-page">
      <h1>Group Points</h1>
      
      <Card className="upload-card">
        <h2>Upload Points File</h2>
        <div className="file-upload-container">
          <input 
            type="file" 
            accept=".csv,.json" 
            onChange={handleFileUpload}
            id="file-upload"
            className="file-input"
          />
          <label htmlFor="file-upload" className="file-upload-label">
            Choose CSV or JSON file
          </label>
          <span className="file-format-info">
            Supported formats: CSV, JSON
          </span>
        </div>
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
        
        {isLoading && (
          <div className="loading-indicator">
            Loading...
          </div>
        )}
      </Card>

      {points.length > 0 && (
        <Card className="points-table-card">
          <div className="table-header">
            <h2>
              Points Data 
              {fileType && <span className="file-type-badge">{fileType.toUpperCase()}</span>}
              <span className="points-count">{points.length} points</span>
            </h2>
            <div className="table-actions">
              <button
                onClick={handleAIGrouping}
                disabled={isGrouping}
                className="ai-grouping-button"
              >
                {isGrouping ? (
                  <>
                    <span className="spinner"></span>
                    AI Grouping...
                  </>
                ) : (
                  'AI Grouping'
                )}
              </button>
              <button
                onClick={exportToCSV}
                disabled={isExporting || points.length === 0}
                className="export-button"
              >
                {isExporting ? (
                  <>
                    <span className="spinner"></span>
                    Exporting...
                  </>
                ) : (
                  'Export CSV'
                )}
              </button>
              <button
                onClick={exportToEnOS}
                disabled={isExporting || points.length === 0}
                className="export-button"
              >
                {isExporting ? (
                  <>
                    <span className="spinner"></span>
                    Exporting to EnOS...
                  </>
                ) : (
                  'Export to EnOS'
                )}
              </button>
            </div>
          </div>
          
          <div className="pagination-controls">
            <div className="page-size-selector">
              <label htmlFor="page-size">Items per page:</label>
              <select
                id="page-size"
                value={pageSize}
                onChange={handlePageSizeChange}
                className="page-size-select"
              >
                {[10, 20, 50, 100].map(size => (
                  <option key={size} value={size}>{size}</option>
                ))}
              </select>
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
              ref={hotTableRef}
              settings={settings}
            />
          </div>
        </Card>
      )}
    </div>
  );
};

export default GroupPoints;