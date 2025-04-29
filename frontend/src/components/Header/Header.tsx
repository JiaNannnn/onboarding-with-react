import React, { ReactNode } from 'react';
import './Header.css';

/**
 * Header component props interface
 */
export interface HeaderProps {
  /**
   * Logo or brand component
   */
  logo?: ReactNode;
  
  /**
   * Navigation items to display in the header
   */
  navigationItems?: ReactNode;
  
  /**
   * Actions on the right side (e.g., profile, notifications)
   */
  actions?: ReactNode;
  
  /**
   * Title text to display in the header
   */
  title?: string;
  
  /**
   * Subtitle text to display under the title
   */
  subtitle?: string;
  
  /**
   * Header variant
   */
  variant?: 'default' | 'compact' | 'transparent' | 'colored';
  
  /**
   * Whether to make the header sticky
   */
  sticky?: boolean;
  
  /**
   * Custom background color
   */
  backgroundColor?: string;
  
  /**
   * Custom text color
   */
  textColor?: string;
  
  /**
   * Header height
   */
  height?: string;
  
  /**
   * Additional CSS class name
   */
  className?: string;
  
  /**
   * Whether to show a border at the bottom
   */
  showBorder?: boolean;
  
  /**
   * Whether to show a shadow
   */
  showShadow?: boolean;
  
  /**
   * Custom content for the left section
   */
  leftContent?: ReactNode;
  
  /**
   * Custom content for the middle section
   */
  middleContent?: ReactNode;
  
  /**
   * Custom content for the right section
   */
  rightContent?: ReactNode;
  
  /**
   * Whether to show the toggle sidebar button
   */
  showSidebarToggle?: boolean;
  
  /**
   * Handler for sidebar toggle button click
   */
  onSidebarToggle?: () => void;
  
  /**
   * ID for testing purposes
   */
  id?: string;
}

/**
 * Header component
 * 
 * Application header that typically contains navigation and actions
 */
const Header: React.FC<HeaderProps> = ({
  logo,
  navigationItems,
  actions,
  title,
  subtitle,
  variant = 'default',
  sticky = false,
  backgroundColor,
  textColor,
  height,
  className = '',
  showBorder = true,
  showShadow = true,
  leftContent,
  middleContent,
  rightContent,
  showSidebarToggle = false,
  onSidebarToggle,
  id,
}) => {
  // Combine class names
  const headerClasses = [
    'bms-header',
    `bms-header--${variant}`,
    sticky ? 'bms-header--sticky' : '',
    showBorder ? 'bms-header--bordered' : '',
    showShadow ? 'bms-header--shadow' : '',
    className,
  ].filter(Boolean).join(' ');
  
  // Apply custom styles
  const headerStyle = {
    backgroundColor,
    color: textColor,
    height,
  };
  
  const handleSidebarToggle = () => {
    if (onSidebarToggle) {
      onSidebarToggle();
    }
  };
  
  return (
    <header className={headerClasses} style={headerStyle} id={id}>
      {/* Left section */}
      <div className="bms-header__section bms-header__section--left">
        {leftContent || (
          <>
            {showSidebarToggle && (
              <button
                className="bms-header__sidebar-toggle"
                onClick={handleSidebarToggle}
                aria-label="Toggle sidebar"
              >
                <span className="bms-header__sidebar-toggle-icon"></span>
              </button>
            )}
            
            {logo && (
              <div className="bms-header__logo">
                {logo}
              </div>
            )}
            
            {(title || subtitle) && (
              <div className="bms-header__titles">
                {title && <h1 className="bms-header__title">{title}</h1>}
                {subtitle && <div className="bms-header__subtitle">{subtitle}</div>}
              </div>
            )}
          </>
        )}
      </div>
      
      {/* Middle section */}
      <div className="bms-header__section bms-header__section--middle">
        {middleContent || (
          navigationItems && (
            <nav className="bms-header__navigation">
              {navigationItems}
            </nav>
          )
        )}
      </div>
      
      {/* Right section */}
      <div className="bms-header__section bms-header__section--right">
        {rightContent || (
          actions && (
            <div className="bms-header__actions">
              {actions}
            </div>
          )
        )}
      </div>
    </header>
  );
};

export default Header; 