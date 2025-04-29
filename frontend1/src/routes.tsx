import React, { lazy, Suspense } from 'react';
import { Navigate } from 'react-router-dom';
import { Loading } from './components/common/Loading';

// Lazy load page components
const Dashboard = lazy(() => import('./pages/Dashboard'));
const FetchPoints = lazy(() => import('./pages/FetchPoints'));
const GroupPoints = lazy(() => import('./pages/GroupPoints'));
const MappingPoints = lazy(() => import('./pages/MappingPoints'));
const SavedMappings = lazy(() => import('./pages/SavedMappings'));

// Loading fallback for lazy-loaded routes
const LoadingFallback = () => <Loading fullPage message="Loading page..." />;

// Route configuration
interface RouteConfig {
  path: string;
  element: React.ReactNode;
  children?: RouteConfig[];
}

const routes: RouteConfig[] = [
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: '/dashboard',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <Dashboard />
      </Suspense>
    ),
  },
  {
    path: '/fetch-points',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <FetchPoints />
      </Suspense>
    ),
  },
  {
    path: '/group-points',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <GroupPoints />
      </Suspense>
    ),
  },
  {
    path: '/mapping-points',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <MappingPoints />
      </Suspense>
    ),
  },
  {
    path: '/saved-mappings',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <SavedMappings />
      </Suspense>
    ),
  },
];

export default routes;
