# Technical Guide for Developers

## Frontend System Design Document / 前端系统设计文档

### 1. Technology Stack Overview / 技术栈概述

#### Core Technologies / 核心技术
- **React 18.2.0**: Modern UI library with concurrent rendering features
- **TypeScript 4.9.5**: Static typing for enhanced development experience
- **React Router 6.30.0**: Client-side routing solution
- **Axios**: HTTP client for API communication
- **Handsontable**: Advanced data grid component
- **Zod**: Runtime type checking and validation

#### Development Tools / 开发工具
- **ESLint**: Code linting with TypeScript support
- **Prettier**: Code formatting
- **Jest & Testing Library**: Unit and integration testing
- **React Scripts**: Build and development tooling

### 2. Project Architecture / 项目架构

#### Directory Structure / 目录结构
```
src/
├── api/          # API integration and service interfaces
├── components/   # Reusable UI components
├── contexts/     # React Context providers
├── hooks/        # Custom React hooks
├── pages/        # Route-level components
├── router/       # Routing configuration
├── services/     # Business logic and data processing
├── types/        # TypeScript type definitions
└── utils/        # Utility functions and helpers
```

#### Key Components / 核心组件
- **API Layer**: Centralized API communication
- **Component Library**: Reusable UI building blocks
- **Context System**: Global state management
- **Custom Hooks**: Shared component logic
- **Routing System**: Application navigation
- **Type System**: TypeScript interfaces and types

### 3. Data Flow / 数据流

#### State Management / 状态管理
- React Context for global state
- Component-level state using hooks
- Props for component communication

#### API Integration / API 集成
- Centralized API client configuration
- Type-safe API responses
- Error handling middleware

### 4. Key Features / 核心功能

#### Data Grid Integration / 数据表格集成
- Handsontable implementation
- Custom cell renderers
- Data validation and formatting

#### Type Safety / 类型安全
- TypeScript for static typing
- Zod for runtime validation
- Type-safe API responses

### 5. Development Workflow / 开发工作流

#### Scripts / 脚本命令
- `npm start`: Development server
- `npm run build`: Production build
- `npm run typecheck`: Type checking
- `npm run lint`: Code linting
- `npm run format`: Code formatting

#### Code Quality / 代码质量
- ESLint configuration
- Prettier formatting rules
- TypeScript strict mode
- Unit testing requirements

### 6. Performance Considerations / 性能考虑

#### Optimization Strategies / 优化策略
- Code splitting
- Lazy loading
- Memoization
- Virtual scrolling for large datasets

#### Build Optimization / 构建优化
- Tree shaking
- Bundle size optimization
- Asset optimization

### 7. Security / 安全性

#### Security Measures / 安全措施
- Input validation
- XSS prevention
- CSRF protection
- Secure HTTP headers

### 8. Testing Strategy / 测试策略

#### Testing Levels / 测试层级
- Unit tests
- Integration tests
- Component tests
- End-to-end tests

### 9. Deployment / 部署

#### Build Process / 构建流程
- Environment configuration
- Build optimization
- Asset management

#### Environment Variables / 环境变量
- `.env` configuration
- Environment-specific settings
- Sensitive data handling

### 10. Future Considerations / 未来展望

#### Scalability / 可扩展性
- Component modularity
- Performance monitoring
- Code maintainability

#### Planned Improvements / 计划改进
- State management evolution
- Component library expansion
- Testing coverage improvement

---

## Maintenance Guidelines / 维护指南

### Code Style / 代码风格
- Follow TypeScript best practices
- Use functional components
- Implement proper error handling
- Document complex logic

### Documentation / 文档
- Keep README.md updated
- Document new features
- Maintain API documentation
- Update this technical guide

### Version Control / 版本控制
- Follow Git workflow
- Write meaningful commit messages
- Review pull requests
- Maintain change log

## Introduction

This technical guide provides detailed information and best practices for developers working on the BMS to EnOS Onboarding Tool frontend. The guide covers type safety rules, coding standards, and key implementation patterns.

## Development Environment Setup

### Prerequisites

- Node.js (v16+)
- npm (v8+) or yarn (v1.22+)
- VSCode with the following extensions:
  - ESLint
  - Prettier
  - TypeScript Error Translator
  - React Developer Tools

### Getting Started

