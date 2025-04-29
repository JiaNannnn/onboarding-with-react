import { useState, useRef } from 'react';
import { BMSPoint } from '../../types/apiTypes';
import { v4 as uuidv4 } from 'uuid';

interface UseFileUploadOptions {
  onSuccess?: (points: BMSPoint[]) => void;
  onError?: (error: string) => void;
}

/**
 * Hook for handling file upload and processing for BMS points
 */
export function useFileUpload(options: UseFileUploadOptions = {}) {
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Helper function to parse CSV lines, handling quoted values
  const parseCSVLine = (line: string): string[] => {
    const result: string[] = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      
      if (char === '"') {
        // Toggle quote state
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        // End of field
        result.push(current.trim());
        current = '';
      } else {
        // Add character to current field
        current += char;
      }
    }
    
    // Add the last field
    result.push(current.trim());
    
    return result;
  };

  // Handle file upload
  const handleFileUpload = (file: File | null) => {
    setUploadError(null);
    
    if (!file) {
      return;
    }
    
    const allowedExtensions = ['.csv', '.json'];
    const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!allowedExtensions.includes(fileExt)) {
      const error = `File type not supported. Please upload a CSV or JSON file.`;
      setUploadError(error);
      if (options.onError) options.onError(error);
      return;
    }
    
    setIsUploading(true);
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const data = e.target?.result as string;
        let json: any[] = [];
        
        if (fileExt === '.csv') {
          // Parse CSV - handle different line endings and quoted values
          const lines = data.split(/\r?\n/).filter(line => line.trim().length > 0);
          
          if (lines.length === 0) {
            const error = 'The CSV file appears to be empty.';
            setUploadError(error);
            if (options.onError) options.onError(error);
            setIsUploading(false);
            return;
          }
          
          // Parse the header line
          const headers = parseCSVLine(lines[0]);
          
          // Validate that we have the expected columns
          const requiredColumns = ['objectName', 'pointName'];
          const hasRequiredColumns = requiredColumns.some(col => 
            headers.some(header => header.toLowerCase() === col.toLowerCase())
          );
          
          if (!hasRequiredColumns) {
            const error = 'CSV file is missing required columns. Please ensure the file has either objectName or pointName column.';
            setUploadError(error);
            if (options.onError) options.onError(error);
            setIsUploading(false);
            return;
          }
          
          // Parse the data rows
          for (let i = 1; i < lines.length; i++) {
            const values = parseCSVLine(lines[i]);
            if (values.length === 0) continue;
            
            const row: Record<string, string> = {};
            
            // Make sure we don't go out of bounds on either array
            const minLength = Math.min(headers.length, values.length);
            
            for (let j = 0; j < minLength; j++) {
              row[headers[j]] = values[j] || '';
            }
            
            json.push(row);
          }
        } else {
          // Parse JSON
          json = JSON.parse(data);
        }
        
        // Process data and convert to BMSPoint format
        const importedPoints: BMSPoint[] = [];
        
        json.forEach((row: any) => {
          // Map the specific columns from the dataset
          // Support the standard BMS column names provided by user
          const pointName = row['pointName'] || row['objectName'] || '';
          const pointType = row['pointType'] || row['objectType'] || '';
          const unit = row['unit'] || '';
          const description = row['description'] || '';
          const pointId = row['pointId'] || row['objectIdentifier'] || '';
          
          if (pointName) {
            importedPoints.push({
              id: pointId || uuidv4(), // Use pointId if available, otherwise generate a UUID
              pointName: pointName,
              pointType: pointType || 'Unknown',
              unit: unit || '',
              description: description || '',
              // Include all additional fields
              deviceInstance: row['deviceInstance'] || '',
              deviceAddress: row['deviceAddress'] || '',
              assetId: row['assetId'] || '',
              objectInst: row['objectInst'] || '',
              objectIdentifier: row['objectIdentifier'] || '',
              presentValue: row['presentValue'] || '',
              timestamp: row['timestamp'] || '',
              source: row['source'] || '',
              otDeviceInst: row['otDeviceInst'] || '',
              covIncrement: row['covIncrement'] || ''
            });
          }
        });
        
        if (importedPoints.length === 0) {
          const error = 'No valid points found in the uploaded file. Make sure the file contains columns like "pointName", "objectName", "pointType", etc.';
          setUploadError(error);
          if (options.onError) options.onError(error);
          setIsUploading(false);
          return;
        }
        
        console.log(`Successfully imported ${importedPoints.length} points`);
        
        // Call success callback with imported points
        if (options.onSuccess) {
          options.onSuccess(importedPoints);
        }
        
        // Reset file input
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        
      } catch (err) {
        console.error('Error processing file:', err);
        const errorMessage = `Error processing file: ${err instanceof Error ? err.message : 'Unknown error'}`;
        setUploadError(errorMessage);
        if (options.onError) options.onError(errorMessage);
      } finally {
        setIsUploading(false);
      }
    };
    
    reader.onerror = () => {
      const error = 'Error reading file.';
      setUploadError(error);
      if (options.onError) options.onError(error);
      setIsUploading(false);
    };
    
    reader.readAsText(file);
  };

  // Handle file input change
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    handleFileUpload(file);
  };

  // Reset the file input and error state
  const resetFileInput = () => {
    setUploadError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return {
    fileInputRef,
    uploadError,
    isUploading,
    handleFileInputChange,
    resetFileInput
  };
}