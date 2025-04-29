import React, { useState, useEffect } from 'react';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  Button,
  Typography,
  CircularProgress,
  Paper,
} from '@mui/material';
import { useSnackbar } from 'notistack';
import GroupPoints from '../pages/GroupPoints';
import TaggingPage from './TaggingPage';

export interface Point {
  id?: string;
  pointName: string;
  name?: string;
  description?: string;
  [key: string]: any;
}

// Ensure compatibility with GroupPoints component
export interface GroupPoint {
  id: string;
  name?: string;
  pointName?: string;
  description?: string;
  [key: string]: any;
}

export interface Group {
  name: string;
  description?: string;
  points: Point[];
}

export interface GroupsMap {
  [key: string]: Group;
}

export interface TagsMap {
  [key: string]: string[];
}

const steps = ['Group Points', 'Generate Tags', 'Review & Save'];

const PointMappingWorkflow: React.FC = () => {
  const { enqueueSnackbar } = useSnackbar();
  const [activeStep, setActiveStep] = useState(0);
  const [points, setPoints] = useState<Point[]>([]);
  const [groups, setGroups] = useState<GroupsMap>({});
  const [tags, setTags] = useState<TagsMap>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Don't automatically load points on component mount
    // Let user explicitly load points when needed
    // loadPoints();

    // Initialize with empty points array
    setPoints([]);
  }, []);

  const loadPoints = async () => {
    setLoading(true);
    try {
      // Add a confirmation dialog before making API call
      const shouldProceed = window.confirm('Do you want to load points from the server?');
      if (!shouldProceed) {
        setLoading(false);
        return;
      }

      const response = await fetch('/api/points');
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setPoints(data.points);
        } else {
          enqueueSnackbar(data.error || 'Failed to load points', { variant: 'error' });
        }
      } else {
        enqueueSnackbar('Failed to load points', { variant: 'error' });
      }
    } catch (error) {
      enqueueSnackbar('Error loading points', { variant: 'error' });
      console.error('Error loading points:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleReset = () => {
    setActiveStep(0);
    setGroups({});
    setTags({});
  };

  const handleGroupsGenerated = (newGroups: GroupsMap) => {
    setGroups(newGroups);
    handleNext();
  };

  const handleTagsGenerated = (newTags: TagsMap) => {
    setTags(newTags);
    handleNext();
  };

  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <GroupPoints
            points={points.map((p) => ({
              ...p,
              id: p.id || p.pointName || `point-${Math.random().toString(36).substring(2, 9)}`,
              name: p.name || p.pointName, // Ensure name property exists
            }))}
            onGroupsGenerated={handleGroupsGenerated}
          />
        );
      case 1:
        return <TaggingPage points={points} onTagsGenerated={handleTagsGenerated} />;
      case 2:
        return (
          <Box p={3}>
            <Typography variant="h6" gutterBottom>
              Review Generated Groups and Tags
            </Typography>
            {Object.entries(groups).map(([groupName, group]) => (
              <Paper key={groupName} sx={{ p: 2, mb: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  {groupName}
                </Typography>
                {group.description && (
                  <Typography color="textSecondary" paragraph>
                    {group.description}
                  </Typography>
                )}
                <Typography variant="body2">Points in group: {group.points.length}</Typography>
                {tags[groupName] && tags[groupName].length > 0 && (
                  <Box mt={1}>
                    <Typography variant="body2">Tags:</Typography>
                    <Box display="flex" flexWrap="wrap" gap={1} mt={1}>
                      {tags[groupName].map((tag, index) => (
                        <Typography
                          key={index}
                          variant="body2"
                          sx={{
                            bgcolor: 'primary.light',
                            color: 'primary.contrastText',
                            px: 1,
                            py: 0.5,
                            borderRadius: 1,
                          }}
                        >
                          {tag}
                        </Typography>
                      ))}
                    </Box>
                  </Box>
                )}
              </Paper>
            ))}
          </Box>
        );
      default:
        return 'Unknown step';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Stepper activeStep={activeStep}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
      <Box sx={{ mt: 4 }}>
        {activeStep === steps.length ? (
          <Box>
            <Typography sx={{ mt: 2, mb: 1 }}>
              All steps completed - you&apos;re finished
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'row', pt: 2 }}>
              <Box sx={{ flex: '1 1 auto' }} />
              <Button onClick={handleReset}>Start New Workflow</Button>
            </Box>
          </Box>
        ) : (
          <Box>
            {getStepContent(activeStep)}
            <Box sx={{ display: 'flex', flexDirection: 'row', pt: 2 }}>
              <Button
                color="inherit"
                disabled={activeStep === 0}
                onClick={handleBack}
                sx={{ mr: 1 }}
              >
                Back
              </Button>
              <Box sx={{ flex: '1 1 auto' }} />
              {activeStep === steps.length - 1 ? (
                <Button onClick={handleNext}>Finish</Button>
              ) : (
                <Button onClick={handleNext}>Next</Button>
              )}
            </Box>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default PointMappingWorkflow;
