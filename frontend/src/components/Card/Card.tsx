import React, { ReactNode } from 'react';
import './Card.css';

/**
 * Card component props interface
 */
export interface CardProps {
  /**
   * Card title
   */
  title?: string;
  
  /**
   * Card subtitle
   */
  subtitle?: string;
  
  /**
   * Card content
   */
  children: ReactNode;
  
  /**
   * Card footer
   */
  footer?: ReactNode;
  
  /**
   * Card icon or image on the left side of the header
   */
  icon?: ReactNode;
  
  /**
   * Card actions (typically buttons) to be displayed in the header
   */
  actions?: ReactNode;
  
  /**
   * Card variant
   */
  variant?: 'default' | 'outline' | 'filled' | 'elevated';
  
  /**
   * Card hover effect
   */
  hoverEffect?: boolean;
  
  /**
   * Card padding
   */
  padding?: 'none' | 'small' | 'medium' | 'large';
  
  /**
   * Whether the card is selected
   */
  selected?: boolean;
  
  /**
   * Whether the card is disabled
   */
  disabled?: boolean;
  
  /**
   * Whether the card is clickable
   */
  clickable?: boolean;
  
  /**
   * Card width (e.g., '300px', '100%')
   */
  width?: string;
  
  /**
   * Card height (e.g., '200px', 'auto')
   */
  height?: string;
  
  /**
   * Card custom className
   */
  className?: string;
  
  /**
   * On click handler
   */
  onClick?: () => void;
  
  /**
   * ID for testing and accessibility
   */
  id?: string;
  
  /**
   * Whether to render a divider between header and content
   */
  headerDivider?: boolean;
  
  /**
   * Whether to render a divider between content and footer
   */
  footerDivider?: boolean;
  
  /**
   * Card background color
   */
  backgroundColor?: string;
  
  /**
   * Card border color
   */
  borderColor?: string;
}

/**
 * Card component
 * 
 * A flexible card component for displaying content in a contained format
 */
const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  children,
  footer,
  icon,
  actions,
  variant = 'default',
  hoverEffect = false,
  padding = 'medium',
  selected = false,
  disabled = false,
  clickable = false,
  width,
  height,
  className = '',
  onClick,
  id,
  headerDivider = true,
  footerDivider = true,
  backgroundColor,
  borderColor,
}) => {
  const hasHeader = title || subtitle || icon || actions;
  
  const cardClasses = [
    'bms-card',
    `bms-card--${variant}`,
    `bms-card--padding-${padding}`,
    hoverEffect ? 'bms-card--hover' : '',
    selected ? 'bms-card--selected' : '',
    disabled ? 'bms-card--disabled' : '',
    clickable ? 'bms-card--clickable' : '',
    className,
  ].filter(Boolean).join(' ');
  
  const cardStyle = {
    width,
    height,
    backgroundColor,
    borderColor,
  };
  
  const handleClick = () => {
    if (!disabled && onClick) {
      onClick();
    }
  };
  
  return (
    <div
      className={cardClasses}
      style={cardStyle}
      onClick={handleClick}
      id={id}
      role={clickable ? 'button' : undefined}
      tabIndex={clickable ? 0 : undefined}
      aria-disabled={disabled}
    >
      {hasHeader && (
        <div className={`bms-card__header ${headerDivider ? 'bms-card__header--divider' : ''}`}>
          {icon && <div className="bms-card__icon">{icon}</div>}
          
          {(title || subtitle) && (
            <div className="bms-card__titles">
              {title && <h3 className="bms-card__title">{title}</h3>}
              {subtitle && <div className="bms-card__subtitle">{subtitle}</div>}
            </div>
          )}
          
          {actions && <div className="bms-card__actions">{actions}</div>}
        </div>
      )}
      
      <div className="bms-card__content">
        {children}
      </div>
      
      {footer && (
        <div className={`bms-card__footer ${footerDivider ? 'bms-card__footer--divider' : ''}`}>
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card; 