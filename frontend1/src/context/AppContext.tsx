import React, { createContext, useContext, useState } from 'react';

export type AppContextType = {
  rawPoints: any[];
  setRawPoints: (points: any[]) => void;
  groupPointsByProperty: (points: any[], property: string) => any;
  hierarchicalGroups: Record<string, any>;
  setHierarchicalGroups: (groups: Record<string, any>) => void;
  pointTags: Record<string, string[]>;
  setPointTags: (tags: Record<string, string[]>) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
};

const AppContext = createContext<AppContextType | null>(null);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [rawPoints, setRawPoints] = useState<any[]>([]);
  const [hierarchicalGroups, setHierarchicalGroups] = useState<Record<string, any>>({});
  const [pointTags, setPointTags] = useState<Record<string, string[]>>({});
  const [loading, setLoading] = useState(false);

  const groupPointsByProperty = (points: any[], property: string) => {
    return points.reduce((groups: any, point: any) => {
      const value = point[property];
      if (!groups[value]) {
        groups[value] = [];
      }
      groups[value].push(point);
      return groups;
    }, {});
  };

  return (
    <AppContext.Provider
      value={{
        rawPoints,
        setRawPoints,
        groupPointsByProperty,
        hierarchicalGroups,
        setHierarchicalGroups,
        pointTags,
        setPointTags,
        loading,
        setLoading,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => useContext(AppContext);

export default AppContext;
