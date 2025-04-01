/**
 * Export all API services from this file
 */

// Import the core api client for default export
import { api } from './core/apiClient';

// Export unified API client
export * from './core/apiClient';

// Export legacy API clients (for backward compatibility)
export * from './apiClient';

// Export BMS client
export * from './bmsClient';

// Export BMS service (marked as deprecated)
export * from './bmsService';

// Default export the core api client
export default api;