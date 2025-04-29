import React, { createContext, useContext, useState, useCallback } from 'react';

// Define types for the context
export interface Point {
  id: string;
  name: string;
  description?: string;
  pointType?: string;
  unit?: string;
  deviceId?: string;
  [key: string]: any;
}

export interface GroupedPoints {
  [groupKey: string]: {
    [instanceKey: string]: Point[];
  };
}

export interface PointTag {
  name: string;
  value: string;
}

export interface PointsContextType {
  points: Point[];
  setPoints: (points: Point[]) => void;
  groupedPoints: GroupedPoints;
  setGroupedPoints: (groupedPoints: GroupedPoints) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
  pointTags: Record<string, string[]>;
  setPointTags: (tags: Record<string, string[]>) => void;
  addTag: (pointId: string, tag: string) => void;
  removeTag: (pointId: string, tag: string) => void;
  loadPoints: (source: string) => Promise<void>;
  groupPoints: (groupBy: string) => void;
}

// Create the context
const PointsContext = createContext<PointsContextType | null>(null);

// Custom hook for using this context
export const usePointsContext = () => {
  const context = useContext(PointsContext);
  if (!context) {
    throw new Error('usePointsContext must be used within a PointsProvider');
  }
  return context;
};

// Provider component
export const PointsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [points, setPoints] = useState<Point[]>([]);
  const [groupedPoints, setGroupedPoints] = useState<GroupedPoints>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [pointTags, setPointTags] = useState<Record<string, string[]>>({});

  // Load points from various sources
  const loadPoints = useCallback(async (source: string) => {
    setLoading(true);
    setError(null);

    try {
      // This would be replaced with actual API calls
      if (source === 'api') {
        // Simulate API call
        const response = await fetch('/api/v1/bms/points');

        if (!response.ok) {
          throw new Error(`Failed to fetch points: ${response.statusText}`);
        }

        const data = await response.json();

        if (!data.success) {
          throw new Error(data.error || 'Failed to load points');
        }

        setPoints(data.points);
      } else if (source === 'csv') {
        // CSV processing would be handled separately
        // This is just a placeholder
      } else if (source === 'demo') {
        // Load demo data
        const demoPoints: Point[] = [
          {
            id: '1',
            name: 'AHU-1-SupplyTemp',
            pointType: 'temperature',
            unit: 'C',
            description: 'Supply Air Temperature',
          },
          {
            id: '2',
            name: 'AHU-1-ReturnTemp',
            pointType: 'temperature',
            unit: 'C',
            description: 'Return Air Temperature',
          },
          {
            id: '3',
            name: 'AHU-1-FanStatus',
            pointType: 'status',
            description: 'Supply Fan Status',
          },
          {
            id: '4',
            name: 'AHU-1-FanSpeed',
            pointType: 'speed',
            unit: '%',
            description: 'Supply Fan Speed',
          },
          {
            id: '5',
            name: 'AHU-1-DamperPosition',
            pointType: 'position',
            unit: '%',
            description: 'Outdoor Air Damper Position',
          },
          {
            id: '6',
            name: 'VAV-1-ZoneTemp',
            pointType: 'temperature',
            unit: 'C',
            description: 'Zone Temperature',
          },
          {
            id: '7',
            name: 'VAV-1-Setpoint',
            pointType: 'setpoint',
            unit: 'C',
            description: 'Zone Temperature Setpoint',
          },
          {
            id: '8',
            name: 'VAV-1-Airflow',
            pointType: 'flow',
            unit: 'CFM',
            description: 'Zone Airflow',
          },
          {
            id: '9',
            name: 'VAV-2-ZoneTemp',
            pointType: 'temperature',
            unit: 'C',
            description: 'Zone Temperature',
          },
          {
            id: '10',
            name: 'VAV-2-Setpoint',
            pointType: 'setpoint',
            unit: 'C',
            description: 'Zone Temperature Setpoint',
          },
        ];

        setPoints(demoPoints);

        // Initialize tags for demo points
        const initialTags: Record<string, string[]> = {};
        demoPoints.forEach((point) => {
          initialTags[point.id] = [];
        });

        setPointTags(initialTags);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      console.error('Error loading points:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Group points by a specific property
  const groupPoints = useCallback(
    (groupBy: string) => {
      setLoading(true);

      try {
        // Simple grouping function
        const grouped: GroupedPoints = {};

        points.forEach((point) => {
          // Default grouping by type if the specified property doesn't exist
          const groupKey = point[groupBy] || point.pointType || 'unknown';

          // Try to extract an instance identifier from the name
          let instanceKey = 'default';

          // For example, extract AHU-1 from AHU-1-SupplyTemp
          const nameParts = point.name.split('-');
          if (nameParts.length >= 2) {
            instanceKey = `${nameParts[0]}-${nameParts[1]}`;
          }

          // Initialize group if it doesn't exist
          if (!grouped[groupKey]) {
            grouped[groupKey] = {};
          }

          // Initialize instance if it doesn't exist
          if (!grouped[groupKey][instanceKey]) {
            grouped[groupKey][instanceKey] = [];
          }

          // Add point to the group
          grouped[groupKey][instanceKey].push(point);
        });

        setGroupedPoints(grouped);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred while grouping points');
        console.error('Error grouping points:', err);
      } finally {
        setLoading(false);
      }
    },
    [points]
  );

  // Add a tag to a point
  const addTag = useCallback((pointId: string, tag: string) => {
    setPointTags((prevTags) => {
      const currentTags = prevTags[pointId] || [];

      // Only add if not already present
      if (!currentTags.includes(tag)) {
        return {
          ...prevTags,
          [pointId]: [...currentTags, tag],
        };
      }

      return prevTags;
    });
  }, []);

  // Remove a tag from a point
  const removeTag = useCallback((pointId: string, tag: string) => {
    setPointTags((prevTags) => {
      const currentTags = prevTags[pointId] || [];

      return {
        ...prevTags,
        [pointId]: currentTags.filter((t) => t !== tag),
      };
    });
  }, []);

  // Context value
  const value: PointsContextType = {
    points,
    setPoints,
    groupedPoints,
    setGroupedPoints,
    loading,
    setLoading,
    error,
    setError,
    pointTags,
    setPointTags,
    addTag,
    removeTag,
    loadPoints,
    groupPoints,
  };

  return <PointsContext.Provider value={value}>{children}</PointsContext.Provider>;
};

export default PointsContext;
