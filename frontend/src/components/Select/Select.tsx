import React, { SelectHTMLAttributes, forwardRef, ReactNode } from 'react';
import './Select.css';

/**
 * Select option interface
 */
export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

/**
 * Select component props interface
 */
export interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  /**
   * Select label
   */
  label?: string;
  
  /**
   * Options for the select
   */
  options: SelectOption[];
  
  /**
   * Error message
   */
  error?: string;
  
  /**
   * Helper text
   */
  helperText?: string;
  
  /**
   * Select size
   */
  size?: 'small' | 'medium' | 'large';
  
  /**
   * Select variant
   */
  variant?: 'outlined' | 'filled' | 'standard';
  
  /**
   * Start icon
   */
  startIcon?: ReactNode;
  
  /**
   * Full width select
   */
  fullWidth?: boolean;
  
  /**
   * Placeholder text
   */
  placeholder?: string;
}

/**
 * Select component
 */
const Select = forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      label,
      options,
      error,
      helperText,
      size = 'medium',
      variant = 'outlined',
      startIcon,
      fullWidth = false,
      className = '',
      id,
      placeholder,
      ...rest
    },
    ref
  ) => {
    // Generate unique ID if not provided
    const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`;
    
    // Create class names based on props
    const baseClass = 'bms-select';
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
          <label htmlFor={selectId} className={`${baseClass}__label`}>
            {label}
          </label>
        )}
        
        <div className={`${baseClass}__select-container`}>
          {startIcon && <div className={`${baseClass}__start-icon`}>{startIcon}</div>}
          
          <select
            ref={ref}
            id={selectId}
            className={`${baseClass}__select`}
            aria-invalid={!!error}
            {...rest}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            
            {options.map((option) => (
              <option 
                key={option.value} 
                value={option.value} 
                disabled={option.disabled}
              >
                {option.label}
              </option>
            ))}
          </select>
          
          <div className={`${baseClass}__dropdown-icon`}>
            <svg 
              width="10" 
              height="6" 
              viewBox="0 0 10 6" 
              fill="none" 
              xmlns="http://www.w3.org/2000/svg"
            >
              <path 
                d="M1 1L5 5L9 1" 
                stroke="currentColor" 
                strokeWidth="1.5" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
            </svg>
          </div>
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
Select.displayName = 'Select';

export default Select; 