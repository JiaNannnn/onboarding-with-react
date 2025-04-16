/**
 * Type-safe API client implementation using Axios
 */

import axios, { AxiosError, AxiosRequestConfig, AxiosInstance } from 'axios';
import { logger } from '../utils/logger';

/**
 * Base API URL for the backend.
 * All requests will be sent to this URL.
 */
const API_BASE_URL = 'http://localhost:5000';

/**
 * Default request timeout in milliseconds
 * Increased timeout (e.g., 15 minutes = 900,000 ms) might be needed for long AI tasks.
 */
const DEFAULT_TIMEOUT = 900000; 

/**
 * Create a pre-configured Axios instance.
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: DEFAULT_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// --- Request Interceptor ---
apiClient.interceptors.request.use(
  (config) => {
    // Log request details
    logger.debug('API Request', { 
      baseURL: config.baseURL, // Should always be API_BASE_URL
      url: config.url, 
      method: config.method, 
      params: config.params,
      // data: config.data, // Avoid logging potentially large data
    });

    // Add authorization header if available (e.g., from localStorage)
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Ensure the URL path starts with a slash if it's relative
    if (config.url && !config.url.startsWith('/') && !config.url.startsWith('http')) {
      config.url = `/${config.url}`;
    }

    return config;
  },
  (error) => {
    logger.error('API Request Interceptor Error', { error });
    return Promise.reject(error);
  }
);

// --- Response Interceptor ---
apiClient.interceptors.response.use(
  (response) => {
    // Log basic response info
    logger.debug('API Response', { 
      url: response.config.url, 
      status: response.status,
      // data: response.data, // Avoid logging potentially large data
    });
    return response;
  },
  (error: AxiosError) => {
    const config = error.config;
    const url = config?.url || 'unknown';
    const method = config?.method || 'unknown';

    if (error.response) {
      // Server responded with an error status code
      const status = error.response.status;
      let message = `API Error (${status})`;
      if (error.response.data) {
        if (typeof error.response.data === 'string') {
          // Handle plain text or HTML errors (like the 405 page)
          if (error.response.data.toLowerCase().includes('method not allowed')) {
            message = `Method ${method?.toUpperCase()} not allowed for URL ${url}`;
          } else {
            message = error.response.data.substring(0, 200); // Limit length
          }
        } else if (typeof error.response.data === 'object') {
          const data = error.response.data as Record<string, unknown>;
          message = (data.message || data.error || data.detail || message) as string;
        }
      }
      
      logger.error(`API Error (${status})`, { url, method, status, responseData: error.response.data });
      // Throw a simplified error object
      throw new Error(message);

    } else if (error.request) {
      // Request was made but no response received (Network error)
      logger.error('API Network Error', { url, method, error: error.message });
      throw new Error('Network error: Could not connect to the server.');

    } else {
      // Error setting up the request
      logger.error('API Client Setup Error', { message: error.message });
      throw new Error(`Client setup error: ${error.message}`);
    }
  }
);

// --- Simplified API Methods ---

/**
 * Makes a GET request.
 * @param url - The relative URL path (e.g., '/api/users')
 * @param params - Optional query parameters.
 * @param config - Optional Axios request configuration overrides.
 * @returns Promise resolving to the response data.
 */
async function get<T>(url: string, params?: Record<string, any>, config?: AxiosRequestConfig): Promise<T> {
  try {
    const response = await apiClient.get<T>(url, { params, ...config });
    return response.data;
  } catch (error) {
    // Logged by interceptor, rethrow simplified error
    throw error; 
  }
}

/**
 * Makes a POST request.
 * @param url - The relative URL path (e.g., '/api/bms/ai-grouping')
 * @param data - The request body data.
 * @param config - Optional Axios request configuration overrides.
 * @returns Promise resolving to the response data.
 */
async function post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  try {
    const response = await apiClient.post<T>(url, data, config);
    return response.data;
  } catch (error) {
    // Logged by interceptor, rethrow simplified error
    throw error;
  }
}

/**
 * Makes a PUT request.
 * @param url - The relative URL path.
 * @param data - The request body data.
 * @param config - Optional Axios request configuration overrides.
 * @returns Promise resolving to the response data.
 */
async function put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  try {
    const response = await apiClient.put<T>(url, data, config);
    return response.data;
  } catch (error) { 
    throw error;
  }
}

/**
 * Makes a DELETE request.
 * @param url - The relative URL path.
 * @param config - Optional Axios request configuration overrides.
 * @returns Promise resolving to the response data.
 */
async function del<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  try {
    const response = await apiClient.delete<T>(url, config);
    return response.data;
  } catch (error) { 
    throw error;
  }
}

// Export the simplified methods directly
export const api = {
  get,
  post,
  put,
  delete: del, // Use 'delete' as the export name
};

// Export default for convenience
export default api;