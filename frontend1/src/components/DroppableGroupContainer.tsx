import React from 'react';
import { Box, Paper, Typography, IconButton, Divider } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import { BMSPoint, PointGroup } from '../types';
import { useDrop, DropMonitor } from '../hooks/useDrop';
import DraggablePointCard from './DraggablePointCard';

// Define the point drag type constant
const POINT_TYPE = 'POINT';

// Define the component props
interface DroppableGroupContainerProps {
  group: PointGroup;
  selected?: boolean;
  onDelete?: () => void;
  onEdit?: () => void;
  onClick?: () => void;
  onDrop: (itemId: string, targetGroupId: string) => void;
}

// Define drop collection return type
interface DropCollectedProps {
  isOver: boolean;
  canDrop: boolean;
}

// Define the drag item structure
interface DragItem {
  id: string;
  groupId?: number | null;
  type: string;
}

const DroppableGroupContainer: React.FC<DroppableGroupContainerProps> = ({
  group,
  selected = false,
  onDelete,
  onEdit,
  onClick,
  onDrop,
}) => {
  // Use our custom useDrop hook with proper typing
  const [{ isOver, canDrop }, dropRef] = useDrop<DragItem, {}, DropCollectedProps>({
    accept: POINT_TYPE,
    drop: (item: DragItem) => {
      // Only process drop if the item is from a different group
      if (item.groupId !== Number(group.id)) {
        onDrop(item.id, group.id);
      }
      return undefined;
    },
    collect: (monitor: DropMonitor) => ({
      isOver: monitor.isOver(),
      canDrop: monitor.canDrop(),
    }),
  });

  // Calculate background color based on drag state
  const getBgColor = () => {
    if (isOver && canDrop) return 'rgba(25, 118, 210, 0.1)'; // Light blue for active drop
    if (selected) return 'rgba(25, 118, 210, 0.05)'; // Lighter blue for selection
    return 'background.paper'; // Default background
  };

  return (
    <Paper
      ref={dropRef}
      elevation={2}
      onClick={onClick}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: getBgColor(),
        border: selected ? '2px solid' : '1px solid',
        borderColor: selected ? 'primary.main' : 'divider',
        transition: 'background-color 0.2s, border 0.2s',
      }}
    >
      <Box
        sx={{
          p: 1.5,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Typography variant="subtitle1" noWrap sx={{ flex: 1 }}>
          {group.name} ({group.points?.length || 0})
        </Typography>
        <Box>
          {onEdit && (
            <IconButton size="small" onClick={(e) => {
              e.stopPropagation();
              onEdit();
            }}>
              <EditIcon fontSize="small" />
            </IconButton>
          )}
          {onDelete && (
            <IconButton size="small" onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}>
              <DeleteIcon fontSize="small" />
            </IconButton>
          )}
        </Box>
      </Box>
      <Divider />
      <Box
        sx={{
          p: 1.5,
          pt: 1,
          flexGrow: 1,
          overflow: 'auto',
          backgroundColor: isOver && canDrop ? 'rgba(25, 118, 210, 0.05)' : 'transparent',
        }}
      >
        {group.points && group.points.map(point => (
          <DraggablePointCard 
            key={point.id} 
            point={point}
            groupId={Number(group.id)} 
          />
        ))}
      </Box>
    </Paper>
  );
};

export default DroppableGroupContainer;