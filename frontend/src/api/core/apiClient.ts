import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';
import { AppError, ErrorSource, ErrorSeverity, ApiError, NetworkError } from '../../types/errorTypes';
import { ApiResponse } from '../../types/apiTypes';
import { logger } from '../../utils/logger';

/**
 * Base API URL - IMPORTANT: This is the only allowed base URL for API requests.
 * All API gateway URLs must be passed as parameters in the request body.
 */
const API_BASE_URL = 'http://localhost:5000';

/**
 * Default request timeout in milliseconds
 * 10 minutes = 600,000 milliseconds
 */
const DEFAULT_TIMEOUT = 600000;

/**
 * API Client configuration interface
 */
export interface APIClientConfig {
  // baseURL is no longer configurable - only used internally
  accessKey?: string;
  secretKey?: string;
  timeout?: number;
  headers?: Record<string, string>;
  // Allow passing apiGateway as a parameter in the request body
  apiGateway?: string;
  orgId?: string;
  assetId?: string;
}

/**
 * Centralized API Client for making requests to backend services
 */
export class APIClient {
  private headers: Record<string, string>;
  private timeout: number;
  private apiInstance: AxiosInstance;
  // API gateway for request params (not baseURL)
  private apiGateway?: string;
  private orgId?: string;
  private assetId?: string;

  /**
   * Create a new API client instance
   */
  constructor(config: APIClientConfig = {}) {
    // Store API gateway for request params, but never use as baseURL
    this.apiGateway = config.apiGateway;
    this.orgId = config.orgId;
    this.assetId = config.assetId;
    this.timeout = config.timeout || DEFAULT_TIMEOUT;
    this.headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...config.headers,
    };

    // Add auth headers if provided
    if (config.accessKey) {
      this.headers['AccessKey'] = config.accessKey;
      this.headers['x-access-key'] = config.accessKey;
    }
    if (config.secretKey) {
      this.headers['SecretKey'] = config.secretKey;
      this.headers['x-secret-key'] = config.secretKey;
    }

    // Create Axios instance with interceptors
    this.apiInstance = axios.create({
      baseURL: API_BASE_URL,
      timeout: this.timeout,
      headers: this.headers,
    });

