import React from 'react';
import './Button.css';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Button variants */
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'text';
  
  /** Button sizes */
  size?: 'small' | 'medium' | 'large';
  
  /** Full width button */
  fullWidth?: boolean;
  
  /** Is the button in a loading state */
  isLoading?: boolean;
  
  /** Loading text to display when isLoading is true */
  loadingText?: string;
  
  /** Optional icon to display before text */
  icon?: React.ReactNode;
  
  /** Option custom CSS class */
  className?: string;
  
  /** Children elements */
  children: React.ReactNode;
}

/**
 * Button component with different variants, sizes and states
 */
const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'medium',
  fullWidth = false,
  isLoading = false,
  loadingText,
  icon,
  className = '',
  children,
  disabled,
  ...restProps
}) => {
  // Compute class names
  const buttonClass = `
    button 
    button--${variant} 
    button--${size}
    ${fullWidth ? 'button--full-width' : ''}
    ${isLoading ? 'button--loading' : ''}
    ${className}
  `.trim().replace(/\s+/g, ' ');
  
  return (
    <button
      className={buttonClass}
      disabled={isLoading || disabled}
      {...restProps}
    >
      {isLoading ? (
        <>
          <span className="button__spinner"></span>
          {loadingText || children}
        </>
      ) : (
        <>
          {icon && <span className="button__icon">{icon}</span>}
          {children}
        </>
      )}
    </button>
  );
};

export default Button; 