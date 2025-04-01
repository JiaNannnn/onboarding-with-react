import React, { ReactNode } from 'react';
import './Navigation.css';

/**
 * NavigationItem interface for type-safety
 */
export interface NavigationItem {
  /**
   * Unique ID for the item
   */
  id: string;
  
  /**
   * Display text for the item
   */
  label: string;
  
  /**
   * URL to navigate to
   */
  href?: string;
  
  /**
   * Whether the item is currently active
   */
  isActive?: boolean;
  
  /**
   * Whether the item is disabled
   */
  isDisabled?: boolean;
  
  /**
   * Icon to display with the item
   */
  icon?: ReactNode;
  
  /**
   * Click handler for the item
   */
  onClick?: () => void;
  
  /**
   * Dropdown items for this navigation item
   */
  children?: NavigationItem[];
  
  /**
   * Target attribute for links
   */
  target?: string;
  
  /**
   * Additional attributes for the item
   */
  attributes?: Record<string, string>;
}

/**
 * Navigation component props interface
 */
export interface NavigationProps {
  /**
   * Array of navigation items
   */
  items: NavigationItem[];
  
  /**
   * Orientation of the navigation
   */
  orientation?: 'horizontal' | 'vertical';
  
  /**
   * Variant of the navigation
   */
  variant?: 'default' | 'tabs' | 'pills' | 'underline';
  
  /**
   * Callback when an item is clicked
   */
  onItemClick?: (item: NavigationItem) => void;
  
  /**
   * Whether to collapse on small screens
   */
  collapsible?: boolean;
  
  /**
   * Whether the navigation is expanded when collapsible
   */
  expanded?: boolean;
  
  /**
   * Toggle function for collapsible navigation
   */
  onToggle?: () => void;
  
  /**
   * Label for the toggle button
   */
  toggleLabel?: string;
  
  /**
   * Additional CSS class name
   */
  className?: string;
  
  /**
   * Custom style for active items
   */
  activeStyle?: 'bold' | 'colored' | 'background' | 'none';
  
  /**
   * Spacing between items
   */
  spacing?: 'default' | 'compact' | 'loose';
  
  /**
   * Maximum depth for dropdown menus
   */
  maxDepth?: number;
  
  /**
   * ID for testing purposes
   */
  id?: string;
}

/**
 * Navigation component
 * 
 * A flexible navigation component that can be used in headers, sidebars, or as a standalone component
 */
const Navigation: React.FC<NavigationProps> = ({
  items,
  orientation = 'horizontal',
  variant = 'default',
  onItemClick,
  collapsible = false,
  expanded = false,
  onToggle,
  toggleLabel = 'Menu',
  className = '',
  activeStyle = 'colored',
  spacing = 'default',
  maxDepth = 2,
  id,
}) => {
  // Combine class names
  const navClasses = [
    'bms-nav',
    `bms-nav--${orientation}`,
    `bms-nav--${variant}`,
    `bms-nav--active-${activeStyle}`,
    `bms-nav--spacing-${spacing}`,
    collapsible ? 'bms-nav--collapsible' : '',
    expanded ? 'bms-nav--expanded' : '',
    className,
  ].filter(Boolean).join(' ');
  
  // Handle item click
  const handleItemClick = (item: NavigationItem) => {
    if (item.isDisabled) {
      return;
    }
    
    if (item.onClick) {
      item.onClick();
    }
    
    if (onItemClick) {
      onItemClick(item);
    }
  };
  
  // Handle toggle click
  const handleToggle = () => {
    if (onToggle) {
      onToggle();
    }
  };
  
  // Render a navigation item (recursive for dropdowns)
  const renderItem = (item: NavigationItem, depth = 0) => {
    const hasChildren = item.children && item.children.length > 0 && depth < maxDepth;
    
    const itemClasses = [
      'bms-nav__item',
      item.isActive ? 'bms-nav__item--active' : '',
      item.isDisabled ? 'bms-nav__item--disabled' : '',
      hasChildren ? 'bms-nav__item--has-children' : '',
    ].filter(Boolean).join(' ');
    
    return (
      <li 
        key={item.id} 
        className={itemClasses}
        {...item.attributes}
      >
        {item.href && !item.isDisabled ? (
          <a 
            href={item.href} 
            className="bms-nav__link"
            onClick={() => handleItemClick(item)}
            target={item.target}
          >
            {item.icon && <span className="bms-nav__icon">{item.icon}</span>}
            <span className="bms-nav__label">{item.label}</span>
            {hasChildren && <span className="bms-nav__dropdown-icon">▼</span>}
          </a>
        ) : (
          <button 
            className="bms-nav__button"
            onClick={() => handleItemClick(item)}
            disabled={item.isDisabled}
          >
            {item.icon && <span className="bms-nav__icon">{item.icon}</span>}
            <span className="bms-nav__label">{item.label}</span>
            {hasChildren && <span className="bms-nav__dropdown-icon">▼</span>}
          </button>
        )}
        
        {hasChildren && (
          <ul className="bms-nav__dropdown">
            {item.children!.map(child => renderItem(child, depth + 1))}
          </ul>
        )}
      </li>
    );
  };
  
  return (
    <nav className={navClasses} id={id}>
      {collapsible && (
        <button 
          className="bms-nav__toggle" 
          onClick={handleToggle}
          aria-expanded={expanded}
          aria-controls="bms-nav-menu"
        >
          <span className="bms-nav__toggle-icon"></span>
          <span className="bms-nav__toggle-label">{toggleLabel}</span>
        </button>
      )}
      
      <ul 
        className="bms-nav__menu" 
        id="bms-nav-menu" 
        aria-hidden={collapsible && !expanded}
      >
        {items.map(item => renderItem(item))}
      </ul>
    </nav>
  );
};

export default Navigation; 