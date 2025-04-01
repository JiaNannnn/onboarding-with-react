import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { AppLayout } from './components/Layout/AppLayout';
import { AppRouter } from './router';
import { GroupingProvider, MappingProvider, PointsProvider } from './contexts';
import './App.css';

/**
 * Main application component
 * Simplified to only include migration tools
 */
function App() {
  return (
    <Router>
      <PointsProvider>
        <GroupingProvider>
          <MappingProvider>
            <AppLayout>
              <AppRouter />
            </AppLayout>
          </MappingProvider>
        </GroupingProvider>
      </PointsProvider>
    </Router>
  );
}

export default App;