import React from 'react';
import { AppProvider } from './AppContext';
import { PointsProvider } from './PointsContext';
import { MappingProvider } from './MappingContext';
import { GroupingProvider } from './GroupingContext';

// Export individual contexts
export { useAppContext } from './AppContext';
export { usePointsContext } from './PointsContext';
export { useMappingContext } from './MappingContext';
export { useGroupingContext } from './GroupingContext';

// Combined provider that wraps all contexts
export const AppContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <AppProvider>
      <PointsProvider>
        <MappingProvider>
          <GroupingProvider>{children}</GroupingProvider>
        </MappingProvider>
      </PointsProvider>
    </AppProvider>
  );
};

export default AppContextProvider;
