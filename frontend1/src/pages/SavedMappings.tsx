import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { useAppContext } from '../store/AppContext';

const SavedMappings: React.FC = () => {
  const { state } = useAppContext();

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Saved Mappings
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        View and manage your saved point mappings and export them for use.
      </Typography>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6">
          Saved Mappings: {state.mappings.length}
        </Typography>
        <Typography variant="body1" sx={{ mt: 2 }}>
          This page will allow you to view, edit, and export your saved mappings.
        </Typography>
      </Paper>
    </Box>
  );
};

export default SavedMappings; 