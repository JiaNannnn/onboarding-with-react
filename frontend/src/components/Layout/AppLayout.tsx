import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './AppLayout.css';

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const location = useLocation();

  const navigationItems = [
    
    { path: '/fetch-bms-points', label: 'Fetch BMS Points', icon: '📡' },
    { path: '/group-points', label: 'Group Points', icon: '📑' },
    { path: '/map-points', label: 'Map Points', icon: '🗺️' },
    { path: '/enos-migration', label: 'Enos Migration', icon: '🔁' },
    { path: '/dev/api-analytics', label: 'API Analytics', icon: '📊' },
    { path: '/dev/migration-assistant', label: 'Migration Assistant', icon: '🔧' }
  ];

  return (
    <div className="app-layout">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <h1>API Migration Tools</h1>
        </div>
        <div className="header-right">
          <button className="user-menu">
            <span className="user-icon">👤</span>
            <span>Admin</span>
          </button>
        </div>
      </header>

      {/* Main content with sidebar */}
      <div className="app-main">
        {/* Sidebar */}
        <nav className="app-sidebar">
          {navigationItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </Link>
          ))}
        </nav>

        {/* Main content */}
        <main className="app-content">
          {children}
        </main>
      </div>
    </div>
  );
};