import React, { createContext, useContext, useReducer, ReactNode, useCallback } from 'react';
import { BMSPoint } from '../types/apiTypes';

// Define the state interface
interface PointsState {
  points: BMSPoint[];
  selectedPoints: BMSPoint[];
  filteredPoints: BMSPoint[];
  isLoading: boolean;
  error: string | null;
}

// Define the action types
type PointsAction =
  | { type: 'SET_POINTS'; payload: BMSPoint[] }
  | { type: 'ADD_POINTS'; payload: BMSPoint[] }
  | { type: 'SELECT_POINT'; payload: BMSPoint }
  | { type: 'DESELECT_POINT'; payload: string }
  | { type: 'SELECT_POINTS'; payload: BMSPoint[] }
  | { type: 'DESELECT_POINTS'; payload: string[] }
  | { type: 'SELECT_ALL_POINTS' }
  | { type: 'DESELECT_ALL_POINTS' }
  | { type: 'FILTER_POINTS'; payload: { searchTerm: string; pointTypes?: string[] } }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'RESET' };

// Define the context interface
interface PointsContextType {
  state: PointsState;
  setPoints: (points: BMSPoint[]) => void;
  addPoints: (points: BMSPoint[]) => void;
  selectPoint: (point: BMSPoint) => void;
  deselectPoint: (pointId: string) => void;
  selectPoints: (points: BMSPoint[]) => void;
  deselectPoints: (pointIds: string[]) => void;
  selectAllPoints: () => void;
  deselectAllPoints: () => void;
  filterPoints: (searchTerm: string, pointTypes?: string[]) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

// Create the context
const PointsContext = createContext<PointsContextType | undefined>(undefined);

// Initial state
const initialState: PointsState = {
  points: [],
  selectedPoints: [],
  filteredPoints: [],
  isLoading: false,
  error: null,
};

// Reducer function
function pointsReducer(state: PointsState, action: PointsAction): PointsState {
  switch (action.type) {
    case 'SET_POINTS':
      return {
        ...state,
        points: action.payload,
        filteredPoints: action.payload,
      };
    case 'ADD_POINTS':
      // Avoid duplicates by checking IDs
      const newPoints = action.payload.filter(
        (newPoint) => !state.points.some((p) => p.id === newPoint.id)
      );
      const updatedPoints = [...state.points, ...newPoints];
      return {
        ...state,
        points: updatedPoints,
        filteredPoints: updatedPoints,
      };
    case 'SELECT_POINT':
      // Don't add if already selected
      if (state.selectedPoints.some((p) => p.id === action.payload.id)) {
        return state;
      }
      return {
        ...state,
        selectedPoints: [...state.selectedPoints, action.payload],
      };
    case 'DESELECT_POINT':
      return {
        ...state,
        selectedPoints: state.selectedPoints.filter((p) => p.id !== action.payload),
      };
    case 'SELECT_POINTS':
      const existingIds = new Set(state.selectedPoints.map((p) => p.id));
      const pointsToAdd = action.payload.filter((p) => !existingIds.has(p.id));
      return {
        ...state,
        selectedPoints: [...state.selectedPoints, ...pointsToAdd],
      };
    case 'DESELECT_POINTS':
      const idsToRemove = new Set(action.payload);
      return {
        ...state,
        selectedPoints: state.selectedPoints.filter((p) => !idsToRemove.has(p.id)),
      };
    case 'SELECT_ALL_POINTS':
      return {
        ...state,
        selectedPoints: [...state.filteredPoints],
      };
    case 'DESELECT_ALL_POINTS':
      return {
        ...state,
        selectedPoints: [],
      };
    case 'FILTER_POINTS': {
      const { searchTerm, pointTypes } = action.payload;
      const filtered = state.points.filter((point) => {
        const matchesSearch =
          searchTerm === '' ||
          point.pointName.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (point.description && point.description.toLowerCase().includes(searchTerm.toLowerCase()));
        
        const matchesType = !pointTypes || pointTypes.length === 0 || pointTypes.includes(point.pointType);
        
        return matchesSearch && matchesType;
      });
      return {
        ...state,
        filteredPoints: filtered,
      };
    }
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
      };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}

// Provider component
interface PointsProviderProps {
  children: ReactNode;
}

export const PointsProvider: React.FC<PointsProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(pointsReducer, initialState);

  // Actions
  const setPoints = useCallback((points: BMSPoint[]) => {
    dispatch({ type: 'SET_POINTS', payload: points });
  }, []);

  const addPoints = useCallback((points: BMSPoint[]) => {
    dispatch({ type: 'ADD_POINTS', payload: points });
  }, []);

  const selectPoint = useCallback((point: BMSPoint) => {
    dispatch({ type: 'SELECT_POINT', payload: point });
  }, []);

  const deselectPoint = useCallback((pointId: string) => {
    dispatch({ type: 'DESELECT_POINT', payload: pointId });
  }, []);

  const selectPoints = useCallback((points: BMSPoint[]) => {
    dispatch({ type: 'SELECT_POINTS', payload: points });
  }, []);

  const deselectPoints = useCallback((pointIds: string[]) => {
    dispatch({ type: 'DESELECT_POINTS', payload: pointIds });
  }, []);

  const selectAllPoints = useCallback(() => {
    dispatch({ type: 'SELECT_ALL_POINTS' });
  }, []);

  const deselectAllPoints = useCallback(() => {
    dispatch({ type: 'DESELECT_ALL_POINTS' });
  }, []);

  const filterPoints = useCallback((searchTerm: string, pointTypes?: string[]) => {
    dispatch({ type: 'FILTER_POINTS', payload: { searchTerm, pointTypes } });
  }, []);

  const setLoading = useCallback((isLoading: boolean) => {
    dispatch({ type: 'SET_LOADING', payload: isLoading });
  }, []);

  const setError = useCallback((error: string | null) => {
    dispatch({ type: 'SET_ERROR', payload: error });
  }, []);

  const reset = useCallback(() => {
    dispatch({ type: 'RESET' });
  }, []);

  const value = {
    state,
    setPoints,
    addPoints,
    selectPoint,
    deselectPoint,
    selectPoints,
    deselectPoints,
    selectAllPoints,
    deselectAllPoints,
    filterPoints,
    setLoading,
    setError,
    reset,
  };

  return <PointsContext.Provider value={value}>{children}</PointsContext.Provider>;
};

// Custom hook for using the context
export const usePoints = (): PointsContextType => {
  const context = useContext(PointsContext);
  if (context === undefined) {
    throw new Error('usePoints must be used within a PointsProvider');
  }
  return context;
};

export default PointsContext; 