1. Clone the repository
2. Install dependencies: `npm install` or `yarn install`
3. Start the development server: `npm start` or `yarn start`
4. Run tests: `npm test` or `yarn test`

## API Endpoints Reference

The frontend application communicates with the backend through the following API endpoints. These endpoints are defined in the backend code and should be accessed through the type-safe API client.

### Base API URL

The base URL for API requests is configured through the `REACT_APP_API_BASE_URL` environment variable. If not set, it defaults to `/api`.

### BMS API Endpoints

#### Fetch Points

```
POST /api/bms/fetch-points
```

Fetches points from the BMS system.

**Request:**
```typescript
interface FetchPointsRequest {
  assetId: string;
  deviceInstance: string;
  deviceAddress?: string; // optional
}
```

**Response:**
```typescript
interface FetchPointsResponse {
  success: boolean;
  data?: Array<{
    id: string;
    name: string;
    type: string;
    description?: string;
    device_id?: string;
    value_type?: string;
    unit?: string;
    // other properties
  }>;
  error?: string;
}
```

**Example Usage:**
```typescript
const response = await request<FetchPointsResponse>({
  url: '/bms/fetch-points',
  method: 'POST',
  data: {
    assetId: 'asset123',
    deviceInstance: 'device456',
    deviceAddress: '192.168.1.1'
  }
});
```

#### AI Group Points

```
POST /api/bms/ai-group-points
```

Groups BMS points using AI-based algorithms.

**Request:**
```typescript
interface GroupPointsRequest {
  points: Array<{
    id: string;
    name: string;
    type: string;
    description?: string;
    device_id?: string;
    value_type?: string;
    unit?: string;
    min_value?: number;
    max_value?: number;
    raw_data?: Record<string, unknown>;
  }>;
  strategy?: 'default' | 'ai' | 'ontology'; // default is 'ai'
  model?: string; // optional OpenAI model name
}
```

**Response:**
```typescript
interface GroupPointsResponse {
  success: boolean;
  grouped_points?: Record<string, {
    name: string;
    description: string;
    points: Array<{
      id: string;
      name: string;
      type: string;
      // other point properties
    }>;
    subgroups: Record<string, unknown>;
  }>;
  stats?: {
    total_points: number;
    equipment_types: number;
    equipment_instances: number;
  };
  error?: string;
}
```

**Example Usage:**
```typescript
const response = await request<GroupPointsResponse>({
  url: '/bms/ai-group-points',
  method: 'POST',
  data: {
    points: pointsArray,
    strategy: 'ai',
    model: 'gpt-4o'
  }
});
```

#### Group Points (Alternative Endpoint)

```
POST /api/bms/group-points
```

Alternative endpoint for grouping points with different strategies.

**Request:**
```typescript
interface AlternativeGroupPointsRequest {
  points: Array<{
    pointName: string; // or objectName
    pointType?: string; // optional for hierarchical_simple
    // other point properties
  }>;
  groupingStrategy?: 'default' | 'equipment_instance' | 'hierarchical' | 'hierarchical_simple';
}
```

**Response:**
Similar to the AI Group Points response.

#### Save Mapping

```
POST /api/bms/save-mapping
```

Saves a BMS to EnOS mapping configuration to a CSV file.

**Request:**
```typescript
interface SaveMappingRequest {
  mapping: Array<{
    enosEntity: string;
    enosPoint: string;
    rawPoint: string;
    rawUnit: string;
    rawFactor: number;
  }>;
  filename?: string; // optional
}
```

**Response:**
```typescript
interface SaveMappingResponse {
  success: boolean;
  filepath?: string;
  error?: string;
}
```

**Example Usage:**
```typescript
const response = await request<SaveMappingResponse>({
  url: '/bms/save-mapping',
  method: 'POST',
  data: {
    mapping: mappingArray,
    filename: 'my_mapping'
  }
});
```

#### List Saved Files

```
GET /api/bms/list-saved-files
```

Lists all saved CSV mapping files.

**Response:**
```typescript
interface ListSavedFilesResponse {
  success: boolean;
  files?: Array<{
    filename: string;
    filepath: string;
    size: number;
    modified: string; // formatted date
  }>;
  error?: string;
}
```

**Example Usage:**
```typescript
const response = await request<ListSavedFilesResponse>({
  url: '/bms/list-saved-files',
  method: 'GET'
});
```

