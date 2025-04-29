/**
 * Loading wrapper component that shows a loading indicator or error message.
 */

import React, { ReactNode } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';

interface LoadingWrapperProps {
  loading: boolean;
  error?: string | null;
  children: ReactNode;
  message?: string;
}

// Component implementation
function LoadingWrapperComponent({
  loading,
  error,
  children,
  message = 'Loading...'
}: LoadingWrapperProps) {
  if (loading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
        <CircularProgress size={40} />
        <Typography variant="body1" sx={{ mt: 2 }}>
          {message}
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3, color: 'error.main' }}>
        <Typography variant="body1">{error}</Typography>
      </Box>
    );
  }

  return <>{children}</>;
}

// Export as both default and named export
export const LoadingWrapper = LoadingWrapperComponent;
export default LoadingWrapperComponent;
