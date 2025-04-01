# Technical Guide for Developers

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
  }>;
  config: {
    targetSchema: string;
    matchingStrategy: 'strict' | 'fuzzy' | 'ai';
    confidence: number;
    transformationRules: Record<string, string>;
  };
}
```

**Response:**
```typescript
interface MapPointsResponse {
  success: boolean;
  mappings?: Array<{
    pointId: string;
    status: 'mapped' | 'error';
    enosPath?: string;
    confidence?: number;
    error?: string;
  }>;
  error?: string;
}
```

**Example Usage:**
```typescript
const response = await request<MapPointsResponse>({
  url: '/bms/map-points',
  method: 'POST',
  data: {
    points: selectedPoints,
    config: mappingConfig
  }
});
```

## Component Documentation

### MapPoints Component

The MapPoints component provides a comprehensive interface for mapping BMS points to EnOS schema paths. It supports multiple mapping strategies, validation rules, and preview functionality.

#### Features

- Point selection and filtering
- Multiple mapping strategies (strict, fuzzy, AI-assisted)
- Configurable confidence thresholds
- Custom transformation rules
- Validation rules with visual feedback
- Preview functionality before mapping
- Mapping statistics visualization

#### Component Structure

```typescript
interface MappedPoint extends BMSPoint {
  enosPath?: string;
  mappingStatus?: 'mapped' | 'unmapped' | 'error';
  mappingError?: string;
  confidence?: number;
  validationErrors?: string[];
}

interface MappingConfig {
  targetSchema: string;
  matchingStrategy: 'strict' | 'fuzzy' | 'ai';
  confidence: number;
  transformationRules: Record<string, string>;
}

interface ValidationRule {
  id: string;
  name: string;
  description: string;
  validate: (point: MappedPoint) => boolean;
  errorMessage: string;
}
```

#### Usage Example

```typescript
import { MapPoints } from '../pages/MapPoints';

function App() {
  return (
    <Router>
      <Route path="/map-points" component={MapPoints} />
    </Router>
  );
}
```

#### Configuration Options

1. Target Schemas:
   - Default EnOS Schema
   - HVAC Systems
   - Lighting Systems
   - Energy Management
   - Custom Schema

2. Matching Strategies:
   - Strict Matching: Exact matches only
   - Fuzzy Matching: Approximate string matching
   - AI-Assisted Matching: Uses AI to determine best matches

3. Validation Rules:
   - No Special Characters: EnOS paths should not contain special characters
   - Minimum Path Segments: EnOS paths should have at least 3 segments
   - Maximum Path Segments: EnOS paths should have no more than 5 segments

#### Styling

The component uses a modular CSS approach with BEM naming convention. Key style classes:

```css
.map-points__content      // Main container
.map-points__toolbar     // Top actions bar
.map-points__table      // Points table
.map-points__config     // Configuration panel
.map-points__preview    // Preview panel
.map-points__stats     // Statistics panel
```

Custom styling can be applied by overriding these classes in your CSS files.

#### Best Practices

1. Error Handling:
   - Always validate points before mapping
   - Display clear error messages
   - Provide validation feedback inline

2. Performance:
   - Use pagination for large datasets
   - Implement debounced search
   - Cache mapping results when possible

3. User Experience:
   - Show loading states during mapping
   - Provide clear feedback on mapping status
   - Allow easy navigation of validation errors

4. Accessibility:
   - Include ARIA labels
   - Ensure keyboard navigation
   - Provide high contrast visual indicators

### SavedMappings Component

The SavedMappings component provides a comprehensive interface for managing, viewing, and exporting saved mappings. It allows users to browse all saved mapping files, view their contents, download them, and export them to EnOS for deployment.

#### Features

- Display list of saved mapping files
- Search and filter mappings
- Sort mappings by filename, size, or modification date
- View detailed mapping contents
- Download mapping files
- Export mappings to EnOS format
- Error handling and feedback

#### Component Structure

```typescript
interface SavedMapping {
  filename: string;
  filepath: string;
  size: number;
  modified: string;
}

interface MappingData {
  enosEntity: string;
  enosPoint: string;
  rawPoint: string;
  rawUnit: string;
  rawFactor: number;
  [key: string]: unknown;
}
```

#### Usage Example

```typescript
import { SavedMappings } from '../pages/SavedMappings';

