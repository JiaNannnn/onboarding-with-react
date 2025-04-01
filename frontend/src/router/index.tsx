import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import GroupPoints from '../pages/GroupPoints';

// Commented out unused imports
// import Dashboard from '../pages/Dashboard';
// import FetchPoints from '../pages/FetchPoints';
// import MapPoints from '../pages/MapPoints/MapPoints';
// import SavedMappings from '../pages/SavedMappings';

// Placeholder components until they are created
const Login = () => <div>Login Page</div>;

export const AppRouter: React.FC = () => {
  // TODO: Replace with actual auth check
  const isAuthenticated = true;

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/group-points" element={<GroupPoints />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}; 