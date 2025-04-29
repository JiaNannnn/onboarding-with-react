/**
 * Common type definitions
 */

/**
 * Type for nullable values
 */
export type Nullable<T> = T | null;

/**
 * Type for undefined values
 */
export type Optional<T> = T | undefined;

/**
 * Type for unique identifier
 */
export type ID = string;

/**
 * Type for a function that takes any arguments and returns nothing
 */
export type VoidFunction = (...args: any[]) => void;

/**
 * Type for a function that takes any arguments and returns a Promise with no value
 */
export type AsyncVoidFunction = (...args: any[]) => Promise<void>;

/**
 * Type for a validation result
 */
export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

/**
 * Type for log levels
 */
export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
}

/**
 * Type for a log entry
 */
export interface LogEntry {
  timestamp: Date;
  level: LogLevel;
  message: string;
  data?: Record<string, unknown>;
} 