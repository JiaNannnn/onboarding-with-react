import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { BMSPoint, PointGroup } from '../types/apiTypes';

/**
 * GroupingContext state type definition
 */
interface GroupingContextState {
  groups: Record<string, PointGroup>;
  groupingStrategy: 'default' | 'ai' | 'ontology';
  loading: boolean;
  error: string | null;
}

/**
 * GroupingContext actions type definition
 */
interface GroupingContextActions {
  setGroups: (groups: Record<string, PointGroup>) => void;
  addGroup: (groupKey: string, group: PointGroup) => void;
  removeGroup: (groupKey: string) => void;
  updateGroup: (groupKey: string, group: Partial<PointGroup>) => void;
  addPointToGroup: (groupKey: string, point: BMSPoint) => void;
  removePointFromGroup: (groupKey: string, pointId: string) => void;
  movePoint: (fromGroupKey: string, toGroupKey: string, pointId: string) => void;
  clearGroups: () => void;
  setGroupingStrategy: (strategy: 'default' | 'ai' | 'ontology') => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

/**
 * Combined GroupingContext type
 */
type GroupingContextType = GroupingContextState & GroupingContextActions;

/**
 * Default state for GroupingContext
 */
const defaultGroupingState: GroupingContextState = {
  groups: {},
  groupingStrategy: 'default',
  loading: false,
  error: null,
};

/**
 * Create the GroupingContext
 */
const GroupingContext = createContext<GroupingContextType | null>(null);

/**
 * GroupingProvider props interface
 */
interface GroupingProviderProps {
  children: ReactNode;
}

/**
 * Provider component for GroupingContext
 */
export function GroupingProvider({ children }: GroupingProviderProps): JSX.Element {
  const [state, setState] = useState<GroupingContextState>(defaultGroupingState);

  /**
   * Set all groups
   */
  const setGroups = useCallback((groups: Record<string, PointGroup>): void => {
    setState((prevState) => ({
      ...prevState,
      groups,
    }));
  }, []);

  /**
   * Add a new group
   */
  const addGroup = useCallback((groupKey: string, group: PointGroup): void => {
    setState((prevState) => ({
      ...prevState,
      groups: {
        ...prevState.groups,
        [groupKey]: group,
      },
    }));
  }, []);

  /**
   * Remove a group
   */
  const removeGroup = useCallback((groupKey: string): void => {
    setState((prevState) => {
      const newGroups = { ...prevState.groups };
      delete newGroups[groupKey];
      return {
        ...prevState,
        groups: newGroups,
      };
    });
  }, []);

  /**
   * Update an existing group
   */
  const updateGroup = useCallback((groupKey: string, groupUpdates: Partial<PointGroup>): void => {
    setState((prevState) => {
      const group = prevState.groups[groupKey];
      if (!group) return prevState;

      return {
        ...prevState,
        groups: {
          ...prevState.groups,
          [groupKey]: {
            ...group,
            ...groupUpdates,
          },
        },
      };
    });
  }, []);

  /**
   * Add a point to a group
   */
  const addPointToGroup = useCallback((groupKey: string, point: BMSPoint): void => {
    setState((prevState) => {
      const group = prevState.groups[groupKey];
      if (!group) return prevState;

      // Check if point already exists in the group
      const pointExists = group.points.some((p) => p.id === point.id);
      if (pointExists) return prevState;

      return {
        ...prevState,
        groups: {
          ...prevState.groups,
          [groupKey]: {
            ...group,
            points: [...group.points, point],
          },
        },
      };
    });
  }, []);

  /**
   * Remove a point from a group
   */
  const removePointFromGroup = useCallback((groupKey: string, pointId: string): void => {
    setState((prevState) => {
      const group = prevState.groups[groupKey];
      if (!group) return prevState;

      return {
        ...prevState,
        groups: {
          ...prevState.groups,
          [groupKey]: {
            ...group,
            points: group.points.filter((p) => p.id !== pointId),
          },
        },
      };
    });
  }, []);

  /**
   * Move a point from one group to another
   */
  const movePoint = useCallback((fromGroupKey: string, toGroupKey: string, pointId: string): void => {
    setState((prevState) => {
      const fromGroup = prevState.groups[fromGroupKey];
      const toGroup = prevState.groups[toGroupKey];
      
      if (!fromGroup || !toGroup) return prevState;

      // Find the point to move
      const pointIndex = fromGroup.points.findIndex((p) => p.id === pointId);
      if (pointIndex === -1) return prevState;

      const point = fromGroup.points[pointIndex];
      
      // Remove from source group and add to target group
      return {
        ...prevState,
        groups: {
          ...prevState.groups,
          [fromGroupKey]: {
            ...fromGroup,
            points: fromGroup.points.filter((p) => p.id !== pointId),
          },
          [toGroupKey]: {
            ...toGroup,
            points: [...toGroup.points, point],
          },
        },
      };
    });
  }, []);

  /**
   * Clear all groups
   */
  const clearGroups = useCallback((): void => {
    setState((prevState) => ({
      ...prevState,
      groups: {},
    }));
  }, []);

  /**
   * Set the grouping strategy
   */
  const setGroupingStrategy = useCallback((strategy: 'default' | 'ai' | 'ontology'): void => {
    setState((prevState) => ({
      ...prevState,
      groupingStrategy: strategy,
    }));
  }, []);

  /**
   * Set loading state
   */
  const setLoading = useCallback((loading: boolean): void => {
    setState((prevState) => ({
      ...prevState,
      loading,
    }));
  }, []);

  /**
   * Set error state
   */
  const setError = useCallback((error: string | null): void => {
    setState((prevState) => ({
      ...prevState,
      error,
    }));
  }, []);

  // Combine state and actions
  const value: GroupingContextType = {
    ...state,
    setGroups,
    addGroup,
    removeGroup,
    updateGroup,
    addPointToGroup,
    removePointFromGroup,
    movePoint,
    clearGroups,
    setGroupingStrategy,
    setLoading,
    setError,
  };

  return <GroupingContext.Provider value={value}>{children}</GroupingContext.Provider>;
}

/**
 * Hook for using the GroupingContext
 */
export function useGroupingContext(): GroupingContextType {
  const context = useContext(GroupingContext);

  if (!context) {
    throw new Error('useGroupingContext must be used within a GroupingProvider');
  }

  return context;
}

export default GroupingContext; 