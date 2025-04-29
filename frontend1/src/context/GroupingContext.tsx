import React, { createContext, useContext, useState, useCallback } from 'react';
import { BMSPoint, PointGroup } from '../types/api';
import { groupPoints, aiGroupPoints } from '../api/bmsApi';

// Define types for the context
export interface GroupingContextType {
  // State
  groups: Record<string, PointGroup>;
  selectedGroupId: string | null;
  groupingProperty: string;
  isAiGrouping: boolean;
  aiStatus: string | null;
  ungroupedPoints: BMSPoint[];
  loading: boolean;
  error: string | null;

  // Actions
  setGroups: (groups: Record<string, PointGroup>) => void;
  selectGroup: (groupId: string | null) => void;
  setGroupingProperty: (property: string) => void;
  groupPointsByProperty: (points: BMSPoint[], property?: string) => Promise<void>;
  groupPointsWithAI: (points: BMSPoint[]) => Promise<void>;
  addGroup: (name: string, description?: string) => void;
  updateGroup: (groupId: string, updates: Partial<PointGroup>) => void;
  deleteGroup: (groupId: string) => void;
  addPointToGroup: (groupId: string, point: BMSPoint) => void;
  removePointFromGroup: (groupId: string, pointId: string) => void;
  movePointBetweenGroups: (sourceGroupId: string, targetGroupId: string, pointId: string) => void;
  clearAllGroups: () => void;
}

// Create the context
const GroupingContext = createContext<GroupingContextType | null>(null);

// Custom hook for using this context
export const useGroupingContext = () => {
  const context = useContext(GroupingContext);
  if (!context) {
    throw new Error('useGroupingContext must be used within a GroupingProvider');
  }
  return context;
};

