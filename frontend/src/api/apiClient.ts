/**
 * Type-safe API client implementation using Axios
 * 
 * NOTE: This file now exports the unified API client from core/apiClient.ts
 * for backward compatibility. For new code, import from core/apiClient.ts directly.
 */

// Import and re-export the unified API client
import { 
  APIClient, 
  defaultClient, 
  api,
  createApiClient,
  APIClientConfig 
} from './core/apiClient';

// Re-export for backward compatibility
export { 
  APIClient, 
  defaultClient as localClient, 
  api,
  createApiClient
};

// Re-export types
export type { APIClientConfig };

// Deprecated function for backward compatibility
export async function request<T>(config: any): Promise<any> {
  console.warn('DEPRECATED: Please use api.get/post/etc. or APIClient class instead of request function');
  return defaultClient.request<T>(config);
}

// Export default
export default api;