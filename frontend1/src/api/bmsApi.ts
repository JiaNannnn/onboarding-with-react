/**
 * BMS API client for making requests to the BMS endpoints.
 */

import { request } from './apiClient';
import {
  BMSPoint,
  PointsResponse,
  GroupsResponse,
  AIGroupsResponse,
  TaggedPointsResponse,
  SaveMappingResponse,
  LoadMappingResponse,
  FilesListResponse,
} from '../types';

/**
 * Fetch points from the BMS system
 */
export const fetchPoints = async (
  assetId: string,
  deviceInstance: string,
  deviceAddress: string = 'unknown-ip'
): Promise<PointsResponse> => {
  return request<PointsResponse>({
    method: 'POST',
    url: '/api/v1/bms/fetch-points',
    data: {
      assetId,
      deviceInstance,
      deviceAddress,
    },
  });
};

/**
 * Group points by a property
 */
export const groupPoints = async (
  points: BMSPoint[],
  groupProperty?: string
): Promise<GroupsResponse> => {
  return request<GroupsResponse>({
    method: 'POST',
    url: '/api/v1/bms/group-points',
    data: {
      points,
      groupProperty,
    },
  });
};

/**
 * Group points using AI
 */
export const aiGroupPoints = async (points: BMSPoint[]): Promise<AIGroupsResponse> => {
  return request<AIGroupsResponse>({
    method: 'POST',
    url: '/api/v1/bms/ai-group-points',
    data: {
      points,
    },
  });
};

/**
 * Generate tags for points using AI
 */
export const aiGenerateTags = async (points: BMSPoint[]): Promise<TaggedPointsResponse> => {
  return request<TaggedPointsResponse>({
    method: 'POST',
    url: '/api/v1/bms/ai-generate-tags',
    data: {
      points,
    },
  });
};

/**
 * Save mapping to a file
 */
export const saveMapping = async (
  mapping: any[],
  filename: string = ''
): Promise<SaveMappingResponse> => {
  return request<SaveMappingResponse>({
    method: 'POST',
    url: '/api/v1/bms/save-mapping',
    data: {
      mapping,
      filename,
    },
  });
};

/**
 * Load mapping from a file
 */
export const loadMapping = async (filepath: string): Promise<LoadMappingResponse> => {
  return request<LoadMappingResponse>({
    method: 'POST',
    url: '/api/v1/bms/load-mapping',
    data: {
      filepath,
    },
  });
};

/**
 * List saved mapping files
 */
export const listSavedFiles = async (): Promise<FilesListResponse> => {
  return request<FilesListResponse>({
    method: 'GET',
    url: '/api/v1/bms/list-saved-files',
  });
};
