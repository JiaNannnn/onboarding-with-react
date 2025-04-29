/**
 * Error-related type definitions
 */

/**
 * Error severity levels
 */
export enum ErrorSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical',
}

/**
 * Error source types
 */
export enum ErrorSource {
  API = 'api',
  UI = 'ui',
  VALIDATION = 'validation',
  NETWORK = 'network',
  UNKNOWN = 'unknown',
}

/**
 * Base error interface
 */
export interface AppError {
  message: string;
  code?: string;
  source: ErrorSource;
  severity: ErrorSeverity;
  timestamp: Date;
  metadata?: Record<string, unknown>;
}

/**
 * API error interface
 */
export interface ApiError extends AppError {
  source: ErrorSource.API;
  status?: number;
  url?: string;
  method?: string;
}

/**
 * Validation error interface
 */
export interface ValidationError extends AppError {
  source: ErrorSource.VALIDATION;
  field?: string;
  value?: unknown;
  constraints?: Record<string, string>;
}

/**
 * Network error interface
 */
export interface NetworkError extends AppError {
  source: ErrorSource.NETWORK;
  status?: number;
  url?: string;
}

/**
 * Type guard for API errors
 */
export function isApiError(error: AppError): error is ApiError {
  return error.source === ErrorSource.API;
}

/**
 * Type guard for validation errors
 */
export function isValidationError(error: AppError): error is ValidationError {
  return error.source === ErrorSource.VALIDATION;
}

/**
 * Type guard for network errors
 */
export function isNetworkError(error: AppError): error is NetworkError {
  return error.source === ErrorSource.NETWORK;
} 