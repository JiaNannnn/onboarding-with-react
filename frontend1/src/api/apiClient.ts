/**
 * API client for making requests to the backend.
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiResponse } from '../types';

// Create Axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Request interceptor for API calls
apiClient.interceptors.request.use(
  (config) => {
    // You can add auth tokens here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for API calls
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle errors globally
    console.error('API Error:', error);

    // You can add global error handling here
    // For example, handling authentication errors, server errors, etc.

    return Promise.reject(error);
  }
);

/**
 * Generic request function with type safety
 */
export const request = async <T>(config: AxiosRequestConfig): Promise<T> => {
  try {
    const response: AxiosResponse<ApiResponse<T>> = await apiClient(config);

    // Check for API success/error pattern
    if (response.data && response.data.success === false) {
      throw new Error(response.data.error || 'Unknown API error');
    }

    // If response is wrapped in data property, return that
    if (response.data && 'data' in response.data) {
      return response.data.data as T;
    }

    // Otherwise return the whole response data as T
    return response.data as unknown as T;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      // Handle specific HTTP status codes if needed
      const statusCode = error.response.status;
      const errorMessage = error.response.data?.error || error.message;

      throw new Error(`API Error ${statusCode}: ${errorMessage}`);
    }

    // Re-throw other errors
    throw error;
  }
};

export default apiClient;
