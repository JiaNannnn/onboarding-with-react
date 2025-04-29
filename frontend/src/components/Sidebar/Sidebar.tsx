import React, { ReactNode } from 'react';
import './Sidebar.css';

/**
 * SidebarItem interface for type-safe sidebar navigation items
 */
export interface SidebarItem {
  /**
   * Unique ID for the item
   */
  id: string;
  
  /**
   * Display label for the item
   */
  label: string;
  
  /**
   * Icon for the item
   */
  icon?: ReactNode;
  
  /**
   * URL to navigate to when clicked
   */
  href?: string;
  
  /**
   * Whether the item is currently active
   */
  isActive?: boolean;
  
  /**
   * Whether the item is currently disabled
   */
  isDisabled?: boolean;
  
  /**
   * Click handler for the item
   */
  onClick?: () => void;
  
  /**
   * Nested items for a collapsible section
   */
  children?: SidebarItem[];
  
  /**
   * Whether the collapsible section is expanded
   */
  isExpanded?: boolean;
  
  /**
   * Badge text or element to display next to the item
   */
  badge?: ReactNode;
}

/**
 * SidebarSection interface for grouping items
 */
export interface SidebarSection {
  /**
   * Unique ID for the section
   */
  id: string;
  
  /**
   * Display title for the section
   */
  title?: string;
  
  /**
   * Items in this section
   */
  items: SidebarItem[];
}

/**
 * Sidebar component props interface
 */
export interface SidebarProps {
  /**
   * Array of top-level items
   */
  items?: SidebarItem[];
  
  /**
   * Array of sections with their own items
   */
  sections?: SidebarSection[];
  
  /**
   * Header content (e.g., logo or title)
   */
  header?: ReactNode;
  
  /**
   * Footer content
   */
  footer?: ReactNode;
  
  /**
   * Whether the sidebar is expanded
   */
  expanded?: boolean;
  
  /**
   * Width of the expanded sidebar
   */
  expandedWidth?: string;
  
  /**
   * Width of the collapsed sidebar
   */
  collapsedWidth?: string;
  
  /**
   * Callback when an item is clicked
   */
  onItemClick?: (item: SidebarItem) => void;
  
  /**
   * Callback when the expand/collapse toggle is clicked
   */
  onToggleExpand?: () => void;
  
  /**
   * Custom trigger element for the expand/collapse toggle
   */
  expandToggleTrigger?: ReactNode;
  
  /**
   * Whether to show the toggle trigger
   */
  showExpandToggle?: boolean;
  
  /**
   * Whether to show tooltips on hover (for collapsed state)
   */
  showTooltips?: boolean;
  
  /**
   * Custom background color
   */
  backgroundColor?: string;
  
  /**
   * Custom text color
   */
  textColor?: string;
  
  /**
   * Sidebar variant
   */
  variant?: 'light' | 'dark' | 'primary' | 'custom';
  
  /**
   * Additional CSS class name
   */
  className?: string;
  
  /**
   * Custom width for items
   */
  itemWidth?: string;
  
  /**
   * Custom height for items
   */
  itemHeight?: string;
  
  /**
   * Whether to show icons only in collapsed mode
   */
  iconsOnly?: boolean;
  
  /**
   * Whether to show dividers between sections
   */
  showDividers?: boolean;
  
  /**
   * ID for testing purposes
   */
  id?: string;
}

/**
 * Sidebar component
 * 
 * Navigation sidebar with support for sections, nested items, and collapsible state
 */
