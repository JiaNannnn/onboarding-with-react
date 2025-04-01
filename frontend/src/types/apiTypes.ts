/**
 * API-related type definitions
 */

/**
 * HTTP methods supported by the API
 */
export enum HttpMethod {
  GET = 'GET',
  POST = 'POST',
  PUT = 'PUT',
  DELETE = 'DELETE',
  PATCH = 'PATCH',
}

/**
 * Base request options interface
 */
export interface RequestOptions {
  url: string;
  method: HttpMethod;
  data?: unknown;
  params?: Record<string, string | number | boolean | undefined>;
  headers?: Record<string, string>;
  timeout?: number;
  withCredentials?: boolean;
}

/**
 * Base API response interface
 */
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

/**
 * Point structure as returned from the API
 */
export interface BMSPointRaw {
  id?: string;
  pointId?: string;
  pointName: string;
  pointType: string;
  unit?: string;
  description?: string;
  value?: string | number | boolean;
  timestamp?: string;
  status?: string;
}

/**
 * Standard point structure used in the application
 */
export interface BMSPoint {
  id: string;
  pointName: string;
  pointType: string;
  unit: string;
  description: string;
  value?: string | number | boolean;
  timestamp?: string;
  status?: string;
  deviceInstance?: string;
  deviceAddress?: string;
  assetId?: string;
  objectInst?: string;
  objectIdentifier?: string;
  presentValue?: string | number;
  covIncrement?: string | number;
  source?: string;
  otDeviceInst?: string;
  deviceType?: string;
  deviceId?: string;
}

/**
 * Point Group interface
 */
export interface PointGroup {
  id: string;
  name: string;
  description?: string;
  points: BMSPoint[];
  subgroups?: Record<string, PointGroup>;
}

/**
 * Request parameters for fetching points
 */
export interface FetchPointsRequest {
  assetId: string;
  deviceInstance: string | number;
  deviceAddress?: string;
  orgId?: string;
  page?: number;
  pageSize?: number;
  filter?: string;
}

/**
 * Response structure for fetch points API
 */
export interface FetchPointsResponse {
  record?: BMSPointRaw[];
  totalCount?: number;
  hasMore?: boolean;
  status?: string;
  message?: string;
}

/**
 * Group Points Request interface
 */
export interface GroupPointsRequest {
  points: BMSPoint[];
  strategy?: 'default' | 'ai' | 'ontology';
  model?: string;
}

/**
 * Group Points Response interface
 */
export interface GroupPointsResponse extends ApiResponse<Record<string, PointGroup>> {
  grouped_points?: Record<string, PointGroup>;
  stats?: {
    total_points: number;
    equipment_types: number;
    equipment_instances: number;
    processing_time?: number;
  };
}

/**
 * AI Group Points Request interface
 */
export interface AIGroupPointsRequest {
  points: BMSPoint[];
  strategy?: string;
  model?: string;
  format?: string;
  groupBy?: string;
}

/**
 * AI Group Points Response interface
 */
export interface AIGroupPointsResponse extends ApiResponse<Record<string, PointGroup>> {
  grouped_points?: Record<string, PointGroup>;
  stats?: {
    total_points: number;
    equipment_types: number;
    equipment_instances: number;
    processing_time?: number;
  };
  method?: string;
}

/**
 * EnOS Point interface
 */
export interface EnOSPoint {
  id: string;
  name: string;
  type: string;
  description?: string;
}

/**
 * Mapping interface
 */
export interface PointMapping {
  enosEntity: string;          // HVAC equipment type (AHU, VAV, etc.)
  enosPoint: string;           // Point category (temperature, humidity, etc.)
  rawPoint: string;            // Original BMS point name
  pointName?: string;          // Extracted point name (without device prefix)
  rawUnit?: string;            // Original unit of measurement
  rawFactor?: number;          // Conversion factor if needed
  enosPath?: string;           // Full EnOS model path
  deviceId?: string;           // Device identifier
  confidence?: number;         // AI confidence score for the mapping
  pointCategory?: string;      // EnOS point category
  status?: string;             // Mapping status
}

/**
 * Save Mapping Request interface
 */
export interface SaveMappingRequest {
  mapping: PointMapping[];
  filename?: string;
}

/**
 * Save Mapping Response interface
 */
export interface SaveMappingResponse extends ApiResponse<string> {
  filepath?: string;
}

/**
 * List Files Response interface
 */
export interface ListFilesResponse extends ApiResponse<Array<{
  filename: string;
  filepath: string;
  size: number;
  modified: string;
}>> {
  files?: Array<{
    filename: string;
    filepath: string;
    size: number;
    modified: string;
  }>;
  directory?: string;
}

/**
 * Load CSV Request interface
 */
export interface LoadCSVRequest {
  filepath: string;
}

/**
 * Load CSV Response interface
 */
export interface LoadCSVResponse extends ApiResponse<unknown[]> {
  data?: unknown[];
} 