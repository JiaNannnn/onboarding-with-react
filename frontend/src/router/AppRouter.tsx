import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ApiAnalytics, MigrationAssistant, GroupPoints, MapPoints, FetchBMSPoints, EnosMigration } from '../pages';
import './AppRouter.css';

/**
 * Application router component
 * Includes GroupPoints page and developer tools for API migration
 */
const AppRouter: React.FC = () => {
  return (
    <Routes>
      {/* Default redirect to Group Points */}
      <Route path="/" element={<Navigate to="/fetch-bms-points" replace />} />
      
      {/* Main pages */}
      <Route path="/group-points" element={<GroupPoints />} />
      <Route path="/map-points" element={<MapPoints />} />
      <Route path="/fetch-bms-points" element={<FetchBMSPoints />} />
      <Route path="/enos-migration" element={<EnosMigration />} />
      
      {/* Developer tools */}
      <Route path="/dev/api-analytics" element={<ApiAnalytics />} />
      <Route path="/dev/migration-assistant" element={<MigrationAssistant />} />
      
      {/* Fallback for unknown routes */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

/**
 * Not Found (404) component
 */
const NotFound: React.FC = () => {
  return (
    <div className="not-found">
      <h1>404 - Not Found</h1>
      <p>The page you're looking for doesn't exist.</p>
      <button onClick={() => window.history.back()}>Go Back</button>
    </div>
  );
};

export default AppRouter;