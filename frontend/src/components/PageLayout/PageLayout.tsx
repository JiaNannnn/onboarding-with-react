import React from 'react';
import './PageLayout.css';

interface PageLayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
}

/**
 * Page layout component with optional sidebar
 */
const PageLayout: React.FC<PageLayoutProps> = ({ children, sidebar }) => {
  return (
    <div className="page-layout">

      {sidebar ? (
        <div className="page-layout__with-sidebar">
          <aside className="page-layout__sidebar">
            {sidebar}
          </aside>
          <main className="page-layout__main-with-sidebar">
            {children}
          </main>
        </div>
      ) : (
        <div className="page-layout__content">
          <main className="page-layout__main">
            {children}
          </main>
        </div>
      )}

      <footer className="page-layout__footer">
        <div className="page-layout__footer-copyright">
          © {new Date().getFullYear()} BMS-EnOS Onboarding Tool
        </div>
        <div className="page-layout__footer-links">
          <a href="/" className="page-layout__footer-link">Privacy Policy</a>
          <a href="/" className="page-layout__footer-link">Terms of Service</a>
          <a href="/" className="page-layout__footer-link">Documentation</a>
        </div>
      </footer>
    </div>
  );
};

export default PageLayout; 