#### Load CSV

```
POST /api/bms/load-csv
```

Loads a CSV file from the results directory.

**Request:**
```typescript
interface LoadCsvRequest {
  filepath: string;
}
```

**Response:**
```typescript
interface LoadCsvResponse {
  success: boolean;
  data?: Array<Record<string, unknown>>;
  error?: string;
}
```

**Example Usage:**
```typescript
const response = await request<LoadCsvResponse>({
  url: '/bms/load-csv',
  method: 'POST',
  data: {
    filepath: '/path/to/file.csv'
  }
});
```

#### Download File

```
GET /api/bms/download-file?filepath={filepath}
```

Downloads a file from the results directory.

**Query Parameters:**
- `filepath`: The path to the file to download

**Response:**
The file as a downloadable attachment.

**Example Usage:**
```typescript
// Direct browser download
window.location.href = `${process.env.REACT_APP_API_BASE_URL}/bms/download-file?filepath=${encodeURIComponent(filePath)}`;
```

#### Generate Tags

```
POST /api/bms/generate-tags
```

Generates tags for BMS points using AI.

**Request:**
```typescript
interface GenerateTagsRequest {
  points: Array<{
    pointName: string;
    pointType: string;
    // other point properties
  }>;
}
```

**Response:**
```typescript
interface GenerateTagsResponse {
  success: boolean;
  taggedPoints?: Array<{
    pointName: string;
    pointType: string;
    tags: string[];
    // other point properties
  }>;
  error?: string;
}
```

**Example Usage:**
```typescript
const response = await request<GenerateTagsResponse>({
  url: '/bms/generate-tags',
  method: 'POST',
  data: {
    points: pointsArray
  }
});
```

### Onboarding API Endpoints

#### Onboard BMS Points

```
POST /api/bms/onboard
```

Processes BMS points through the onboarding pipeline.

**Request:**
```typescript
interface OnboardPointsRequest {
  points: Array<{
    id: string;
    name: string;
    type: string;
    description?: string;
    device_id?: string;
    value_type?: string;
    unit?: string;
    min_value?: number;
    max_value?: number;
  }>;
  batch_size?: number; // default: 200
  ontology_version?: string;
  memory_limit_pct?: number; // default: 75
}
```

**Response:**
```typescript
interface OnboardPointsResponse {
  status: 'success' | 'error';
  summary?: {
    total_points: number;
    mapped_points: number;
    equipment_types: string[];
    instances: Record<string, string[]>;
  };
  result?: Record<string, Record<string, unknown>>;
  message?: string; // error message if status is 'error'
}
```

**Example Usage:**
```typescript
const response = await request<OnboardPointsResponse>({
  url: '/bms/onboard',
  method: 'POST',
  data: {
    points: pointsArray,
    batch_size: 100
  }
});
```

#### Export Mapping

```
POST /api/bms/export-mapping
```

Generates an exportable mapping configuration.

**Request:**
```typescript
interface ExportMappingRequest {
  result: Record<string, Record<string, unknown>>;
}
```

**Response:**
```typescript
interface ExportMappingResponse {
  status: 'success' | 'error';
  mapping_config?: Record<string, unknown>;
  message?: string; // error message if status is 'error'
}
```

**Example Usage:**
```typescript
const response = await request<ExportMappingResponse>({
  url: '/bms/export-mapping',
  method: 'POST',
  data: {
    result: onboardingResult
  }
});
```

### Utility Endpoints

#### Health Check

```
GET /api/bms/health
```

Checks if the API is running.

**Response:**
```typescript
interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
}
```

**Example Usage:**
```typescript
const response = await request<HealthResponse>({
  url: '/bms/health',
  method: 'GET'
});
```

#### List OpenAI Responses

```
GET /api/list-openai-responses
```

Lists all saved OpenAI response files.

**Response:**
```typescript
interface ListOpenAIResponsesResponse {
  success: boolean;
  files?: Array<{
    filename: string;
    path: string;
    size: number;
    created: number;
    modified: number;
  }>;
  count?: number;
  error?: string;
}
```

**Example Usage:**
```typescript
const response = await request<ListOpenAIResponsesResponse>({
  url: '/list-openai-responses',
  method: 'GET'
});
```

#### Get OpenAI Response

