import React, { useState, useRef, ChangeEvent, DragEvent } from 'react';
import './EnhancedFileUpload.css';

/**
 * EnhancedFileUpload props interface
 */
export interface EnhancedFileUploadProps {
  // Core functionality
  onFileSelected: (file: File) => void;
  onFileAnalyzed?: (fileType: string, recordCount: number) => void;
  acceptedFileTypes?: string[];
  maxFileSizeMB?: number;
  
  // Customization
  title?: string;
  subtitle?: string;
  dropzoneText?: string;
  buttonText?: string;
  className?: string;
  showPreview?: boolean;
  
  // State indicators
  isLoading?: boolean;
  error?: string | null;
}

/**
 * Enhanced file upload component with drag and drop, validation, and preview
 */
const EnhancedFileUpload: React.FC<EnhancedFileUploadProps> = ({
  // Core functionality
  onFileSelected,
  onFileAnalyzed,
  acceptedFileTypes = ['.csv', '.json'],
  maxFileSizeMB = 10,
  
  // Customization
  title = 'Upload File',
  subtitle = 'Drop a file or click to browse',
  dropzoneText = 'Drag & Drop file here',
  buttonText = 'Choose File',
  className = '',
  showPreview = true,
  
  // State indicators
  isLoading = false,
  error = null
}) => {
  // State for file and drag status
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [preview, setPreview] = useState<{ type: string; content: string } | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  
  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounter = useRef<number>(0);
  
  // Click handler to trigger file input
  const handleClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };
  
  // File format validation
  const isValidFileType = (file: File): boolean => {
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    return acceptedFileTypes.includes(fileExtension);
  };
  
  // File size validation
  const isValidFileSize = (file: File): boolean => {
    const fileSizeMB = file.size / (1024 * 1024);
    return fileSizeMB <= maxFileSizeMB;
  };
  
  // Process the selected file
  const processFile = async (file: File) => {
    try {
      // Validate file type
      if (!isValidFileType(file)) {
        setValidationError(`Invalid file type. Accepted types: ${acceptedFileTypes.join(', ')}`);
        return;
      }
      
      // Validate file size
      if (!isValidFileSize(file)) {
        setValidationError(`File size exceeds the limit of ${maxFileSizeMB}MB`);
        return;
      }
      
      // Clear previous errors
      setValidationError(null);
      
      // Set the file
      setFile(file);
      
      // Generate preview
      if (showPreview) {
        generatePreview(file);
      }
      
      // Callback with the file
      onFileSelected(file);
      
      // Analyze file content
      if (onFileAnalyzed) {
        analyzeFile(file);
      }
    } catch (err) {
      setValidationError(err instanceof Error ? err.message : 'Error processing file');
    }
  };
  
  // Generate a preview of the file
  const generatePreview = (file: File) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      const content = e.target?.result as string;
      const fileType = file.name.split('.').pop()?.toLowerCase();
      
      if (fileType === 'csv' || fileType === 'json') {
        // For CSV and JSON, show the first few lines
        const previewLines = content.split('\n').slice(0, 10).join('\n');
        setPreview({
          type: fileType,
          content: previewLines
        });
      } else {
        setPreview(null);
      }
    };
    
    reader.onerror = () => {
      setPreview(null);
      setValidationError('Error generating file preview');
    };
    
    reader.readAsText(file);
  };
  
  // Analyze the file content
  const analyzeFile = (file: File) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const fileType = file.name.split('.').pop()?.toLowerCase();
        
        let recordCount = 0;
        
        if (fileType === 'csv') {
          // For CSV, count lines (minus header)
          const lines = content.split('\n').filter(line => line.trim() !== '');
          recordCount = lines.length > 0 ? lines.length - 1 : 0;
        } else if (fileType === 'json') {
          // For JSON, try to parse and count records
          const data = JSON.parse(content);
          recordCount = Array.isArray(data) ? data.length : 1;
        }
        
        if (onFileAnalyzed) {
          onFileAnalyzed(fileType || '', recordCount);
        }
      } catch (err) {
        setValidationError(err instanceof Error ? err.message : 'Error analyzing file content');
      }
    };
    
    reader.onerror = () => {
      setValidationError('Error reading file content');
    };
    
    reader.readAsText(file);
  };
  
  // File change handler
  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      processFile(files[0]);
    }
  };
  
  // Drag events
  const handleDragEnter = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    dragCounter.current += 1;
    if (event.dataTransfer.items && event.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  };
  
  const handleDragLeave = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    dragCounter.current -= 1;
    if (dragCounter.current <= 0) {
      setIsDragging(false);
      dragCounter.current = 0;
    }
  };
  
  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
  };
  
  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
    dragCounter.current = 0;
    
    if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
      processFile(event.dataTransfer.files[0]);
      event.dataTransfer.clearData();
    }
  };
  
  // Dynamic classes
  const dropzoneClasses = `file-upload-dropzone ${isDragging ? 'dragging' : ''} ${isLoading ? 'loading' : ''}`;
  
  return (
    <div className={`enhanced-file-upload ${className}`}>
      <div className="file-upload-header">
        <h3 className="file-upload-title">{title}</h3>
        <p className="file-upload-subtitle">{subtitle}</p>
      </div>
      
      <div
        className={dropzoneClasses}
        onClick={handleClick}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <input
          type="file"
          ref={fileInputRef}
          className="file-upload-input"
          onChange={handleFileChange}
          accept={acceptedFileTypes.join(',')}
          disabled={isLoading}
        />
        
        {!file && (
          <div className="file-upload-placeholder">
            <div className="upload-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <p className="upload-text">{dropzoneText}</p>
            <button type="button" className="upload-button">
              {buttonText}
            </button>
          </div>
        )}
        
        {file && (
          <div className="file-upload-info">
            <div className="file-info">
              <div className="file-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                  <polyline points="10 9 9 9 8 9" />
                </svg>
              </div>
              <div className="file-details">
                <div className="file-name">{file.name}</div>
                <div className="file-size">{(file.size / 1024).toFixed(1)} KB</div>
              </div>
            </div>
            <button
              type="button"
              className="file-remove-button"
              onClick={(e) => {
                e.stopPropagation();
                setFile(null);
                setPreview(null);
                if (fileInputRef.current) {
                  fileInputRef.current.value = '';
                }
              }}
            >
              Remove
            </button>
          </div>
        )}
        
        {isLoading && (
          <div className="file-upload-loading">
            <div className="loading-spinner"></div>
            <span>Processing file...</span>
          </div>
        )}
      </div>
      
      {/* Display error messages */}
      {(error || validationError) && (
        <div className="file-upload-error">
          {error || validationError}
        </div>
      )}
      
      {/* File preview */}
      {file && preview && showPreview && (
        <div className="file-preview">
          <h4>File Preview</h4>
          <pre className="preview-content">{preview.content}</pre>
        </div>
      )}
      
      {/* Footer with information about accepted files */}
      <div className="file-upload-footer">
        <div className="accepted-files">
          <small>
            Accepted file types: {acceptedFileTypes.join(', ')} (Max size: {maxFileSizeMB}MB)
          </small>
        </div>
      </div>
    </div>
  );
};

export default EnhancedFileUpload;