const Sidebar: React.FC<SidebarProps> = ({
  items = [],
  sections = [],
  header,
  footer,
  expanded = true,
  expandedWidth = '260px',
  collapsedWidth = '64px',
  onItemClick,
  onToggleExpand,
  expandToggleTrigger,
  showExpandToggle = true,
  showTooltips = true,
  backgroundColor,
  textColor,
  variant = 'light',
  className = '',
  itemWidth,
  itemHeight,
  iconsOnly = true,
  showDividers = true,
  id,
}) => {
  // Combine class names
  const sidebarClasses = [
    'bms-sidebar',
    `bms-sidebar--${variant}`,
    expanded ? 'bms-sidebar--expanded' : 'bms-sidebar--collapsed',
    showDividers ? 'bms-sidebar--dividers' : '',
    className,
  ].filter(Boolean).join(' ');
  
  // Apply custom styles
  const sidebarStyle = {
    backgroundColor,
    color: textColor,
    width: expanded ? expandedWidth : collapsedWidth,
  };
  
  const handleItemClick = (item: SidebarItem) => {
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
  
  const handleToggleExpand = () => {
    if (onToggleExpand) {
      onToggleExpand();
    }
  };
  
  const renderItem = (item: SidebarItem, level = 0) => {
    const hasChildren = item.children && item.children.length > 0;
    
    const itemClasses = [
      'bms-sidebar__item',
      item.isActive ? 'bms-sidebar__item--active' : '',
      item.isDisabled ? 'bms-sidebar__item--disabled' : '',
      hasChildren ? 'bms-sidebar__item--has-children' : '',
      hasChildren && item.isExpanded ? 'bms-sidebar__item--expanded' : '',
      `bms-sidebar__item--level-${level}`,
    ].filter(Boolean).join(' ');
    
    return (
      <li key={item.id} className={itemClasses}>
        <div
          className="bms-sidebar__item-content"
          onClick={() => handleItemClick(item)}
          style={{ height: itemHeight }}
        >
          {item.icon && (
            <span className="bms-sidebar__item-icon">
              {item.icon}
            </span>
          )}
          
          {(!iconsOnly || expanded) && (
            <span className="bms-sidebar__item-label">
              {item.label}
            </span>
          )}
          
          {item.badge && expanded && (
            <span className="bms-sidebar__item-badge">
              {item.badge}
            </span>
          )}
          
          {hasChildren && expanded && (
            <span className="bms-sidebar__item-expand-icon">
              {/* Arrow icon indicating expandable */}
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path 
                  d={item.isExpanded ? "M4 10L8 6L12 10" : "M4 6L8 10L12 6"} 
                  stroke="currentColor" 
                  strokeWidth="2" 
                  strokeLinecap="round"
                />
              </svg>
            </span>
          )}
        </div>
        
        {hasChildren && item.isExpanded && expanded && (
          <ul className="bms-sidebar__children">
            {item.children?.map(child => renderItem(child, level + 1))}
          </ul>
        )}
      </li>
    );
  };
  
  const renderSection = (section: SidebarSection) => (
    <div key={section.id} className="bms-sidebar__section">
      {section.title && expanded && (
        <div className="bms-sidebar__section-title">
          {section.title}
        </div>
      )}
      <ul className="bms-sidebar__items">
        {section.items.map(item => renderItem(item))}
      </ul>
    </div>
  );
  
  const renderToggle = () => (
    <button
      className="bms-sidebar__toggle"
      onClick={handleToggleExpand}
      aria-label={expanded ? 'Collapse sidebar' : 'Expand sidebar'}
    >
      {expandToggleTrigger || (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path 
            d={expanded ? "M10 4L6 8L10 12" : "M6 4L10 8L6 12"} 
            stroke="currentColor" 
            strokeWidth="2" 
            strokeLinecap="round"
          />
        </svg>
      )}
    </button>
  );
  
  return (
    <aside className={sidebarClasses} style={sidebarStyle} id={id}>
      {header && (
        <div className="bms-sidebar__header">
          {header}
          {showExpandToggle && renderToggle()}
        </div>
      )}
      
      <div className="bms-sidebar__content">
        {items.length > 0 && (
          <ul className="bms-sidebar__items">
            {items.map(item => renderItem(item))}
          </ul>
        )}
        
        {sections.map(section => renderSection(section))}
      </div>
      
      {footer && (
        <div className="bms-sidebar__footer">
          {footer}
        </div>
      )}
    </aside>
  );
};

export default Sidebar; 