import React from 'react';
import { CircularProgress, Box, Typography } from '@mui/material';

interface LoadingProps {
  message?: string;
  fullPage?: boolean;
}

export const Loading: React.FC<LoadingProps> = ({ message = 'Loading...', fullPage = false }) => {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      p={3}
      sx={fullPage ? { minHeight: '100vh', width: '100%' } : {}}
    >
      <CircularProgress size={40} />
      <Typography variant="body1" mt={2}>
        {message}
      </Typography>
    </Box>
  );
};

interface WithLoadingProps {
  isLoading: boolean;
  loadingMessage?: string;
}

export function withLoading<P extends object>(
  Component: React.ComponentType<P>
): React.FC<P & WithLoadingProps> {
  return ({ isLoading, loadingMessage, ...props }: WithLoadingProps & P) => {
    if (isLoading) {
      return <Loading message={loadingMessage} />;
    }

    return <Component {...(props as P)} />;
  };
}