```
GET /api/openai-responses/{filename}
```

Gets a specific OpenAI response file.

**Path Parameters:**
- `filename`: The name of the OpenAI response file

**Response:**
The JSON file.

**Example Usage:**
```typescript
const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}/openai-responses/${filename}`);
const data = await response.json();
```

### Type Definitions

All these endpoint requests and responses should be properly typed in your codebase to ensure type safety. Define these types in the `types/apiTypes.ts` file:

```typescript
// Example of type definitions for API endpoints
export namespace BmsApi {
  export interface FetchPointsRequest {
    assetId: string;
    deviceInstance: string;
    deviceAddress?: string;
  }
  
  export interface FetchPointsResponse {
    success: boolean;
    data?: Point[];
    error?: string;
  }
  
  // Define other request and response types...
}
```

## Type Safety Guidelines

### Core Type Safety Principles

1. **No `any` Types**: Never use the `any` type in the codebase
2. **Use `unknown` for Unknown Data**: When the type is not known, use `unknown` with type guards
3. **Explicit Function Return Types**: Always specify return types for functions
4. **Strict Null Checking**: Always check for null/undefined before using values

### Map Points API Endpoints

#### Map Points to EnOS

```
POST /api/bms/map-points
```

Maps BMS points to EnOS schema paths.

**Request:**
```typescript
interface MapPointsRequest {
  points: Array<{
    id: string;
    pointName: string;
    pointType: string;
    unit?: string;
    description?: string;
    deviceType?: string;  // Optional - will be inferred from pointName if not provided
    deviceId?: string;    // Optional
  }>;
  mappingConfig: {
    targetSchema: string;
    matchingStrategy: 'strict' | 'fuzzy' | 'ai';
    batchMode?: boolean;  // Optional - enables batch processing mode
    batchSize?: number;   // Optional - number of points per batch (default: 50)
    deviceTypes?: string[]; // Optional - device types to prioritize processing
  };
}
```

**Response:**
```typescript
interface MapPointsResponse {
  success: boolean;
  taskId?: string;  // For async processing in batch mode
  status?: 'processing' | 'completed' | 'error';
  progress?: number; // Percentage complete for batch operations
  mappings?: Array<{
    mapping: {
      pointId: string;
      enosPoint: string;
      status: 'mapped' | 'error';
      error?: string;
    },
    original: {
      pointName: string;
      pointType: string;
      deviceType: string;
      deviceId: string;
      unit: string;
      value: string;
    }
  }>;
  stats?: {
    total: number;
    mapped: number;
    errors: number;
  };
  error?: string;
}
```

**Batch Processing Status Check:**
```
GET /api/v1/map-points/{task_id}?includePartial=true
```

Check status of an ongoing batch mapping operation. The `includePartial` parameter (optional) returns partial results for completed batches.

**Example Usage:**
```typescript
// Start mapping process
const startResponse = await request<MapPointsResponse>({
  url: '/bms/map-points',
  method: 'POST',
  data: {
    points: selectedPoints,
    mappingConfig: {
      targetSchema: 'enos',
      matchingStrategy: 'ai',
      batchMode: true,
      batchSize: 20,
      deviceTypes: ['AHU', 'FCU', 'CH']
    }
  }
});

