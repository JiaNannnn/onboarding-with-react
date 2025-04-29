import React, { useState, useEffect, startTransition } from 'react';
import {
  Box,
  Button,
  CircularProgress,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
  TextField,
  IconButton,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { useSnackbar } from 'notistack';
import { Point, TagsMap } from './PointMappingWorkflow';

interface TaggingPageProps {
  points?: Point[];
  onTagsGenerated?: (tags: TagsMap) => void;
}

// Use error boundary for the component
const TaggingPage: React.FC<TaggingPageProps> = ({ points: initialPoints, onTagsGenerated }) => {
  const { enqueueSnackbar } = useSnackbar();
  const [points, setPoints] = useState<Point[]>([]);
  const [loading, setLoading] = useState(false);
  const [tags, setTags] = useState<TagsMap>({});
  const [newTag, setNewTag] = useState('');
  const [selectedPoint, setSelectedPoint] = useState<string | null>(null);

  useEffect(() => {
    if (initialPoints) {
      setPoints(initialPoints);
    } else {
      loadPoints();
    }
  }, [initialPoints]);

  const loadPoints = async () => {
    setLoading(true);
    try {
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

  const generateTags = async () => {
    if (!points.length) {
      enqueueSnackbar('No points available for tagging', { variant: 'warning' });
      return;
    }

    setLoading(true);
    try {
      // Use the correct API endpoint path
      const response = await fetch('/api/v1/bms/ai-generate-tags', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ points }),
      });

      // Handle network errors
      if (!response.ok) {
        throw new Error(`Network response error: ${response.status} ${response.statusText}`);
      }

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setTags(data.tags);
          if (onTagsGenerated) {
            onTagsGenerated(data.tags);
          }
          enqueueSnackbar('Tags generated successfully', { variant: 'success' });
        } else {
          enqueueSnackbar(data.error || 'Failed to generate tags', { variant: 'error' });
        }
      } else {
        enqueueSnackbar('Failed to generate tags', { variant: 'error' });
      }
    } catch (error) {
      enqueueSnackbar('Error generating tags', { variant: 'error' });
      console.error('Error generating tags:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddTag = (pointName: string) => {
    if (!newTag.trim()) return;

    setTags((prevTags) => ({
      ...prevTags,
      [pointName]: [...(prevTags[pointName] || []), newTag.trim()],
    }));
    setNewTag('');
  };

  const handleRemoveTag = (pointName: string, tagIndex: number) => {
    setTags((prevTags) => ({
      ...prevTags,
      [pointName]: prevTags[pointName].filter((_, index) => index !== tagIndex),
    }));
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h5">Point Tagging</Typography>
        <Button
          variant="contained"
          color="primary"
          onClick={generateTags}
          disabled={loading || !points.length}
        >
          Generate Tags
        </Button>
      </Box>

      <List>
        {points.map((point) => (
          <Paper key={point.pointName} elevation={1} sx={{ mb: 2, p: 2 }}>
            <ListItem>
              <Box width="100%">
                <ListItemText
                  primary={point.pointName}
                  secondary={point.description || 'No description'}
                />
                <Box mt={1} display="flex" flexWrap="wrap" gap={1}>
                  {(tags[point.pointName] || []).map((tag, index) => (
                    <Chip
                      key={index}
                      label={tag}
                      onDelete={() => handleRemoveTag(point.pointName, index)}
                      color="primary"
                      variant="outlined"
                    />
                  ))}
                </Box>
                <Box mt={2} display="flex" gap={1}>
                  <TextField
                    size="small"
                    placeholder="Add a tag"
                    value={selectedPoint === point.pointName ? newTag : ''}
                    onChange={(e) => {
                      // Batch state updates for better performance
                      startTransition(() => {
                        setSelectedPoint(point.pointName);
                        setNewTag(e.target.value);
                      });
                    }}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handleAddTag(point.pointName);
                      }
                    }}
                  />
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => handleAddTag(point.pointName)}
                    disabled={!newTag.trim() || selectedPoint !== point.pointName}
                  >
                    Add Tag
                  </Button>
                </Box>
              </Box>
            </ListItem>
          </Paper>
        ))}
      </List>
    </Box>
  );
};

export default TaggingPage;
