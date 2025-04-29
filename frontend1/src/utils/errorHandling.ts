/**
 * Error handling utilities.
 */

import axios, { AxiosError } from 'axios';

/**
 * Extract an error message from an error object
 */
export const getErrorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }

  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;

    // Check if the response has an error message
    if (axiosError.response?.data && typeof axiosError.response.data === 'object') {
      const data = axiosError.response.data as Record<string, any>;
      if (data.error) {
        return String(data.error);
      }

      if (data.message) {
        return String(data.message);
      }
    }

    // Fall back to status text or generic message
    if (axiosError.response?.statusText) {
      return `${axiosError.response.status}: ${axiosError.response.statusText}`;
    }

    if (axiosError.message) {
      return axiosError.message;
    }
  }

  return String(error) || 'An unknown error occurred';
};

/**
 * Safe parsing of JSON with error handling
 */
export const safeJsonParse = <T>(json: string, defaultValue: T): T => {
  try {
    return JSON.parse(json) as T;
  } catch (error) {
    console.error('Error parsing JSON:', error);
    return defaultValue;
  }
};