// Provider component
export const GroupingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [groups, setGroups] = useState<Record<string, PointGroup>>({});
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);
  const [groupingProperty, setGroupingProperty] = useState<string>('pointType');
  const [isAiGrouping, setIsAiGrouping] = useState<boolean>(false);
  const [aiStatus, setAiStatus] = useState<string | null>(null);
  const [ungroupedPoints, setUngroupedPoints] = useState<BMSPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Group points by a selected property
  const groupPointsByProperty = useCallback(
    async (points: BMSPoint[], property?: string) => {
      if (points.length === 0) {
        setError('No points available to group');
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const response = await groupPoints(points, property || groupingProperty);
        if (response && response.grouped_points) {
          setGroups(response.grouped_points);

          // Set first group as selected
          const firstGroupKey = Object.keys(response.grouped_points)[0];
          if (firstGroupKey) {
            setSelectedGroupId(firstGroupKey);
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred while grouping points');
        console.error('Error grouping points:', err);
      } finally {
        setLoading(false);
      }
    },
    [groupingProperty]
  );

  // Group points using AI
  const groupPointsWithAI = useCallback(async (points: BMSPoint[]) => {
    if (points.length === 0) {
      setError('No points available for AI grouping');
      return;
    }

    setLoading(true);
    setIsAiGrouping(true);
    setAiStatus('Analyzing point patterns...');
    setError(null);

    try {
      const response = await aiGroupPoints(points);
      if (response && response.grouped_points) {
        setGroups(response.grouped_points);

        // Set first group as selected
        const firstGroupKey = Object.keys(response.grouped_points)[0];
        if (firstGroupKey) {
          setSelectedGroupId(firstGroupKey);
        }

        setAiStatus('AI grouping completed successfully');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during AI grouping');
      console.error('Error in AI grouping:', err);
      setAiStatus('AI grouping failed');
    } finally {
      setLoading(false);
      setIsAiGrouping(false);

      // Clear status after 3 seconds
      setTimeout(() => setAiStatus(null), 3000);
    }
  }, []);

  // Add a new group
  const addGroup = useCallback((name: string, description: string = '') => {
    const newGroupId = `group_${Date.now()}`;
    setGroups((prevGroups) => ({
      ...prevGroups,
      [newGroupId]: {
        name,
        description,
        points: [],
      },
    }));
    setSelectedGroupId(newGroupId);
  }, []);

  // Update an existing group
  const updateGroup = useCallback((groupId: string, updates: Partial<PointGroup>) => {
    setGroups((prevGroups) => {
      if (!prevGroups[groupId]) return prevGroups;

      return {
        ...prevGroups,
        [groupId]: {
          ...prevGroups[groupId],
          ...updates,
        },
      };
    });
  }, []);

  // Delete a group
  const deleteGroup = useCallback((groupId: string) => {
    setGroups((prevGroups) => {
      if (!prevGroups[groupId]) return prevGroups;

      // Add points from this group to ungrouped
      const groupPoints = prevGroups[groupId].points;
      setUngroupedPoints((prev) => [...prev, ...groupPoints]);

      // Create new groups object without the deleted group
      const { [groupId]: deletedGroup, ...remainingGroups } = prevGroups;

      // Select another group if available
      const remainingGroupIds = Object.keys(remainingGroups);
      if (remainingGroupIds.length > 0) {
        setSelectedGroupId(remainingGroupIds[0]);
      } else {
        setSelectedGroupId(null);
      }

      return remainingGroups;
    });
  }, []);

  // Add a point to a group
  const addPointToGroup = useCallback((groupId: string, point: BMSPoint) => {
    setGroups((prevGroups) => {
      if (!prevGroups[groupId]) return prevGroups;

      // Check if point already exists in the group
      const pointExists = prevGroups[groupId].points.some((p) => p.id === point.id);
      if (pointExists) return prevGroups;

      return {
        ...prevGroups,
        [groupId]: {
          ...prevGroups[groupId],
          points: [...prevGroups[groupId].points, point],
        },
      };
    });

    // Remove from ungrouped if present
    setUngroupedPoints((prev) => prev.filter((p) => p.id !== point.id));
  }, []);

  // Remove a point from a group
  const removePointFromGroup = useCallback((groupId: string, pointId: string) => {
    setGroups((prevGroups) => {
      if (!prevGroups[groupId]) return prevGroups;

      // Find the point
      const point = prevGroups[groupId].points.find((p) => p.id === pointId);
      if (point) {
        // Add to ungrouped
        setUngroupedPoints((prev) => [...prev, point]);
      }

      return {
        ...prevGroups,
        [groupId]: {
          ...prevGroups[groupId],
          points: prevGroups[groupId].points.filter((p) => p.id !== pointId),
        },
      };
    });
  }, []);

  // Move a point between groups
  const movePointBetweenGroups = useCallback(
    (sourceGroupId: string, targetGroupId: string, pointId: string) => {
      setGroups((prevGroups) => {
        if (!prevGroups[sourceGroupId] || !prevGroups[targetGroupId]) return prevGroups;

        // Find the point in source group
        const point = prevGroups[sourceGroupId].points.find((p) => p.id === pointId);
        if (!point) return prevGroups;

        return {
          ...prevGroups,
          [sourceGroupId]: {
            ...prevGroups[sourceGroupId],
            points: prevGroups[sourceGroupId].points.filter((p) => p.id !== pointId),
          },
          [targetGroupId]: {
            ...prevGroups[targetGroupId],
            points: [...prevGroups[targetGroupId].points, point],
          },
        };
      });
    },
    []
  );

  // Clear all groups
  const clearAllGroups = useCallback(() => {
    // Collect all points from all groups
    const allPoints: BMSPoint[] = [];
    Object.values(groups).forEach((group) => {
      allPoints.push(...group.points);
    });

    // Add to ungrouped
    setUngroupedPoints((prev) => [...prev, ...allPoints]);

    // Clear groups
    setGroups({});
    setSelectedGroupId(null);
  }, [groups]);

  // Context value
  const value: GroupingContextType = {
    // State
    groups,
    selectedGroupId,
    groupingProperty,
    isAiGrouping,
    aiStatus,
    ungroupedPoints,
    loading,
    error,

    // Actions
    setGroups,
    selectGroup: setSelectedGroupId,
    setGroupingProperty,
    groupPointsByProperty,
    groupPointsWithAI,
    addGroup,
    updateGroup,
    deleteGroup,
    addPointToGroup,
    removePointFromGroup,
    movePointBetweenGroups,
    clearAllGroups,
  };

  return <GroupingContext.Provider value={value}>{children}</GroupingContext.Provider>;
};

export default GroupingContext;
