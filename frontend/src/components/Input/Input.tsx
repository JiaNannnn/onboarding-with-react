import React, { InputHTMLAttributes, forwardRef, ReactNode } from 'react';
import './Input.css';

/**
 * Input component props interface
 */
export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  /**
   * Input label
   */
  label?: string;
  
  /**
   * Error message
   */
  error?: string;
  
  /**
   * Helper text
   */
  helperText?: string;
  
  /**
   * Input size
   */
  size?: 'small' | 'medium' | 'large';
  
  /**
   * Input variant
   */
  variant?: 'outlined' | 'filled' | 'standard';
  
  /**
   * Start icon
   */
  startIcon?: ReactNode;
  
  /**
   * End icon
   */
  endIcon?: ReactNode;
  
  /**
   * Full width input
   */
  fullWidth?: boolean;
  
  /**
   * Input placeholder
   */
  placeholder?: string;
}

/**
 * Input component
 */
const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      size = 'medium',
      variant = 'outlined',
      startIcon,
      endIcon,
      fullWidth = false,
      className = '',
      id,
      ...rest
    },
    ref
  ) => {
    // Generate unique ID if not provided
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
    
    // Create class names based on props
    const baseClass = 'bms-input';
    const containerClasses = [
      baseClass,
      `${baseClass}--${variant}`,
      `${baseClass}--${size}`,
      fullWidth ? `${baseClass}--full-width` : '',
      error ? `${baseClass}--error` : '',
      className,
    ].filter(Boolean).join(' ');
    
    return (
      <div className={containerClasses}>
        {label && (
          <label htmlFor={inputId} className={`${baseClass}__label`}>
            {label}
          </label>
        )}
        
        <div className={`${baseClass}__input-container`}>
          {startIcon && <div className={`${baseClass}__start-icon`}>{startIcon}</div>}
          
          <input
            ref={ref}
            id={inputId}
            className={`${baseClass}__input`}
            aria-invalid={!!error}
            {...rest}
          />
          
          {endIcon && <div className={`${baseClass}__end-icon`}>{endIcon}</div>}
        </div>
        
        {(error || helperText) && (
          <div className={`${baseClass}__helper-text ${error ? `${baseClass}__helper-text--error` : ''}`}>
            {error || helperText}
          </div>
        )}
      </div>
    );
  }
);

// Display name for debugging
Input.displayName = 'Input';

export default Input; 