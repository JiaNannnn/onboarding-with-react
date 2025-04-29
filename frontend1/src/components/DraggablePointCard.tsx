import React from 'react';
import { Box, Card, CardContent, Typography, Chip, CardActionArea } from '@mui/material';
import { BMSPoint } from '../types';
import { useDrag, DragMonitor } from '../hooks/useDrag';

// Define the point drag type constant
const POINT_TYPE = 'POINT';

// Define the props for the component
interface DraggablePointCardProps {
  point: BMSPoint;
  onClick?: () => void;
  isSelected?: boolean;
  groupId?: number | null;
}

// Define the drag item structure
interface DragItem {
  id: string;
  groupId?: number | null;
  type: string;
}

const DraggablePointCard: React.FC<DraggablePointCardProps> = ({
  point,
  onClick,
  isSelected = false,
  groupId,
}) => {
  // Use our custom useDrag hook with proper typing
  const [{ isDragging }, dragRef] = useDrag<DragItem>({
    type: POINT_TYPE,
    item: {
      id: point.id || '',
      groupId,
      type: POINT_TYPE,
    },
    collect: (monitor: DragMonitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  // Extract tags from the point
  const renderTags = () => {
    const tags: string[] = [];
    if (point.pointType) tags.push(point.pointType);
    if (point.unit) tags.push(`Unit: ${point.unit}`);
    
    return tags.map((tag, index) => (
      <Chip 
        key={index} 
        label={tag} 
        size="small" 
        variant="outlined" 
        sx={{ mr: 0.5, mb: 0.5 }} 
      />
    ));
  };

  return (
    <Box
      ref={dragRef}
      sx={{
        opacity: isDragging ? 0.5 : 1,
        cursor: 'grab',
        mb: 1,
      }}
    >
      <Card
        variant="outlined"
        sx={{
          border: isSelected ? '2px solid' : '1px solid',
          borderColor: isSelected ? 'primary.main' : 'divider',
        }}
      >
        <CardActionArea onClick={onClick}>
          <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
            <Typography variant="subtitle1" component="div" noWrap>
              {point.pointName}
            </Typography>
            
            {point.description && (
              <Typography variant="body2" color="text.secondary" noWrap>
                {point.description}
              </Typography>
            )}
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', mt: 1 }}>
              {renderTags()}
            </Box>
          </CardContent>
        </CardActionArea>
      </Card>
    </Box>
  );
};

export default DraggablePointCard;