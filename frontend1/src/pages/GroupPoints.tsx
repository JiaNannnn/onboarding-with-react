import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { useAppContext } from '../store/AppContext';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { DataTable } from '../components/common/DataTable';
import { LoadingWrapper } from '../components/common/LoadingWrapper';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorDisplay } from '../components/common/ErrorDisplay';
import DraggablePointCard from '../components/DraggablePointCard';

const GroupPoints: React.FC = () => {
  const { state } = useAppContext();

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Group Points
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Create and manage logical groups of related points.
      </Typography>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6">
          Points Available: {state.points.length}
        </Typography>
        <Typography variant="body1" sx={{ mt: 2 }}>
          This page will allow you to create groups, add points to groups, and manage the grouping structure.
        </Typography>
      </Paper>
    </Box>
  );
};

export default GroupPoints; 