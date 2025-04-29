import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { EmptyStateProps } from '../../types';

/**
 * Empty state component for displaying when there's no data
 */
export const EmptyState: React.FC<EmptyStateProps> = ({ 
  title, 
  description, 
  icon 
}) => {
  return (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        textAlign: 'center',
        borderRadius: 2,
        backgroundColor: 'background.paper',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {icon && (
        <Box sx={{ mb: 2, color: 'text.secondary' }}>
          {icon}
        </Box>
      )}
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {description}
      </Typography>
    </Paper>
  );
};

export default EmptyState;
