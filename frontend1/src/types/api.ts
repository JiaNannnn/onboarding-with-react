/**
 * Type definitions for API-related types.
 */

// BMS Point interface
export interface BMSPoint {
  id?: string;
  pointName: string;
  pointType: string;
  name?: string;
  unit?: string;
  description?: string;
  deviceId?: string;
  valueType?: string;
  minValue?: number;
  maxValue?: number;
  rawData?: Record<string, any>;
}

// Point Group interface
export interface PointGroup {
  name: string;
  description?: string;
  points: BMSPoint[];
  subgroups?: Record<string, PointGroup>;
}

// API Responses
export interface ApiResponse {
  success: boolean;
  error?: string;
  [key: string]: any;
}

export interface GroupPointsResponse extends ApiResponse {
  grouped_points: Record<string, PointGroup>;
  stats?: {
    total_points: number;
    equipment_types: number;
    equipment_instances: number;
    processing_time?: number;
  };
}

export interface AIGroupPointsRequest {
  points: BMSPoint[];
  strategy?: string;
  model?: string;
  format?: string;
  groupBy?: string;
}

export interface AIGroupPointsResponse extends ApiResponse {
  grouped_points: Record<string, PointGroup>;
  stats: {
    total_points: number;
    equipment_types: number;
    equipment_instances: number;
    processing_time?: number;
  };
  method?: string;
}