    // Set up interceptors
    this.setupInterceptors();
  }

  /**
   * Set up request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor
    this.apiInstance.interceptors.request.use(
      (config) => {
        logger.debug('API Request', { 
          url: config.url, 
          method: config.method, 
          params: config.params,
          data: config.data,
        });
        
        // Add authorization header if user is logged in
        const token = localStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        // ENFORCED RULE: All requests must go through localhost:5000
        // Override any baseURL that is not localhost:5000
        config.baseURL = API_BASE_URL;
        
        // Ensure the URL starts with the base URL if it's a relative path
        if (config.url && !config.url.startsWith('http')) {
          config.url = `${API_BASE_URL}${config.url.startsWith('/') ? '' : '/'}${config.url}`;
        }
        
        // If someone tried to use a full URL (starting with http), force it to use our API_BASE_URL
        if (config.url && config.url.startsWith('http')) {
          // Extract the path part only from the URL
          try {
            const urlObj = new URL(config.url);
            config.url = urlObj.pathname + urlObj.search;
            // Log a warning about the override
            logger.warn('Attempted to use external URL as base. Enforcing localhost:5000', {
              originalUrl: config.url,
              newUrl: `${API_BASE_URL}${config.url}`
            });
          } catch (e) {
            // If URL parsing fails, just use the original URL with warning
            logger.error('Failed to parse URL, falling back to relative path', { url: config.url });
          }
        }
        
        // Special handling for problematic endpoints that might need different methods
        if (config.url && (
            config.url.includes('/api/bms/map-points') ||
            config.url.includes('/bms/map-points') ||
            config.url.includes('/api/v1/map-points') ||
            config.url.includes('/v1/map-points')
        )) {
            logger.info(`Special handling for map-points URL: ${config.url}`);
            
            // If it's a POST request for map-points, make sure it uses the right URL format
            if (config.method?.toLowerCase() === 'post') {
                // Ensure we're using the format the server expects
                if (!config.url.startsWith('/api/v1/map-points')) {
                    config.url = '/api/v1/map-points';
                    logger.info(`Normalized map-points URL to: ${config.url}`);
                }
                
                // Check if the URL starts with a slash
                if (!config.url.startsWith('/')) {
                    config.url = '/' + config.url;
                }
                
                // Make sure content type is set properly
                if (config.headers) {
                    // Use computed property to safely set the header
                    config.headers['Content-Type'] = 'application/json';
                }
            } 
            // For GET requests (status checking), make sure we use the right format
            else if (config.method?.toLowerCase() === 'get' && (config.url.includes('/map-points/') || config.url.includes('map-points%2F'))) {
                // Extract task ID from URL, handling both encoded and unencoded paths
                let taskId = '';
                const match1 = config.url.match(/\/map-points\/([^/?]+)/);
                const match2 = config.url.match(/\/map-points%2F([^/?]+)/);
                
                if (match1 && match1[1]) {
                    taskId = match1[1];
                } else if (match2 && match2[1]) {
                    taskId = match2[1];
                }
                
                if (taskId) {
                    config.url = `/api/v1/map-points/${taskId}`;
                    logger.info(`Normalized map-points status URL to: ${config.url}`);
                }
            }
        }
        
        return config;
      },
      (error) => {
        logger.error('API Request Error', { error });
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.apiInstance.interceptors.response.use(
      (response) => {
        logger.debug('API Response', { 
          url: response.config.url, 
          status: response.status,
          data: response.data,
        });
        
        return response;
      },
      (error: AxiosError) => {
        const url = error.config?.url || 'unknown';
        const method = error.config?.method || 'unknown';
        
        // Create a proper error object
        let appError: AppError;
        
        if (error.response) {
          // Server responded with an error
          const status = error.response.status;
          const message = this.extractErrorMessage(error);
          
          logger.error(`API Error (${status})`, { 
            url, 
            method, 
            status, 
            data: error.response.data,
            message,
          });
          
          appError = {
            message,
            code: `API-${status}`,
            source: ErrorSource.API,
            severity: this.getSeverityFromStatus(status),
            timestamp: new Date(),
            metadata: {
              status,
              url,
              method,
              response: error.response.data,
            },
          } as ApiError;
          
        } else if (error.request) {
          // Request was made but no response
          logger.error('API Network Error', { 
            url, 
            method, 
            error: error.message,
          });
          
          appError = {
            message: 'Network error. Please check your connection and try again.',
            code: 'NETWORK-ERROR',
            source: ErrorSource.NETWORK,
            severity: ErrorSeverity.ERROR,
            timestamp: new Date(),
            metadata: {
              url,
              method,
              originalError: error.message,
            },
          } as NetworkError;
          
        } else {
          // Something else went wrong
          logger.error('API Client Error', { 
            url, 
            method, 
            error: error.message,
          });
          
          appError = {
            message: error.message || 'An unknown error occurred',
            code: 'CLIENT-ERROR',
            source: ErrorSource.UNKNOWN,
            severity: ErrorSeverity.ERROR,
            timestamp: new Date(),
            metadata: {
              url,
              method,
            },
          };
        }
        
        return Promise.reject(appError);
      }
    );
  }

  /**
   * Make a request to the API with consistent error handling
   */
  async request<T>(config: AxiosRequestConfig): Promise<T> {
    try {
      // ENFORCED RULE: Always use localhost:5000
      // If someone passed a baseURL, ignore it and warn
      if (config.baseURL && config.baseURL !== API_BASE_URL) {
        logger.warn(`Ignoring custom baseURL '${config.baseURL}' and using ${API_BASE_URL} instead.`);
      }
      
      // Always set baseURL to localhost:5000
      config.baseURL = API_BASE_URL;
      
      // Ensure URL is relative and doesn't include a full URL
      if (config.url && config.url.startsWith('http')) {
        try {
          // Extract only the path from the full URL
          const urlObj = new URL(config.url);
          config.url = urlObj.pathname + urlObj.search;
          logger.warn(`Converting absolute URL to relative path: ${config.url}`);
        } catch (e) {
          // If URL parsing fails, attempt to strip the domain
          config.url = config.url.replace(/^https?:\/\/[^/]+/i, '');
          logger.warn(`Stripping domain from URL: ${config.url}`);
        }
      }
      
      // Special handling for map-points and other problematic endpoints
      if (config.url && (
          config.url.includes('/api/bms/map-points') || 
          config.url.includes('/bms/map-points')
        )) {
        // Make absolutely sure this is a relative URL that will go through the proxy
        config.url = config.url.replace(/^https?:\/\/[^/]+\/api\//, '/api/');
        config.url = config.url.replace(/^https?:\/\/[^/]+\/bms\//, '/api/bms/');
        if (!config.url.startsWith('/')) {
          if (config.url.startsWith('api/')) {
            config.url = '/' + config.url;
          } else if (config.url.startsWith('bms/')) {
            config.url = '/api/' + config.url;
          }
        }
        logger.info(`Special handling for map-points URL: ${config.url}`);
      }

      // Ensure URL starts with a slash if it's a relative path
      if (config.url && !config.url.startsWith('/')) {
        config.url = `/${config.url}`;
      }

      // If we have an apiGateway and the request has data, add it to the data
      if (this.apiGateway && config.data && typeof config.data === 'object') {
        config.data = {
          ...config.data,
          apiGateway: this.apiGateway
        };
      }

      // If we have an orgId or assetId and the request has data, add them to the data
      if (config.data && typeof config.data === 'object') {
        if (this.orgId) {
          config.data = {
            ...config.data,
            orgId: this.orgId
          };
        }
        
        if (this.assetId) {
          config.data = {
            ...config.data,
            assetId: this.assetId
          };
        }
      }

      // Execute request
      const response = await this.apiInstance.request<T>(config);

      return response.data;
    } catch (error) {
      // Error is already handled by the interceptor
      throw error;
    }
  }

  /**
   * Make a GET request
   */
  async get<T>(url: string, params?: Record<string, any>, config: Omit<AxiosRequestConfig, 'url' | 'method' | 'params'> = {}): Promise<T> {
    return this.request<T>({
      url,
      method: 'GET',
      params,
      ...config,
    });
  }

  /**
   * Make a POST request
   */
  async post<T>(url: string, data?: any, config: Omit<AxiosRequestConfig, 'url' | 'method' | 'data'> = {}): Promise<T> {
    return this.request<T>({
      url,
      method: 'POST',
      data,
      ...config,
    });
  }

  /**
   * Make a PUT request
   */
  async put<T>(url: string, data?: any, config: Omit<AxiosRequestConfig, 'url' | 'method' | 'data'> = {}): Promise<T> {
    return this.request<T>({
      url,
      method: 'PUT',
      data,
      ...config,
    });
  }

  /**
   * Make a DELETE request
   */
  async delete<T>(url: string, config: Omit<AxiosRequestConfig, 'url' | 'method'> = {}): Promise<T> {
    return this.request<T>({
      url,
      method: 'DELETE',
      ...config,
    });
  }

  /**
   * Make a PATCH request
   */
  async patch<T>(url: string, data?: any, config: Omit<AxiosRequestConfig, 'url' | 'method' | 'data'> = {}): Promise<T> {
    return this.request<T>({
      url,
      method: 'PATCH',
      data,
      ...config,
    });
  }

  /**
   * Extract readable error message from API response
   */
  private extractErrorMessage(error: AxiosError): string {
    if (!error.response?.data) {
      return error.message || 'An unknown error occurred';
    }

    const data = error.response.data;

    if (typeof data === 'string') {
      return data;
    }

    if (typeof data === 'object' && data !== null) {
      // Try common fields where error messages might be stored
      const obj = data as Record<string, unknown>;
      const fields = ['message', 'error', 'errorMessage', 'description', 'msg'];
      
      for (const field of fields) {
        if (typeof obj[field] === 'string' && obj[field]) {
          return obj[field] as string;
        }
      }
    }

    return `Error ${error.response.status}: ${error.message}`;
  }

  /**
   * Determine error severity based on HTTP status code
   */
  private getSeverityFromStatus(status: number): ErrorSeverity {
    if (status >= 500) {
      return ErrorSeverity.ERROR;
    } else if (status >= 400) {
      return ErrorSeverity.WARNING;
    }
    return ErrorSeverity.INFO;
  }

  /**
   * Type guard for API responses
   */
  public isApiResponse(data: unknown): data is ApiResponse {
    return (
      typeof data === 'object' &&
      data !== null &&
      'success' in data &&
      typeof (data as ApiResponse).success === 'boolean'
    );
  }

  /**
   * Create a new instance with custom configuration
   */
  withConfig(config: APIClientConfig): APIClient {
    return new APIClient({
      // baseURL is no longer configurable - we always use localhost:5000
      apiGateway: config.apiGateway || this.apiGateway,
      orgId: config.orgId || this.orgId,
      assetId: config.assetId || this.assetId,
      accessKey: config.accessKey,
      secretKey: config.secretKey,
      timeout: config.timeout || this.timeout,
      headers: config.headers,
    });
  }
}

// Default instance that uses localhost
export const defaultClient = new APIClient();

// Convenience methods for default client
export const api = {
  get: <T>(url: string, params?: Record<string, any>, config?: Omit<AxiosRequestConfig, 'url' | 'method' | 'params'>) => 
    defaultClient.get<T>(url, params, config),
    
  post: <T>(url: string, data?: any, config?: Omit<AxiosRequestConfig, 'url' | 'method' | 'data'>) => 
    defaultClient.post<T>(url, data, config),
    
  put: <T>(url: string, data?: any, config?: Omit<AxiosRequestConfig, 'url' | 'method' | 'data'>) => 
    defaultClient.put<T>(url, data, config),
    
  delete: <T>(url: string, config?: Omit<AxiosRequestConfig, 'url' | 'method'>) => 
    defaultClient.delete<T>(url, config),
    
  patch: <T>(url: string, data?: any, config?: Omit<AxiosRequestConfig, 'url' | 'method' | 'data'>) => 
    defaultClient.patch<T>(url, data, config),
    
  // Direct request method for advanced usage
  request: <T>(config: AxiosRequestConfig) => defaultClient.request<T>(config)
};

// Helper for creating a client that uses a remote API gateway (as a param, not baseURL)
export function createApiClient(config?: APIClientConfig): APIClient {
  return new APIClient(config);
}