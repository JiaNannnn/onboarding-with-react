import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { HttpMethod } from '../../types/apiTypes';
import { request } from '../../api/apiClient';
import './ProtectedRoute.css';

interface ProtectedRouteProps {
  /** The component to render if authenticated */
  children: React.ReactNode;
  
  /** Optional redirect path if not authenticated */
  redirectTo?: string;
  
  /** Optional array of required roles */
  requiredRoles?: string[];
}

interface AuthCheckResponse {
  authenticated: boolean;
  user?: {
    id: string;
    name: string;
    role: string;
  };
}

/**
 * Protected route component that checks authentication
 * and redirects to login if not authenticated
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  redirectTo = '/login',
  requiredRoles = []
}) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [userRole, setUserRole] = useState<string | null>(null);
  const location = useLocation();
  
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Check if we have a token
        const token = localStorage.getItem('authToken');
        
        if (!token) {
          setIsAuthenticated(false);
          return;
        }
        
        // Verify the token with the server
        const response = await request<AuthCheckResponse>({
          url: '/api/auth/verify',
          method: HttpMethod.GET,
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        
        setIsAuthenticated(response.data?.authenticated || false);
        setUserRole(response.data?.user?.role || null);
      } catch (error) {
        console.error('Auth check error:', error);
        setIsAuthenticated(false);
        setUserRole(null);
        
        // Clear the token if it's invalid
        localStorage.removeItem('authToken');
      }
    };
    
    checkAuth();
  }, []);
  
  // Still checking authentication
  if (isAuthenticated === null) {
    return (
      <div className="loading-spinner-container">
        <div className="loading-spinner"></div>
        <p>Verifying authentication...</p>
      </div>
    );
  }
  
  // Not authenticated, redirect to login
  if (!isAuthenticated) {
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }
  
  // Check role-based access
  if (requiredRoles.length > 0 && (!userRole || !requiredRoles.includes(userRole))) {
    return (
      <div className="access-denied">
        <h1>Access Denied</h1>
        <p>You don't have the required permissions to access this page.</p>
        <p>Please contact your administrator.</p>
      </div>
    );
  }
  
  // Authenticated and has required roles, render the children
  return <>{children}</>;
};

export default ProtectedRoute; 