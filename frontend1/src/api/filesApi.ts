/**
 * Files API client for file operations.
 */

import apiClient, { request } from './apiClient';
import { FileResponse, FilesListResponse } from '../types';

/**
 * Upload a file
 */
export const uploadFile = async (file: File): Promise<FileResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  return request<FileResponse>({
    method: 'POST',
    url: '/api/v1/files/upload',
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    data: formData,
  });
};

/**
 * Download a file - returns a URL to the file
 */
export const getDownloadUrl = (filepath: string): string => {
  return `${apiClient.defaults.baseURL}/api/v1/files/download?filepath=${encodeURIComponent(
    filepath
  )}`;
};

/**
 * List files in a directory
 */
export const listFiles = async (directory?: string): Promise<FilesListResponse> => {
  const params: Record<string, string> = {};
  if (directory) {
    params.directory = directory;
  }

  return request<FilesListResponse>({
    method: 'GET',
    url: '/api/v1/files/list',
    params,
  });
};

/**
 * Delete a file
 */
export const deleteFile = async (filepath: string): Promise<FileResponse> => {
  return request<FileResponse>({
    method: 'DELETE',
    url: '/api/v1/files/delete',
    data: {
      filepath,
    },
  });
};
