/**
 * @deprecated Use bmsClient.ts instead
 * Legacy BMS service functions for backward compatibility
 */

import { api } from './apiClient';
import { HttpMethod } from '../types/apiTypes';

/**
 * @deprecated Use BMS client instead
 */
export const getBmsPoints = async () => {
  return api.get('/api/bms/points');
};

/**
 * @deprecated Use BMS client instead
 */
export const mapPoints = async (points: string[]) => {
  return api.post('/api/bms/map-points', { points });
};

/**
 * @deprecated Use BMS client instead
 */
export const getPointMappingStatus = async (taskId: string) => {
  return api.get(`/api/bms/map-points/${taskId}`);
};

/**
 * @deprecated Use BMS client instead
 */
export const exportMapping = async (mappingData: any, format: 'json' | 'csv' = 'json') => {
  return api.post('/api/bms/export-mapping', { 
    ...mappingData,
    exportFormat: format
  });
}; 