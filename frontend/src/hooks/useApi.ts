/**
 * Type-safe API hooks for making requests
 */
import { useState, useCallback, useEffect } from 'react';
import { AxiosRequestConfig } from 'axios';
import { HttpMethod } from '../types/apiTypes';
import { AppError } from '../types/errorTypes';
import { api } from '../api/apiClient';

// Define the expected structure of an API client for the hooks
interface ApiClientInterface {
  get: <T>(url: string, params?: Record<string, any>, config?: any) => Promise<T>;
  post: <T>(url: string, data?: any, config?: any) => Promise<T>;
  put: <T>(url: string, data?: any, config?: any) => Promise<T>;
  delete: <T>(url: string, config?: any) => Promise<T>;
  // Removed patch and request as they are not on the base 'api' object
  // patch?: <T>(url: string, data?: any, config?: any) => Promise<T>;
  // request?: <T>(config: any) => Promise<T>; 
}

/**
 * Hook result interface
 */
export interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: AppError | null;
  execute: (requestData?: unknown) => Promise<T | null>;
  reset: () => void;
}

/**
 * Hook options interface
 */
export interface UseApiOptions extends Partial<AxiosRequestConfig> {
  immediate?: boolean;
  initialData?: unknown;
}

/**
 * Hook for making API requests with state management
 */
export function useApi<TData = unknown>(
  url: string,
  method: HttpMethod = HttpMethod.GET,
  options: UseApiOptions = {}
): UseApiResult<TData> {
  const [data, setData] = useState<TData | null>(options.initialData as TData || null);
  const [error, setError] = useState<AppError | null>(null);
  const [loading, setLoading] = useState<boolean>(options.immediate || false);

  const { immediate, initialData, ...axiosOptions } = options;

  const execute = useCallback(
    async (requestData?: unknown): Promise<TData | null> => {
      setLoading(true);
      setError(null);

      try {
        let response: TData;

        // Create request config
        const config: AxiosRequestConfig = {
          ...axiosOptions,
          url,
          method,
        };

        // Add data if provided
        if (requestData !== undefined) {
          config.data = requestData;
        }

        // Execute the request using our unified api client
        if (method === HttpMethod.GET) {
          response = await api.get<TData>(url, config.params, config);
        } else if (method === HttpMethod.POST) {
          response = await api.post<TData>(url, config.data, config);
        } else if (method === HttpMethod.PUT) {
          response = await api.put<TData>(url, config.data, config);
        } else if (method === HttpMethod.DELETE) {
          response = await api.delete<TData>(url, config);
        } else {
          // Removed patch and request calls
          throw new Error(`Unsupported HTTP method: ${method}`);
        }

        setData(response);
        setLoading(false);
        return response;
      } catch (err) {
        // The API client already converts errors to AppError format
        const appError = err as AppError;
        setError(appError);
        setLoading(false);
        return null;
      }
    },
    [url, method, axiosOptions]
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  // Execute immediately if option is set
  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [immediate, execute]);

  return { data, error, loading, execute, reset };
}

/**
 * Hook for making a GET request
 */
export function useGet<TData = unknown>(
  url: string,
  options: UseApiOptions = {}
): UseApiResult<TData> {
  return useApi<TData>(url, HttpMethod.GET, options);
}

/**
 * Hook for making a POST request
 */
export function usePost<TData = unknown>(
  url: string,
  options: UseApiOptions = {}
): UseApiResult<TData> {
  return useApi<TData>(url, HttpMethod.POST, options);
}

/**
 * Hook for making a PUT request
 */
export function usePut<TData = unknown>(
  url: string,
  options: UseApiOptions = {}
): UseApiResult<TData> {
  return useApi<TData>(url, HttpMethod.PUT, options);
}

/**
 * Hook for making a DELETE request
 */
export function useDelete<TData = unknown>(
  url: string,
  options: UseApiOptions = {}
): UseApiResult<TData> {
  return useApi<TData>(url, HttpMethod.DELETE, options);
}

/**
 * Create a API hook factory that uses a custom APIClient instance
 */
export function createApiHooks(client: ApiClientInterface) {
  // Implement a custom api hook with this client
  function useClientApi<TData = unknown>(
    url: string,
    method: HttpMethod = HttpMethod.GET,
    options: UseApiOptions = {}
  ): UseApiResult<TData> {
    const [data, setData] = useState<TData | null>(options.initialData as TData || null);
    const [error, setError] = useState<AppError | null>(null);
    const [loading, setLoading] = useState<boolean>(options.immediate || false);
  
    const { immediate, initialData, ...axiosOptions } = options;
  
    const execute = useCallback(
      async (requestData?: unknown): Promise<TData | null> => {
        setLoading(true);
        setError(null);
  
        try {
          let response: TData;
  
          // Create request config
          const config: AxiosRequestConfig = {
            ...axiosOptions,
            url,
            method,
          };
  
          // Add data if provided
          if (requestData !== undefined) {
            config.data = requestData;
          }
  
          // Execute the request using the provided client
          if (method === HttpMethod.GET) {
            response = await client.get<TData>(url, config.params, config);
          } else if (method === HttpMethod.POST) {
            response = await client.post<TData>(url, config.data, config);
          } else if (method === HttpMethod.PUT) {
            response = await client.put<TData>(url, config.data, config);
          } else if (method === HttpMethod.DELETE) {
            response = await client.delete<TData>(url, config);
          } else {
            // Removed patch and request calls
            throw new Error(`Unsupported HTTP method: ${method}`);
          }
  
          setData(response);
          setLoading(false);
          return response;
        } catch (err) {
          // The API client already converts errors to AppError format
          const appError = err as AppError;
          setError(appError);
          setLoading(false);
          return null;
        }
      },
      [url, method, axiosOptions]
    );
  
    const reset = useCallback(() => {
      setData(null);
      setError(null);
      setLoading(false);
    }, []);
  
    // Execute immediately if option is set
    useEffect(() => {
      if (immediate) {
        execute();
      }
    }, [immediate, execute]);
  
    return { data, error, loading, execute, reset };
  }

  return {
    useApi: useClientApi,
    useGet: <TData = unknown>(url: string, options: UseApiOptions = {}) => 
      useClientApi<TData>(url, HttpMethod.GET, options),
    usePost: <TData = unknown>(url: string, options: UseApiOptions = {}) => 
      useClientApi<TData>(url, HttpMethod.POST, options),
    usePut: <TData = unknown>(url: string, options: UseApiOptions = {}) => 
      useClientApi<TData>(url, HttpMethod.PUT, options),
    useDelete: <TData = unknown>(url: string, options: UseApiOptions = {}) => 
      useClientApi<TData>(url, HttpMethod.DELETE, options),
  };
}

export default useApi;