/**
 * Type definitions for the application.
 */

// Common types used throughout the application

// Basic BMS point type
export interface BMSPoint {
  id: string;
  pointName: string;
  name?: string;
  description?: string;
  pointType: string;
  type?: string;
  unit?: string;
  source?: string;
  [key: string]: any; // For additional properties
}

// Group of points
export interface PointGroup {
  id: string;
  name: string;
  description?: string;
  points: BMSPoint[];
  subgroups?: { [key: string]: PointGroup };
  [key: string]: any;
}

// Mapping between points
export interface PointMapping {
  id: string;
  enosEntity: string;
  enosPoint: string;
  rawPoint: string;
  rawUnit?: string;
  rawFactor?: number;
  [key: string]: any;
}

// Type for hierarchical groups
export interface GroupsMap {
  [key: string]: PointGroup;
}

// Constants for drag and drop
export const ItemTypes = {
  POINT: 'point',
  GROUP: 'group',
};

// API response types
export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
}

// EmptyState component props
export interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
}

// ErrorDisplay component props
export interface ErrorDisplayProps {
  error: string | null;
  onClose?: () => void;
}

// For the LoadingWrapper component
export interface LoadingWrapperProps {
  loading: boolean;
  error?: string | null;
  children: React.ReactNode;
  message?: string;
}

// BMS Point interface
export interface BMSPoint {
  pointName: string;
  pointType: string;
  pointId?: string;
  presentValue?: any;
  objectIdentifier?: string | Record<string, any>;
  deviceInstance?: number;
  objectInstance?: number;
  units?: string;
  description?: string;
  tags?: string[];
}

// BMS Point Group interface
export interface BMSPointGroup {
  name: string;
  description: string;
  points: BMSPoint[];
}

// EnOS Point interface (simplified)
export interface EnOSPoint {
  id: string;
  name: string;
  type: string;
  description?: string;
}

// BMS to EnOS Mapping interface
export interface BMSMapping {
  bmsPoint: BMSPoint;
  enosPoint: EnOSPoint;
  mappingType: string;
  createdAt: string;
  updatedAt: string;
}

// Tagged Point interface (from AI)
export interface TaggedPoint {
  pointName: string;
  tags: string[];
  category: string;
  description: string;
}

export interface PointsResponse extends ApiResponse<BMSPoint[]> {
  points?: BMSPoint[];
}

export interface GroupsResponse extends ApiResponse<Record<string, PointGroup>> {
  groups?: Record<string, PointGroup>;
  grouped_points?: Record<string, PointGroup>;
  stats?: {
    total_points: number;
    equipment_types: number;
    equipment_instances: number;
    processing_time?: number;
  };
}

export interface AIGroupsResponse extends ApiResponse<Record<string, PointGroup>> {
  groups?: Record<string, PointGroup>;
  grouped_points?: Record<string, PointGroup>;
  stats?: {
    total_points: number;
    equipment_types: number;
    equipment_instances: number;
    processing_time?: number;
  };
  method?: string;
}

export interface TaggedPointsResponse extends ApiResponse<TaggedPoint[]> {
  tagged_points: TaggedPoint[];
}

export interface FileResponse extends ApiResponse<string> {
  filepath: string;
  filename?: string;
}

export interface FilesListResponse extends ApiResponse<any> {
  files: Array<{
    filename: string;
    filepath: string;
    size: number;
    modified: string;
    created: string;
  }>;
  directory?: string;
}

export interface SaveMappingResponse extends ApiResponse<string> {
  filepath: string;
}

export interface LoadMappingResponse extends ApiResponse<any> {
  data: any[];
}

// OpenAI related interfaces
export interface OpenAIMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface OpenAIRequest {
  messages: OpenAIMessage[];
  model?: string;
  temperature?: number;
  max_tokens?: number;
  response_format?: { type: string };
}

export interface OpenAIResponse extends ApiResponse<any> {
  result: {
    id: string;
    created: number;
    model: string;
    choices: Array<{
      index: number;
      message: {
        role: string;
        content: string;
      };
      finish_reason: string;
    }>;
    usage: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    };
  };
}
