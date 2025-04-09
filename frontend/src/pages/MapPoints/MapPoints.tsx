import React, { useState, useEffect, useRef } from 'react';
import { BMSPoint, PointMapping } from '../../types/apiTypes';
import { MapPointsToEnOSResponse, MappingConfig } from '../../api/bmsClient';
import './MapPoints.css';
import Card from '../../components/Card';
import MappingControls from '../../components/MappingControls';
import { useMappingContext } from '../../contexts/MappingContext';
import useBMSClient from '../../hooks/useBMSClient';
import useEnhancedMapping from '../../hooks/useEnhancedMapping';
import { HotTable } from '@handsontable/react';
import { registerAllModules } from 'handsontable/registry';
import type { GridSettings } from 'handsontable/settings';
import 'handsontable/dist/handsontable.full.css';

// Register all Handsontable modules
registerAllModules();

/**
 * MapPoints page component
 * Allows users to map BMS points to EnOS schema
 */
const MapPoints: React.FC = () => {
  const [points, setPoints] = useState<BMSPoint[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isMapping, setIsMapping] = useState<boolean>(false);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [isImproving, setIsImproving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  
  // Reference to track component mounting state
  const isMountedRef = useRef<boolean>(true);
  const hotTableRef = useRef<any>(null);
  
  // Get context and hooks
  const { 
    mappings, 
    setMappings, 
    setFilename,
    setRawPoints,
    setMappedPoints,
    setDeviceTypes,
    updateBatchProgress,
    setQualityResults
  } = useMappingContext();
  
  const bmsClient = useBMSClient();
  
  // Use our enhanced mapping hook
  const { 
    isAnalyzing,
    isImproving: hookIsImproving,
    qualityResults,
    batchProgress,
    qualityStatistics,
    analyzeQuality,
    improveMappingResults,
    detectDeviceTypes
  } = useEnhancedMapping();

  // Local device types state
  const [deviceTypesLocal, setDeviceTypesLocal] = useState<string[]>([]);
  const [activeDeviceTypeFilter, setActiveDeviceTypeFilter] = useState<string | null>(null);
  
  // Handler for device type filtering
  const handleFilterByDeviceType = (deviceType: string | null) => {
    setActiveDeviceTypeFilter(deviceType);
    // Filter points by device type if needed
    if (deviceType) {
      const filtered = points.filter(point => point.deviceType === deviceType);
      // Apply filtering logic here
    } else {
      // Reset to show all points
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

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
    setCurrentPage(1); // Reset to first page when loading new file

    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        let parsedData: BMSPoint[] = [];

        if (fileExtension === 'csv') {
          parsedData = parseCSV(content);
        } else if (fileExtension === 'json') {
          parsedData = parseJSON(content);
        } else {
          throw new Error(`Unsupported file format: ${fileExtension}`);
        }

        // Detect device types from the data
        const detectedTypes = detectDeviceTypes(parsedData);
        setDeviceTypesLocal(detectedTypes);
        setDeviceTypes(detectedTypes);

        setPoints(parsedData);
        setRawPoints(parsedData);
        setFilename(file.name);
        setMappings([]);
      } catch (error) {
        console.error("Error processing file:", error);
        setError(error instanceof Error ? error.message : 'Error processing file');
      } finally {
        setIsLoading(false);
      }
    };

    reader.onerror = () => {
      setIsLoading(false);
      setError('Error reading file');
    };

    reader.readAsText(file);
  };

  // Helper function to convert CSV to array of objects
  function parseCSV(csvContent: string): BMSPoint[] {
    const lines = csvContent.trim().split('\n');
    if (lines.length < 2) {
      throw new Error('CSV file must contain at least a header row and one data row');
    }

    // Helper function to parse a single CSV line respecting quotes
    const parseCSVLine = (line: string): string[] => {
      const fields: string[] = [];
      let currentField = '';
      let inQuotes = false;

      for (let i = 0; i < line.length; i++) {
        const char = line[i];

        if (char === '"') {
          // Handle quotes: check for escaped quotes ("")
          if (inQuotes && line[i + 1] === '"') {
            currentField += '"';
            i++; // Skip the second quote of the pair
          } else {
            inQuotes = !inQuotes; // Toggle quote status
          }
        } else if (char === ',' && !inQuotes) {
          // Comma outside quotes signals the end of a field
          fields.push(currentField.trim());
          currentField = ''; // Reset for the next field
        } else {
          // Add character to the current field
          currentField += char;
        }
      }
      // Add the last field after the loop finishes
      fields.push(currentField.trim());
      return fields;
    };

    // Parse header row using the new logic
    const headers = parseCSVLine(lines[0]);

    // Validate required headers
    const requiredHeaders = ['deviceType', 'deviceId', 'pointName'];
    for (const required of requiredHeaders) {
      if (!headers.includes(required)) {
        throw new Error(`CSV missing required header: ${required}`);
      }
    }

    const pointsData: BMSPoint[] = [];

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue; // Skip empty lines

      // Parse data row using the new logic
      const values = parseCSVLine(line);

      // Check column count AFTER parsing respecting quotes
      if (values.length !== headers.length) {
        console.warn(`Line ${i + 1} has ${values.length} columns after parsing, expected ${headers.length}. Skipping. Original line: "${line}"`);
        continue;
      }

      const point: any = {};
      headers.forEach((header, index) => {
        // Remove surrounding quotes from the value if they exist ONLY at the start/end
        let value = values[index];
        if (value.startsWith('"') && value.endsWith('"')) {
           // Be careful not to remove quotes if they are part of the actual data or escaped
           // A simple check: only remove if quotes are exact start/end and not escaped internally
           // (This basic removal might need refinement for complex CSVs, but covers common cases)
           if (!value.slice(1, -1).includes('"')) { // Avoid removing if internal quotes exist
                value = value.slice(1, -1);
           }
           // Handle escaped quotes "" -> "
           value = value.replace(/""/g, '"');
        }
        point[header] = value;
      });

      // Generate a unique ID if not present
      if (!point.id) {
        point.id = `point-${i}-${Date.now()}`;
      }

      pointsData.push(point as BMSPoint);
    }

    // Add a check to see if any data was actually parsed
    if (pointsData.length === 0 && lines.length > 1) {
      console.error("CSV parsing finished, but no valid data rows were processed. Check console warnings for skipped lines.");
      // Optionally throw an error or set an error state here
      // setError("Failed to parse valid data rows from the CSV. Please check file format and console warnings.");
    }


    return pointsData;
  }

  // Helper function to parse JSON point data
  function parseJSON(jsonContent: string): BMSPoint[] {
    const data = JSON.parse(jsonContent);
    
    if (Array.isArray(data)) {
      return data.map((item, index) => {
        if (!item.id) {
          item.id = `point-${index}-${Date.now()}`;
        }
        return item as BMSPoint;
      });
    } else {
      throw new Error('JSON data must be an array of points');
    }
  }

  // Calculate total pages
  const totalPages = Math.ceil(points.length / pageSize);
  
  // Get current page data
  const getCurrentPageData = () => {
    // Log input state and calculated values for debugging pagination
    console.log(`getCurrentPageData: total points = ${points.length}, currentPage = ${currentPage}, pageSize = ${pageSize}`);
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const slicedData = points.slice(startIndex, endIndex);
    console.log(` -> calculated startIndex = ${startIndex}, endIndex = ${endIndex}, returning ${slicedData.length} points`);
    return slicedData;
  };
  
  // Prepare HandsOnTable data and settings
  const getColumns = () => {
    return [
      { data: 'deviceType', title: 'Device Type', readOnly: true },
      { data: 'deviceId', title: 'Device ID', readOnly: true },
      { data: 'pointName', title: 'Point Name', readOnly: true },
      { data: 'pointType', title: 'Point Type', readOnly: true },
      { data: 'enosPoint', title: 'EnOS Point', readOnly: true },
      { data: 'status', title: 'Status', readOnly: true },
      { data: 'description', title: 'Info', readOnly: true },
    ];
  };
  
  const hotSettings: GridSettings = {
    data: getCurrentPageData(),
    columns: getColumns(),
    colHeaders: true,
    rowHeaders: true,
    height: 'auto',
    width: '100%',
    licenseKey: 'non-commercial-and-evaluation',
    stretchH: 'all',
    autoWrapRow: true,
    manualRowResize: true,
    manualColumnResize: true,
    filters: true,
    dropdownMenu: true,
    multiColumnSorting: true,
    columnSorting: true,
    readOnly: true
  };

  // Handle page change
  const handlePageChange = (page: number) => {
    if (page < 1) page = 1;
    // Ensure totalPages is calculated correctly before comparing
    const calculatedTotalPages = Math.ceil(points.length / pageSize);
    if (page > calculatedTotalPages) page = calculatedTotalPages;
    setCurrentPage(page);
    
    // Remove manual update - React re-render will handle it via hotSettings
    // setTimeout(() => {
    //   if (hotTableRef.current && hotTableRef.current.hotInstance) {
    //     hotTableRef.current.hotInstance.loadData(getCurrentPageData());
    //   }
    // }, 0);
  };

  // Handle page size change
  const handlePageSizeChange = (size: number) => {
    setPageSize(size);
    setCurrentPage(1); // Reset to first page when size changes
    
    // Remove manual update - React re-render will handle it via hotSettings
    // setTimeout(() => {
    //   if (hotTableRef.current && hotTableRef.current.hotInstance) {
    //     hotTableRef.current.hotInstance.loadData(getCurrentPageData());
    //   }
    // }, 0);
  };

  // Handle mapping points
  const handleMapPoints = async () => {
    if (points.length === 0) {
      setError('No points to map');
      return;
    }

    setIsMapping(true);
    setError(null);

    try {
      // Call the API to map points
      const response = await bmsClient.mapPointsToEnOS(points, {
        includeDeviceContext: true,
        matchingStrategy: 'ai'
      });

      if (response && response.mappings) {
        // Convert the response mappings to BMSPoints
        const mappedPoints: BMSPoint[] = response.mappings.map(mapping => ({
          id: mapping.mapping?.pointId || mapping.pointId || '',
          pointName: mapping.original?.pointName || mapping.pointName || '',
          pointType: mapping.original?.pointType || mapping.pointType || '',
          unit: mapping.original?.unit || mapping.unit || '',
          description: mapping.mapping?.error || '',
          deviceType: mapping.original?.deviceType || mapping.deviceType || '',
          deviceId: mapping.original?.deviceId || mapping.deviceId || '',
          enosPoint: mapping.mapping?.enosPoint || mapping.enosPoint || '',
          status: mapping.mapping?.status || mapping.status || 'pending'
        }));

        setPoints(mappedPoints);
        setMappedPoints(mappedPoints);
        
        // Update the HandsOnTable with new data
        if (hotTableRef.current && hotTableRef.current.hotInstance) {
          hotTableRef.current.hotInstance.loadData(mappedPoints.slice(0, pageSize));
        }
        
        // Analyze mapping quality
        const qualityAnalysis = await analyzeQuality(response);
        setQualityResults(qualityAnalysis);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to map points');
    } finally {
      setIsMapping(false);
    }
  };

  const handleImproveMapping = async () => {
    if (!qualityResults || !qualityResults.mappingId) {
      return;
    }
    
    setIsImproving(true);
    try {
      // Call the improve mapping function from our hook
      const response = await improveMappingResults(qualityResults.mappingId, {
        qualityFilter: 'all', // 改为'all'，映射所有点位，不管质量如何
        includeDeviceContext: true,
      });
      
      // Update points with improved results
      if (response && response.mappings) {
        const improvedPoints: BMSPoint[] = response.mappings.map(mapping => ({
          id: mapping.mapping?.pointId || mapping.pointId || '',
          pointName: mapping.original?.pointName || mapping.pointName || '',
          pointType: mapping.original?.pointType || mapping.pointType || '',
          unit: mapping.original?.unit || mapping.unit || '',
          description: mapping.mapping?.error || '',
          deviceType: mapping.original?.deviceType || mapping.deviceType || '',
          deviceId: mapping.original?.deviceId || mapping.deviceId || '',
          enosPoint: mapping.mapping?.enosPoint || mapping.enosPoint || '',
          status: mapping.mapping?.status || mapping.status || 'pending'
        }));

        setPoints(improvedPoints);
        setMappedPoints(improvedPoints);
        
        // Update the HandsOnTable with new data
        if (hotTableRef.current && hotTableRef.current.hotInstance) {
          hotTableRef.current.hotInstance.loadData(improvedPoints.slice(0, pageSize));
        }
        
        // Re-analyze quality with improved mappings
        const newQualityAnalysis = await analyzeQuality(response);
        setQualityResults(newQualityAnalysis);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to improve mappings');
    } finally {
      setIsImproving(false);
    }
  };

  // Export mappings to CSV
  const exportMappingsToCSV = async () => {
    if (mappings.length === 0) {
      setError('No mappings available to export. Please map points first.');
      return;
    }
    
    setIsExporting(true);
    
    try {
      // Prepare the data for export
      const exportData = mappings.map(mapping => ({
        enosEntity: mapping.deviceType || 'Unknown',
        enosPoint: mapping.enosPoint || '',
        rawPoint: mapping.pointName || '',
        rawUnit: mapping.unit || ''
      }));
      
      // Generate a filename based on the original file and timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
      const filename = `${selectedFile?.name.split('.')[0] || 'mapping'}_${timestamp}.csv`;
      
      // Call the API to export
      const result = await bmsClient.saveMappingToCSV(exportData as unknown as PointMapping[], filename);
      
      if (result && result.success) {
        // Get download URL
        const downloadUrl = bmsClient.getFileDownloadURL(result.filepath || '');
        
        // Create a temporary link and trigger download
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        console.log('Export completed successfully');
      } else {
        throw new Error(result.error || 'Failed to export mappings');
      }
    } catch (error) {
      console.error('Export error:', error);
      setError(error instanceof Error ? error.message : 'Error exporting mappings');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="map-points-page">
      <h1>Map BMS Points to EnOS</h1>
      
      <section className="file-upload-section">
        <Card className="upload-card">
          <h2>Upload Points File</h2>
          <p>Select a CSV or JSON file containing BMS point data.</p>
          
          <div className="file-input-container">
            <input
              type="file"
              accept=".csv,.json"
              onChange={handleFileUpload}
              disabled={isLoading || isMapping}
            />
            <div className="file-info">
              {selectedFile && (
                <span>Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)</span>
              )}
            </div>
          </div>
        </Card>
      </section>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      
      {points.length > 0 && (
        <Card className="points-card">
          <div className="card-header">
            <h2>Points Data</h2>
            <MappingControls
              // Main actions
              deviceTypes={deviceTypesLocal}
              activeDeviceTypeFilter={activeDeviceTypeFilter}
              onFilterByDeviceType={handleFilterByDeviceType}
              onMapPoints={handleMapPoints}
              onImproveMapping={handleImproveMapping}
              onExportMapping={exportMappingsToCSV}
              
              // State indicators
              isLoading={isLoading}
              isMapping={isMapping}
              isImproving={isImproving}
              isExporting={isExporting}
              
              // Batch processing state
              batchProgress={{
                isInBatchMode: batchProgress.isInBatchMode,
                totalBatches: batchProgress.totalBatches,
                completedBatches: batchProgress.completedBatches,
                progress: batchProgress.progress,
                taskId: qualityResults?.mappingId || null
              }}
              
              // Quality assessment
              hasQualityAnalysis={!!qualityResults}
              hasLowQualityMappings={!!qualityResults && (
                (qualityResults.qualitySummary?.poor || 0) + 
                (qualityResults.qualitySummary?.unacceptable || 0) > 0
              )}
              qualityStats={qualityStatistics}
              
              // Point counts
              pointsCount={points.length}
              mappedPointsCount={mappings.length}
            />
          </div>
          
          <div className="table-controls">
            <div className="pagination">
              <button 
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage <= 1}
              >
                Previous
              </button>
              <span>Page {currentPage} of {totalPages}</span>
              <button 
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage >= totalPages}
              >
                Next
              </button>
            </div>
            
            <div className="page-size-selector">
              <label>Items per page:</label>
              <select 
                value={pageSize}
                onChange={(e) => handlePageSizeChange(Number(e.target.value))}
              >
                <option value="10">10</option>
                <option value="25">25</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </select>
            </div>
          </div>
          
          <div className="points-table-container">
            {isLoading ? (
              <div className="loading-indicator">Loading...</div>
            ) : (
              <div className="hot-table-wrapper">
                <HotTable
                  ref={hotTableRef}
                  settings={hotSettings}
                />
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

export default MapPoints;