function App() {
  return (
    <Router>
      <Route path="/saved-mappings" component={SavedMappings} />
    </Router>
  );
}
```

#### API Integration

The component integrates with the following API endpoints:

1. List Saved Files (`GET /api/bms/list-saved-files`)
2. Load CSV (`POST /api/bms/load-csv`)
3. Download File (`GET /api/bms/download-file`)
4. Export Mapping (`POST /api/bms/export-mapping`)

#### Styling

The component uses a modular CSS approach with BEM naming convention. Key style classes:

```css
.saved-mappings__content      // Main container
.saved-mappings__toolbar     // Top actions bar
.saved-mappings__table      // Mappings table
.saved-mappings__actions    // Action buttons container
.saved-mappings__details    // Details modal content
```

Custom styling can be applied by overriding these classes in your CSS files.

#### Best Practices

1. Error Handling:
   - Provide clear feedback for API failures
   - Show appropriate messages for empty states
   - Handle export failures gracefully

2. Performance:
   - Only load mapping details when requested
   - Implement search filtering on the client side
   - Use pagination for very large lists of files

3. User Experience:
   - Provide sorting capabilities for better organization
   - Allow filtering by filename
   - Show file size in human-readable format

4. Export Workflow:
   - Provide confirmation of successful exports
   - Display detailed error messages for failed exports
   - Allow downloading the original file and the exported version

### AssetSelector Component

The AssetSelector component provides a flexible and user-friendly interface for selecting assets from a list. It includes advanced filtering, search capabilities, pagination, and detail view functionality.

#### Features

- Asset listing with card-based UI
- Search functionality for finding assets by name, type, or description
- Filtering assets by type
- Pagination for large asset lists
- Detailed view of selected assets
- Status indicators for asset health
- Responsive design

#### Component Structure

```typescript
interface Asset {
  id: string;
  name: string;
  type: string;
  deviceCount?: number;
  description?: string;
  location?: string;
  status?: 'active' | 'inactive' | 'maintenance';
  lastUpdated?: string;
}

interface AssetSelectorProps {
  assets: Asset[];
  selectedAssetId: string | null;
  onAssetSelect: (assetId: string) => void;
  isLoading?: boolean;
  error?: string;
  allowSearch?: boolean;
  allowTypeFilter?: boolean;
  pageSize?: number;
}
```

#### Usage Example

```typescript
import { AssetSelector } from '../../components';
import { useAssets } from '../../services/assetService';

function MyComponent() {
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const { assets, isLoading, error } = useAssets({ mock: true });

  return (
    <AssetSelector
      assets={assets}
      selectedAssetId={selectedAssetId}
      onAssetSelect={setSelectedAssetId}
      isLoading={isLoading}
      error={error || ''}
      allowSearch={true}
      allowTypeFilter={true}
      pageSize={4}
    />
  );
}
```

#### Styling

The component uses a modular CSS approach with BEM naming convention. Key style classes:

```css
.asset-selector             // Main container
.asset-selector__header     // Header with title and search
.asset-selector__filters    // Type filters container
.asset-selector__list       // List of asset cards
.asset-selector__item       // Individual asset card
.asset-selector__detail     // Detail view panel
```

Custom styling can be applied by overriding these classes in your CSS files.

#### Asset Service Integration

The component works seamlessly with the assetService for fetching and managing assets:

```typescript
// Using the hook
const { assets, isLoading, error, refetch } = useAssets({
  mock: true,                   // Use mock data for development
  filterByStatus: 'active',     // Filter by status
  filterByType: 'Office Building', // Filter by type
  search: searchTerm           // Search term
});

// Direct API calls
const fetchAssets = async () => {
  try {
    const assets = await fetchAssets({ 
      mock: true,
      orgId: 'my-organization'
    });
    // Do something with assets
  } catch (error) {
    // Handle error
  }
};
```

#### Best Practices

1. Error Handling:
   - Always display appropriate messages for loading states
   - Show clear error messages when asset fetching fails
   - Provide empty state UI when no assets are found

2. Performance:
   - Use pagination for large asset lists
   - Implement debounced search to reduce API calls
   - Lazily load asset details only when needed

3. User Experience:
   - Maintain selection state when filtering/searching
   - Provide visual feedback for selected assets
   - Use status indicators to show asset health at a glance

4. Accessibility:
   - Include proper ARIA labels for all interactive elements
   - Ensure keyboard navigation works for all actions
   - Maintain sufficient color contrast for status indicators

### GroupPoints Component

The GroupPoints component provides a powerful interface for organizing BMS points into logical groups. It supports both manual grouping and AI-assisted grouping, with drag-and-drop functionality for easily managing point assignments.

#### Features

- Manual creation and editing of point groups
- AI-assisted grouping with multiple strategies
- Drag-and-drop interface for point assignment
- Group management (rename, delete, merge)
- Visual representation of group hierarchies
- Real-time filtering and search of points
- Expandable/collapsible group view

#### Component Structure

```typescript
interface GroupWithMetadata extends PointGroup {
  expanded?: boolean;
}

