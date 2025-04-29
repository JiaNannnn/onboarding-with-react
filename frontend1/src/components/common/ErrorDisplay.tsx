import React from 'react';
import { Alert, AlertTitle, Box, Typography, Button, Paper, IconButton } from '@mui/material';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import CloseIcon from '@mui/icons-material/Close';
import { ErrorDisplayProps } from '../../types';

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ 
  error, 
  onClose 
}) => {
  if (!error) return null;
  
  return (
    <Alert 
      severity="error" 
      sx={{ mb: 2 }}
      action={
        onClose ? (
          <IconButton
            aria-label="close"
            color="inherit"
            size="small"
            onClick={onClose}
          >
            <CloseIcon fontSize="inherit" />
          </IconButton>
        ) : undefined
      }
    >
      <AlertTitle>Error</AlertTitle>
      {error}
    </Alert>
  );
};

// Extended ErrorDisplay props for the full page error
interface FullPageErrorProps extends ErrorDisplayProps {
  title?: string;
  onRetry?: () => void;
}

export const FullPageError: React.FC<FullPageErrorProps> = ({ 
  error, 
  title = "Something went wrong",
  onRetry
}) => {
  if (!error) return null;

  const errorMessage = typeof error === 'string' ? error : 'An unknown error occurred';

  return (
    <div className="full-page-error">
      <div className="error-container">
        <h3>{title}</h3>
        <p>{errorMessage}</p>
        {onRetry && (
          <button onClick={onRetry}>Try Again</button>
        )}
      </div>
    </div>
  );
};

export default ErrorDisplay;
