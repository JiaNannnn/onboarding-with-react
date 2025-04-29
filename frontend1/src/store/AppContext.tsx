import React, { createContext, useContext, useReducer, ReactNode } from 'react';

// Types
interface Point {
  id: string;
  name: string;
  description: string;
  type: string;
  source: string;
}

interface Group {
  id: string;
  name: string;
  points: Point[];
}

interface Mapping {
  id: string;
  name: string;
  description: string;
  groups: Group[];
  createdAt: string;
  updatedAt: string;
}

interface AppState {
  points: Point[];
  groups: Group[];
  mappings: Mapping[];
  loading: boolean;
  error: string | null;
}

// Action types
type ActionType = 
  | { type: 'SET_POINTS'; payload: Point[] }
  | { type: 'ADD_POINTS'; payload: Point[] }
  | { type: 'REMOVE_POINT'; payload: string }
  | { type: 'SET_GROUPS'; payload: Group[] }
  | { type: 'ADD_GROUP'; payload: Group }
  | { type: 'UPDATE_GROUP'; payload: Group }
  | { type: 'REMOVE_GROUP'; payload: string }
  | { type: 'SET_MAPPINGS'; payload: Mapping[] }
  | { type: 'ADD_MAPPING'; payload: Mapping }
  | { type: 'UPDATE_MAPPING'; payload: Mapping }
  | { type: 'REMOVE_MAPPING'; payload: string }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null };

// Context and provider props
interface AppContextProps {
  state: AppState;
  dispatch: React.Dispatch<ActionType>;
}

interface AppProviderProps {
  children: ReactNode;
}

// Initial state
const initialState: AppState = {
  points: [],
  groups: [],
  mappings: [],
  loading: false,
  error: null
};

// Create context
const AppContext = createContext<AppContextProps | undefined>(undefined);

// Reducer function
const appReducer = (state: AppState, action: ActionType): AppState => {
  switch (action.type) {
    case 'SET_POINTS':
      return { ...state, points: action.payload };
    case 'ADD_POINTS':
      return { ...state, points: [...state.points, ...action.payload] };
    case 'REMOVE_POINT':
      return { 
        ...state, 
        points: state.points.filter(point => point.id !== action.payload) 
      };
    case 'SET_GROUPS':
      return { ...state, groups: action.payload };
    case 'ADD_GROUP':
      return { ...state, groups: [...state.groups, action.payload] };
    case 'UPDATE_GROUP':
      return { 
        ...state, 
        groups: state.groups.map(group => 
          group.id === action.payload.id ? action.payload : group
        ) 
      };
    case 'REMOVE_GROUP':
      return { 
        ...state, 
        groups: state.groups.filter(group => group.id !== action.payload) 
      };
    case 'SET_MAPPINGS':
      return { ...state, mappings: action.payload };
    case 'ADD_MAPPING':
      return { ...state, mappings: [...state.mappings, action.payload] };
    case 'UPDATE_MAPPING':
      return { 
        ...state, 
        mappings: state.mappings.map(mapping => 
          mapping.id === action.payload.id ? action.payload : mapping
        ) 
      };
    case 'REMOVE_MAPPING':
      return { 
        ...state, 
        mappings: state.mappings.filter(mapping => mapping.id !== action.payload) 
      };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    default:
      return state;
  }
};

// Provider component
export const AppContextProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
};

// Custom hook for using the context
export const useAppContext = (): AppContextProps => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppContextProvider');
  }
  return context;
};

// Export types for use in other files
export type { Point, Group, Mapping, AppState, ActionType }; 