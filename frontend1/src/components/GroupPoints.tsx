import React, { useState } from 'react';
import { Box, Button, Card, CardContent, Divider, Grid, Typography, TextField, CircularProgress } from '@mui/material';
import GroupPointsManual from './GroupPointsManual';
import GroupPointsAI from './GroupPointsAI';
import { BMSPoint } from '../types';

// Use the same type definition as in PointMappingWorkflow
export interface GroupsMap {
  [key: string]: {
    name: string;
    description?: string;
    points: BMSPoint[];
  };
}

interface GroupPointsProps {
  points: BMSPoint[];
  onGroupsGenerated: (groups: GroupsMap) => void;
}

const GroupPoints: React.FC<GroupPointsProps> = ({ points, onGroupsGenerated }) => {
  const [method, setMethod] = useState<'manual' | 'ai' | null>(null);

  const handleSelectMethod = (selectedMethod: 'manual' | 'ai') => {
    setMethod(selectedMethod);
  };

  const renderMethodSelection = () => (
    <Grid container spacing={3} justifyContent="center">
      <Grid item xs={12} sm={6} md={5} lg={4}>
        <Card 
          variant="outlined" 
          sx={{ 
            cursor: 'pointer',
            '&:hover': { 
              borderColor: 'primary.main',
              boxShadow: 3
            },
            height: '100%'
          }}
          onClick={() => handleSelectMethod('manual')}
        >
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Manual Grouping
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Create groups by manually selecting points and organizing them based on your specific needs.
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} md={5} lg={4}>
        <Card 
          variant="outlined" 
          sx={{ 
            cursor: 'pointer',
            '&:hover': { 
              borderColor: 'primary.main',
              boxShadow: 3
            },
            height: '100%'
          }}
          onClick={() => handleSelectMethod('ai')}
        >
          <CardContent>
            <Typography variant="h6" gutterBottom>
              AI-Assisted Grouping
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Let AI analyze your points and suggest logical groups based on naming conventions and point properties.
            </Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderGroupingInterface = () => {
    switch (method) {
      case 'manual':
        return <GroupPointsManual points={points} onGroupsGenerated={onGroupsGenerated} />;
      case 'ai':
        return <GroupPointsAI points={points} onGroupsGenerated={onGroupsGenerated} />;
      default:
        return renderMethodSelection();
    }
  };

  const handleBack = () => {
    setMethod(null);
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom align="center">
        Group BMS Points
      </Typography>
      <Typography variant="body1" paragraph align="center" color="text.secondary">
        Organize your BMS points into logical groups before mapping them to standard entities.
      </Typography>
      <Divider sx={{ my: 3 }} />
      
      {renderGroupingInterface()}
      
      {method && (
        <Box mt={3} display="flex" justifyContent="flex-start">
          <Button variant="outlined" onClick={handleBack}>
            Back to Method Selection
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default GroupPoints; 