// PointGroup from apiTypes.ts
interface PointGroup {
  id: string;
  name: string;
  description?: string;
  points: BMSPoint[];
  subgroups?: Record<string, PointGroup>;
}
```

#### Usage Example

```typescript
import GroupPoints from '../pages/GroupPoints';
import { GroupingProvider } from '../contexts/GroupingContext';
import { PointsProvider } from '../contexts/PointsContext';

function App() {
  return (
    <PointsProvider>
      <GroupingProvider>
        <GroupPoints />
      </GroupingProvider>
    </PointsProvider>
  );
}
```

#### Grouping Context Integration

The component relies on the GroupingContext for state management:

```typescript
const {
  groups,
  loading,
  error,
  addGroup,
  removeGroup,
  updateGroup,
  addPointToGroup,
  removePointFromGroup,
  movePoint,
  clearGroups,
  setGroupingStrategy
} = useGroupingContext();
```

#### AI-Assisted Grouping

The component provides three grouping strategies:

1. **Default Grouping**: Groups points by device type and instance
2. **AI-Assisted Grouping**: Uses AI to analyze point names and group by equipment
3. **Ontology-Based Grouping**: Uses industry standard ontologies to identify equipment

Example of AI grouping call:

```typescript
const response = await groupPointsWithAI(points, {
  apiGateway: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  accessKey: '',
  secretKey: '',
  orgId: '',
  assetId: ''
});

if (response.success && response.grouped_points) {
  // Process grouped points
  const newGroups: Record<string, PointGroup> = {};
  
  Object.entries(response.grouped_points).forEach(([key, value]) => {
    const groupId = `group-${Date.now()}-${key}`;
    newGroups[groupId] = {
      id: groupId,
      name: value.name,
      description: value.description,
      points: value.points,
      subgroups: {} // Initialize empty subgroups
    };
  });
  
  // Clear existing groups and set the new ones
  clearGroups();
  Object.entries(newGroups).forEach(([key, group]) => {
    addGroup(key, group);
  });
}
```

#### Drag and Drop Functionality

The component implements drag-and-drop for:

1. Moving points between groups
2. Merging groups (by dragging one group onto another)

Example drag handlers:

```typescript
// Point drag start
const handlePointDragStart = (e: React.DragEvent, pointId: string) => {
  e.dataTransfer.setData('pointId', pointId);
  setDraggedPointId(pointId);
  e.dataTransfer.effectAllowed = 'move';
};

// Group drop handler
const handleGroupDrop = (e: React.DragEvent, groupId: string) => {
  e.preventDefault();
  const pointId = e.dataTransfer.getData('pointId');
  const draggedGroup = e.dataTransfer.getData('groupId');
  
  if (pointId && !draggedGroup) {
    // Point drop logic
    // ...
  } else if (draggedGroup && draggedGroup !== groupId) {
    // Group merge logic
    // ...
  }
};
```

#### Modal Dialogs

The component uses modal dialogs for:

1. Creating/editing groups
2. Confirming group deletion

#### Best Practices

1. Group Organization:
   - Group points by equipment type
   - Maintain consistent naming conventions
   - Provide clear descriptions

2. Performance:
   - Use filtering to manage large point sets
   - Expand only groups you're actively working with
   - Use AI grouping for initial organization, then refine manually

3. User Experience:
   - Use drag-and-drop for intuitive management
   - Provide keyboard shortcuts for common actions
   - Use clear visual indicators for group status and selection

4. Accessibility:
   - Ensure keyboard navigation for all interactive elements
   - Include appropriate ARIA attributes
   - Maintain high contrast for visual indicators

// ... existing code... 