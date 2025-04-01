import React from 'react';
import { Modal, Button } from '../../components';
import { useFileUpload } from '../../hooks/groupPoints';
import { BMSPoint } from '../../types/apiTypes';
import './FileUploadForm.css';

interface FileUploadFormProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (points: BMSPoint[]) => void;
}

/**
 * Component for uploading files with BMS points data
 */
const FileUploadForm: React.FC<FileUploadFormProps> = ({ 
  isOpen, 
  onClose, 
  onUploadSuccess 
}) => {
  const { 
    fileInputRef, 
    uploadError, 
    isUploading, 
    handleFileInputChange, 
    resetFileInput 
  } = useFileUpload({
    onSuccess: (importedPoints) => {
      onUploadSuccess(importedPoints);
      handleCloseModal();
    }
  });

  const handleCloseModal = () => {
    resetFileInput();
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleCloseModal}
      title="Upload BMS Points"
    >
      <div className="file-upload-form">
        <p className="file-upload-form__instructions">
          Upload a CSV or JSON file containing BMS points data.
        </p>
        
        <div className="file-upload-form__input-container">
          <input 
            ref={fileInputRef}
            type="file" 
            accept=".csv,.json"
            onChange={handleFileInputChange}
            className="file-upload-form__input"
            disabled={isUploading}
          />
          {isUploading && (
            <div className="file-upload-form__loading">
              Processing file...
            </div>
          )}
        </div>
        
        {uploadError && (
          <div className="file-upload-form__error">
            {uploadError}
          </div>
        )}
        
        <div className="file-upload-form__format-info">
          <strong>Expected CSV format:</strong>
          <pre className="file-upload-form__format-example">
            objectType,otDeviceInst,objectInst,objectIdentifier,objectName,...
          </pre>
          <p>The file must contain at least one of these columns: <strong>objectName</strong> or <strong>pointName</strong></p>
          <p>
            Other supported columns: objectType, otDeviceInst, objectInst, 
            objectIdentifier, description, presentValue, covIncrement, unit, 
            timestamp, assetId, deviceInstance, deviceAddress, pointType, 
            source, pointId
          </p>
        </div>

        <div className="file-upload-form__actions">
          <Button
            onClick={handleCloseModal}
            className="file-upload-form__cancel-button"
          >
            Cancel
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default FileUploadForm;