// If batch mode, check status with taskId
if (startResponse.taskId) {
  const statusResponse = await request<MapPointsResponse>({
    url: `/bms/map-points/${startResponse.taskId}`,
    method: 'GET',
    params: {
      includePartial: true  // Include partial results from completed batches
    }
  });
  
  // Display progress to user
  console.log(`Mapping progress: ${statusResponse.progress}%`);
}
```

**Important Notes:**
- The API now supports batch processing mode for large point sets
- When deviceType is not provided, the system attempts to infer it from the point name
- Example: "CT_1.TripStatus" -> Device Type: "CT"
- Progress tracking and partial results are available for batch operations

## Project-Specific Implementation / 项目具体实现

### 1. BMS to EnOS Mapping Core Features / BMS到EnOS映射核心功能

#### Point Mapping Implementation / 点位映射实现
- **File Upload Support**: 
  - CSV and JSON format support
  - Automatic format detection and parsing
  - Robust error handling for malformed data
  - Batch processing capabilities

- **Mapping Interface**: 
  - Interactive data grid using Handsontable
  - Real-time validation and feedback
  - Custom cell renderers for different data types
  - Pagination for large datasets
  - Column sorting and filtering

- **AI-Assisted Mapping**:
  - Integration with OpenAI for intelligent point mapping
  - Multiple mapping strategies (strict/fuzzy/AI)
  - Confidence score display
  - Manual override capabilities

#### Data Processing Features / 数据处理功能
- **CSV Processing**:
  ```typescript
  const parseCSV = (csvText: string): BMSPoint[] => {
    // Handles quoted values and special characters
    // Supports flexible column mapping
    // Automatic type inference
    // Validation of required fields
  };
  ```

- **Batch Processing**:
  ```typescript
  interface BatchConfig {
    batchSize: number;
    totalBatches: number;
    processedBatches: number;
    status: 'processing' | 'completed' | 'error';
  }
  ```

### 2. Core Components / 核心组件

#### MapPoints Component / 映射点位组件
- **Features**:
  - File upload and parsing
  - Data grid display and editing
  - Mapping execution and status tracking
  - Export functionality
  - Error handling and validation

- **Key Methods**:
  ```typescript
  const handleMapPoints = async () => {
    // Initiates the mapping process
    // Handles API communication
    // Updates UI with progress
    // Manages error states
  };

  const exportMappingsToCSV = async () => {
    // Formats mapped data
    // Generates CSV file
    // Handles download
  };
  ```

#### GroupPoints Component / 点位分组组件
- **Features**:
  - Automatic grouping by device type
  - Manual group creation and editing
  - Drag-and-drop point management
  - Group hierarchy visualization
  - Search and filter capabilities

### 3. State Management / 状态管理

#### Mapping Context / 映射上下文
```typescript
interface MappingContextType {
  mappings: PointMapping[];
  setMappings: (mappings: PointMapping[]) => void;
  filename: string;
  setFilename: (name: string) => void;
  // Additional context methods
}
```

#### Points Context / 点位上下文
```typescript
interface PointsContextType {
  points: BMSPoint[];
  setPoints: (points: BMSPoint[]) => void;
  selectedPoints: string[];
  setSelectedPoints: (ids: string[]) => void;
}
```

### 4. Data Models / 数据模型

#### BMS Point Structure / BMS点位结构
```typescript
interface BMSPoint {
  id: string;
  pointName: string;
  pointType: string;
  unit?: string;
  description?: string;
  deviceType?: string;
  deviceId?: string;
  value?: string | number;
}
```

#### Mapping Result Structure / 映射结果结构
```typescript
interface PointMapping {
  mapping: {
    pointId: string;
    enosPoint: string;
    status: 'mapped' | 'error';
    error?: string;
  };
  original: {
    pointName: string;
    pointType: string;
    deviceType: string;
    deviceId: string;
    unit: string;
    value: string;
  };
}
```

### 5. Project Configuration / 项目配置

#### Environment Variables / 环境变量
```bash
# Required Environment Variables
REACT_APP_API_BASE_URL=http://localhost:5000
REACT_APP_OPENAI_API_KEY=your-api-key
REACT_APP_ENOS_ORG_ID=your-org-id

# Optional Environment Variables
REACT_APP_BATCH_SIZE=50
REACT_APP_ENABLE_MOCK_API=false
REACT_APP_DEBUG_MODE=false
```

#### Build Configuration / 构建配置
```json
{
  "build": {
    "outDir": "build",
    "target": "es2018",
    "sourcemap": true,
    "optimization": {
      "minimize": true,
      "splitChunks": {
        "chunks": "all"
      }
    }
  }
}
```

### 6. Development Guidelines / 开发指南

#### Code Organization / 代码组织
- **Feature-based Structure**:
  ```
  src/
  ├── features/
  │   ├── mapping/
  │   │   ├── components/
  │   │   ├── hooks/
  │   │   └── services/
  │   └── grouping/
  │       ├── components/
  │       ├── hooks/
  │       └── services/
  ```

#### Testing Strategy / 测试策略
- Unit tests for utility functions
- Integration tests for API services
- Component tests for UI elements
- End-to-end tests for critical workflows

#### Performance Optimization / 性能优化
- Implement virtual scrolling for large datasets
- Use React.memo for expensive components
- Implement debounced search
- Cache API responses