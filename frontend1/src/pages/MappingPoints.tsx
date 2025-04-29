import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { useAppContext } from '../store/AppContext';

const MappingPoints: React.FC = () => {
  const { state } = useAppContext();

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Mapping Points
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Map points between different building automation systems or standards.
      </Typography>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6">
          Groups Available: {state.groups.length}
        </Typography>
        <Typography variant="body1" sx={{ mt: 2 }}>
          This page will allow you to create mappings between points and standardized naming conventions.
        </Typography>
      </Paper>
    </Box>
  );
};

export default MappingPoints; 