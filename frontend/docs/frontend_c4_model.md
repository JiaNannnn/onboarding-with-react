# Frontend Architecture C4 Model (Detailed)

## Level 1: System Context Diagram

```mermaid
graph TD
    User["BMS Engineer"] <--> Frontend["BMS Onboarding Frontend"]
    Frontend --> Backend["BMS Onboarding Backend"]
    Backend --> LLM["OpenAI LLM Service"]
    Backend --> EnOS["EnOS Platform"]
    User --> BMS["Building Management System"]
    BMS --> Backend
    
    classDef user fill:#08427B,stroke:#052E56,color:#fff
    classDef frontend fill:#1168BD,stroke:#0B4884,color:#fff
    classDef backend fill:#5DB85C,stroke:#3C7F3C,color:#fff
    classDef external fill:#999999,stroke:#666666,color:#fff
    
    class User user
    class Frontend frontend
    class Backend backend
    class LLM,EnOS,BMS external
```

**Elements:**
- **BMS Engineer**: Domain expert who needs to onboard BMS points to the EnOS system
- **BMS Onboarding Frontend**: React application that provides the UI for the onboarding workflow
- **BMS Onboarding Backend**: Python Flask application that processes BMS data and communicates with LLMs
- **OpenAI LLM Service**: External API service that provides AI capabilities for mapping and grouping
- **EnOS Platform**: Target platform where the BMS points will be integrated
- **Building Management System**: Source system containing raw BMS points data

**Relationships:**
- BMS Engineer interacts with the Frontend to upload, group, and map BMS points
- Frontend communicates with Backend for data processing and AI services
- Backend communicates with OpenAI for AI processing of point data
- Backend communicates with EnOS to validate target point structures
- BMS Engineer extracts data from BMS systems
- Backend can directly import data from some BMS systems

## Level 2: Container Diagram

```mermaid
graph TD
    subgraph "BMS Onboarding Frontend System"
        ReactApp["React Application<br/><font size=2>User interface for BMS Onboarding</font>"]
        
        ReactApp -- "Sends requests to<br/>REST API" --> ApiClient["API Client<br/><font size=2>Type-safe HTTP client</font>"]
        
        subgraph "Backend API"
            BmsApi["BMS API<br/><font size=2>Handles BMS specific operations</font>"]
            GroupingApi["Grouping API<br/><font size=2>Handles AI grouping operations</font>"]
            MappingApi["Mapping API<br/><font size=2>Handles AI mapping operations</font>"]
            ExportApi["Export API<br/><font size=2>Handles file export operations</font>"]
        end
        
        ApiClient --> BmsApi
        ApiClient --> GroupingApi
        ApiClient --> MappingApi
        ApiClient --> ExportApi
    end
    
    User["BMS Engineer"] -- "Uses" --> ReactApp
    
    BmsApi -- "Processes BMS Points" --> BackendServer["Backend Server<br/><font size=2>Python Flask application</font>"]
    GroupingApi -- "Groups Points" --> BackendServer
    MappingApi -- "Maps Points" --> BackendServer
    ExportApi -- "Exports Results" --> BackendServer
    
    classDef container fill:#1168BD,stroke:#0B4884,color:#fff
    classDef component fill:#85BBF0,stroke:#5D82A8,color:#000
    classDef external fill:#999999,stroke:#666666,color:#fff
    classDef user fill:#08427B,stroke:#052E56,color:#fff
    
    class ReactApp container
    class ApiClient,BmsApi,GroupingApi,MappingApi,ExportApi component
    class BackendServer external
    class User user
```

**Elements:**
- **React Application**: Main frontend SPA built with React and TypeScript
- **API Client**: Type-safe client for backend communication
- **BMS API**: Handles BMS data retrieval operations
- **Grouping API**: Handles point grouping operations
- **Mapping API**: Handles point mapping operations
- **Export API**: Handles file export operations
- **Backend Server**: Python Flask application that implements the API endpoints

## Level 3: Component Diagram (Detailed)

```mermaid
graph TD
    subgraph "React Application"
        Router["React Router<br/><font size=2>Manages navigation between views</font>"]
        
        subgraph "Pages"
            GroupPointsPage["Group Points Page<br/><font size=2>UI for grouping BMS points</font>"]
            MapPointsPage["Map Points Page<br/><font size=2>UI for mapping points to EnOS</font>"]
            ResultsPage["Results Page<br/><font size=2>UI for viewing/exporting results</font>"]
        end
        
        Router --> GroupPointsPage
        Router --> MapPointsPage
        Router --> ResultsPage
        
        subgraph "Contexts"
            PointsContext["Points Context<br/><font size=2>Manages points state</font>"]
            GroupingContext["Grouping Context<br/><font size=2>Manages grouping state</font>"]
            MappingContext["Mapping Context<br/><font size=2>Manages mapping state</font>"]
        end
        
        GroupPointsPage --> PointsContext
        GroupPointsPage --> GroupingContext
        MapPointsPage --> PointsContext
        MapPointsPage --> MappingContext
        ResultsPage --> PointsContext
        ResultsPage --> MappingContext
        
        subgraph "Hooks"
            UseApi["useApi<br/><font size=2>Generic API hook</font>"]
            UseBMSClient["useBMSClient<br/><font size=2>BMS operations hook</font>"]
            UsePointsFiltering["usePointsFiltering<br/><font size=2>Point filtering hook</font>"]
            UseAIGrouping["useAIGrouping<br/><font size=2>AI grouping hook</font>"]
            UseEnhancedMapping["useEnhancedMapping<br/><font size=2>Enhanced mapping hook</font>"]
        end
        
        PointsContext --> UseApi
        GroupingContext --> UseApi
        GroupingContext --> UseAIGrouping
        MappingContext --> UseApi
        MappingContext --> UseBMSClient
        MappingContext --> UseEnhancedMapping
        
        UseApi --> ApiClient["API Client<br/><font size=2>Type-safe HTTP client</font>"]
        UseBMSClient --> BMSClient["BMS Client<br/><font size=2>BMS-specific client</font>"]
        UseAIGrouping --> ApiClient
        UseEnhancedMapping --> BMSClient
        
        BMSClient --> ApiClient
        
        subgraph "UI Components"
            FileUploadForm["File Upload Form<br/><font size=2>CSV/JSON file upload</font>"]
            PointsTable["Points Table<br/><font size=2>Displays points data</font>"]
            PointsFilter["Points Filter<br/><font size=2>Filters points by criteria</font>"]
            GroupForm["Group Form<br/><font size=2>Creates/edits groups</font>"]
            GroupList["Group List<br/><font size=2>Displays point groups</font>"]
            AIControls["AI Controls<br/><font size=2>Triggers AI operations</font>"]
        end
        
        GroupPointsPage --> FileUploadForm
        GroupPointsPage --> PointsTable
        GroupPointsPage --> PointsFilter
        GroupPointsPage --> GroupForm
        GroupPointsPage --> GroupList
        GroupPointsPage --> AIControls
        
        MapPointsPage --> FileUploadForm
        MapPointsPage --> PointsTable
        MapPointsPage --> PointsFilter
        MapPointsPage --> AIControls
        
        PointsFilter --> UsePointsFiltering
    end
    
    classDef container fill:#1168BD,stroke:#0B4884,color:#fff
    classDef component fill:#85BBF0,stroke:#5D82A8,color:#000
    classDef page fill:#438DD5,stroke:#2C5986,color:#fff
    classDef context fill:#70ad47,stroke:#507c36,color:#fff
    classDef hook fill:#ba5d16,stroke:#8c4d16,color:#fff
    classDef client fill:#ff8c00,stroke:#d97700,color:#fff
    classDef ui fill:#6b6bb8,stroke:#4f4f89,color:#fff
    
    class Router container
    class GroupPointsPage,MapPointsPage,ResultsPage page
    class PointsContext,GroupingContext,MappingContext context
    class UseApi,UseBMSClient,UsePointsFiltering,UseAIGrouping,UseEnhancedMapping hook
    class ApiClient,BMSClient client
    class FileUploadForm,PointsTable,PointsFilter,GroupForm,GroupList,AIControls ui
```

## Level 4: Detailed Component Diagram (MappingContext Flow)

```mermaid
graph TD
    subgraph "Mapping Context System"
        MappingContext["MappingContext<br/><font size=2>Central mapping state management</font>"]
        
        MappingContext --> MapPointsToEnOS["mapPointsToEnOS()<br/><font size=2>Initiates point mapping</font>"]
        MappingContext --> CheckMappingStatus["checkMappingStatus()<br/><font size=2>Polls for task status</font>"]
        MappingContext --> ImproveMappingResults["improveMappingResults()<br/><font size=2>Initiates second-round mapping</font>"]
        MappingContext --> AnalyzeMappingQuality["analyzeMappingQuality()<br/><font size=2>Evaluates mapping quality</font>"]
        
        MapPointsToEnOS --> UseBMSClient["useBMSClient<br/><font size=2>BMS client hook</font>"]
        CheckMappingStatus --> UseBMSClient
        ImproveMappingResults --> UseBMSClient
        AnalyzeMappingQuality --> EnhancedMapping["enhancedMapping<br/><font size=2>Quality assessment utilities</font>"]
        
        UseBMSClient --> BMSClient["BMSClient<br/><font size=2>BMS API client</font>"]
        EnhancedMapping --> ValidateAgainstSchema["validateAgainstSchema()<br/><font size=2>Validates against EnOS schema</font>"]
        EnhancedMapping --> DetectGenericMappings["detectGenericMappings()<br/><font size=2>Finds generic/poor mappings</font>"]
        EnhancedMapping --> SuggestBetterMappings["suggestBetterMappings()<br/><font size=2>Suggests improved mappings</font>"]
        
        BMSClient --> MapPointsToEnOSRequest["mapPointsToEnOS()<br/><font size=2>API request</font>"]
        BMSClient --> CheckPointsMappingStatus["checkPointsMappingStatus()<br/><font size=2>API request</font>"]
        BMSClient --> ImproveMappingResultsRequest["improveMappingResults()<br/><font size=2>API request</font>"]
        BMSClient --> APIClient["APIClient<br/><font size=2>Generic API client</font>"]
        
        ValidateAgainstSchema --> EnOSSchema["EnOS Schema<br/><font size=2>enos_simplified.json</font>"]
        
        APIClient --> BackendAPI["Backend API<br/><font size=2>Flask endpoints</font>"]
    end
    
    classDef context fill:#70ad47,stroke:#507c36,color:#fff
    classDef method fill:#ff8c00,stroke:#d97700,color:#fff
    classDef hook fill:#ba5d16,stroke:#8c4d16,color:#fff
    classDef utility fill:#6b6bb8,stroke:#4f4f89,color:#fff
    classDef client fill:#1168BD,stroke:#0B4884,color:#fff
    classDef external fill:#999999,stroke:#666666,color:#fff
    classDef data fill:#4bacc6,stroke:#31859b,color:#fff
    
    class MappingContext context
    class MapPointsToEnOS,CheckMappingStatus,ImproveMappingResults,AnalyzeMappingQuality method
    class UseBMSClient hook
    class EnhancedMapping,ValidateAgainstSchema,DetectGenericMappings,SuggestBetterMappings utility
    class BMSClient,APIClient client
    class MapPointsToEnOSRequest,CheckPointsMappingStatus,ImproveMappingResultsRequest method
    class BackendAPI external
    class EnOSSchema data
```

## Code-Level Diagram: Mapping Enhancement System

```mermaid
classDiagram
    class MappingContext {
        +mappingResults: MappingResult[]
        +isLoading: boolean
        +error: Error | null
        +taskId: string | null
        +progress: number
        +batchMode: boolean
        +totalBatches: number
        +completedBatches: number
        +mapPointsToEnOS(points: BMSPoint[], config: MappingConfig): Promise<void>
        +checkMappingStatus(taskId: string): Promise<void>
        +improveMappingResults(taskId: string, qualityFilter: string): Promise<void>
        +analyzeMappingQuality(): MappingQualityReport
    }
    
    class BMSClient {
        +mapPointsToEnOS(points: BMSPoint[], config: MappingConfig): Promise<MapPointsToEnOSResponse>
        +checkPointsMappingStatus(taskId: string): Promise<TaskStatusResponse>
        +improveMappingResults(taskId: string, qualityFilter: string, config: MappingConfig): Promise<MapPointsToEnOSResponse>
        -post(endpoint: string, data: any): Promise<any>
        -get(endpoint: string): Promise<any>
    }
    
    class APIClient {
        +request<T>(config: RequestConfig): Promise<T>
        -handleError(error: unknown): Error
    }
    
    class EnhancedMapping {
        +analyzeMappingQuality(mappingResults: MappingResult[]): MappingQualityReport
        +isValidEnosPoint(deviceType: string, enosPoint: string): boolean
        +suggestBetterMapping(originalPoint: string, deviceType: string): string
        +detectGenericMappings(mappingResult: MappingResult): boolean
        +getValidPointsForDeviceType(deviceType: string): string[]
        -loadEnOSSchema(): EnOSSchema
    }
    
    class UseBMSClient {
        +client: BMSClient
        +isLoading: boolean
        +error: Error | null
        +mapPointsToEnOS(points: BMSPoint[], config: MappingConfig): Promise<MapPointsToEnOSResponse>
        +checkPointsMappingStatus(taskId: string): Promise<TaskStatusResponse>
        +improveMappingResults(taskId: string, qualityFilter: string, config: MappingConfig): Promise<MapPointsToEnOSResponse>
        +analyzeCSVDeviceTypes(csvFilePath: string): Promise<string[]>
        -withStateHandling<T>(operation: () => Promise<T>): Promise<T>
    }
    
    class MapPointsComponent {
        +points: BMSPoint[]
        +mappingResults: MappingResult[]
        +isLoading: boolean
        +error: Error | null
        +progress: number
        +handleMapPoints(): void
        +handleImproveMapping(): void
        +renderMappingQuality(quality: string): ReactNode
        +renderProgressBar(): ReactNode
    }
    
    MappingContext --> BMSClient: uses
    MappingContext --> EnhancedMapping: uses
    BMSClient --> APIClient: uses
    UseBMSClient --> BMSClient: wraps
    UseBMSClient --> EnhancedMapping: uses
    MapPointsComponent --> MappingContext: consumes
```

## Data Flow Diagram: First-Round Mapping Process

```mermaid
sequenceDiagram
    participant User as BMS Engineer
    participant UI as MapPoints Component
    participant Context as MappingContext
    participant Hook as useBMSClient
    participant Client as BMSClient
    participant API as APIClient
    participant Backend as Backend API
    participant LLM as OpenAI LLM
    
    User->>UI: Uploads CSV file
    Note over UI: Parse CSV data
    UI->>UI: Transforms data to BMSPoint[]
    User->>UI: Clicks "Map Points" button
    UI->>Context: mapPointsToEnOS(points, config)
    Context->>Hook: mapPointsToEnOS(points, config)
    Hook->>Hook: Set isLoading = true
    Hook->>Client: mapPointsToEnOS(points, config)
    
    alt Has device types for batching
        Client->>Client: Group points by deviceType
        Client->>Client: Set batchMode = true
    else No device type info
        Client->>Client: Process all points at once
    end
    
    Client->>API: request({ url: '/bms/map-points', method: 'POST', data })
    API->>Backend: POST /api/bms/map-points
    Backend->>Backend: Start async task
    Backend-->>API: { taskId: 'abc123', batchMode: true, totalBatches: 5 }
    API-->>Client: MapPointsToEnOSResponse
    Client-->>Hook: MapPointsToEnOSResponse
    Hook->>Context: Set taskId, batchMode, totalBatches
    
    loop Polling
        Context->>Hook: checkMappingStatus(taskId)
        Hook->>Client: checkPointsMappingStatus(taskId)
        Client->>API: request({ url: `/bms/task-status/${taskId}` })
        API->>Backend: GET /api/bms/task-status/{taskId}
        
        alt Task in Progress
            Backend->>LLM: Process batch of points
            LLM-->>Backend: Mapping results for batch
            Backend-->>API: { status: 'in_progress', progress: 60, completedBatches: 3 }
            API-->>Client: TaskStatusResponse
            Client-->>Hook: Update progress state
            Hook-->>Context: Update progress, completedBatches
            Context-->>UI: Render progress (60%)
        else Task Complete
            Backend-->>API: { status: 'completed', results: [...] }
            API-->>Client: TaskStatusResponse with results
            Client-->>Hook: Process completed task
            Hook-->>Context: Update mappingResults
            Context->>Context: analyzeMappingQuality()
            Context-->>UI: Render mapping results with quality indicators
            UI-->>User: Display mapping results table
        end
    end
```

## Data Flow Diagram: Second-Round Mapping Improvement Process

```mermaid
sequenceDiagram
    participant User as BMS Engineer
    participant UI as MapPoints Component
    participant Context as MappingContext
    participant Mapper as EnhancedMapping
    participant Hook as useBMSClient
    participant Client as BMSClient
    participant API as APIClient
    participant Backend as Backend API
    participant LLM as OpenAI LLM
    
    Note over UI: Mapping results already loaded
    
    Context->>Mapper: analyzeMappingQuality(mappingResults)
    Mapper->>Mapper: Load enos_simplified.json schema
    
    loop For each mapping result
        Mapper->>Mapper: isValidEnosPoint(deviceType, enosPoint)
        Mapper->>Mapper: detectGenericMappings(result)
        alt Poor quality mapping
            Mapper->>Mapper: Mark as "poor" quality
            Mapper->>Mapper: suggestBetterMapping()
        else Generic mapping
            Mapper->>Mapper: Mark as "unacceptable" quality
            Mapper->>Mapper: suggestBetterMapping()
        else Good mapping
            Mapper->>Mapper: Mark as "good" quality
        end
    end
    
    Mapper-->>Context: MappingQualityReport
    Context-->>UI: Update with quality indicators
    UI-->>User: Display quality indicators and improvement button
    
    User->>UI: Clicks "Improve Mappings" button
    UI->>Context: improveMappingResults(taskId, 'below_fair')
    Context->>Hook: improveMappingResults(taskId, 'below_fair')
    Hook->>Client: improveMappingResults(taskId, 'below_fair', config)
    
    Client->>Client: Filter original points (only poor quality)
    Client->>Client: Add quality feedback to request
    Client->>API: request({ url: '/bms/improve-mappings', method: 'POST', data })
    API->>Backend: POST /api/bms/improve-mappings
    Backend->>Backend: Extract poor mappings
    Backend->>Backend: Prepare enhanced context for LLM
    Backend->>LLM: Process with additional context
    Note over Backend,LLM: Include feedback on poor mappings
    Note over Backend,LLM: Include device type context
    Note over Backend,LLM: Include examples of good mappings
    LLM-->>Backend: Improved mapping results
    
    Backend-->>API: { taskId: 'def456' }
    API-->>Client: MapPointsToEnOSResponse
    
    loop Polling for improved results
        Client->>API: request({ url: `/bms/task-status/${taskId}` })
        API->>Backend: GET /api/bms/task-status/{taskId}
        Backend-->>API: Status updates
        API-->>Client: TaskStatusResponse
    end
    
    Backend-->>API: { status: 'completed', results: [...] }
    API-->>Client: TaskStatusResponse with improved results
    Client-->>Hook: Process completed task
    Hook->>Hook: Merge improved results with originals
    Hook-->>Context: Update mappingResults with improvements
    Context->>Mapper: analyzeMappingQuality(updatedResults)
    Mapper-->>Context: Updated MappingQualityReport
    Context-->>UI: Render improved mapping results
    UI-->>User: Display improved mappings with quality indicators
```

## Component Detail: Enhanced Mapping System

```mermaid
flowchart TD
    subgraph "Enhanced Mapping System"
        direction TB
        
        EnhancedMapping["enhancedMapping.ts<br/><font size=2>Mapping quality assessment system</font>"]
        
        subgraph "Quality Analysis Functions"
            AnalyzeQuality["analyzeMappingQuality()<br/><font size=2>Main quality analysis function</font>"]
            IsValidPoint["isValidEnosPoint()<br/><font size=2>Validates point against schema</font>"]
            DetectGeneric["detectGenericMappings()<br/><font size=2>Identifies generic mappings</font>"]
            SuggestBetter["suggestBetterMapping()<br/><font size=2>Suggests improvements</font>"]
        end
        
        subgraph "Schema Validation"
            LoadSchema["loadEnOSSchema()<br/><font size=2>Loads schema from JSON</font>"]
            GetValid["getValidPointsForDeviceType()<br/><font size=2>Gets valid points list</font>"]
            ValidatePattern["validatePointPattern()<br/><font size=2>Validates naming patterns</font>"]
        end
        
        subgraph "Pattern Matching"
            ExtractDevice["extractDeviceType()<br/><font size=2>Extracts type from name</font>"]
            FindPattern["findPointPatterns()<br/><font size=2>Finds common patterns</font>"]
            ApplyHeuristics["applyPointHeuristics()<br/><font size=2>Applies mapping rules</font>"]
        end
        
        EnhancedMapping --> AnalyzeQuality
        AnalyzeQuality --> IsValidPoint
        AnalyzeQuality --> DetectGeneric
        AnalyzeQuality --> SuggestBetter
        
        IsValidPoint --> LoadSchema
        IsValidPoint --> GetValid
        GetValid --> LoadSchema
        
        SuggestBetter --> FindPattern
        SuggestBetter --> ApplyHeuristics
        SuggestBetter --> ExtractDevice
        DetectGeneric --> ValidatePattern
    end
    
    UseBMSClient["useBMSClient.ts<br/><font size=2>BMS client hook</font>"] --> EnhancedMapping
    MappingContext["MappingContext.tsx<br/><font size=2>Mapping state management</font>"] --> EnhancedMapping
    
    EnhancedMapping --> EnOSSchema["enos_simplified.json<br/><font size=2>Point schema definition</font>"]
    
    classDef module fill:#1168BD,stroke:#0B4884,color:#fff
    classDef mainFunc fill:#70ad47,stroke:#507c36,color:#fff
    classDef utilFunc fill:#ff8c00,stroke:#d97700,color:#fff
    classDef schema fill:#6b6bb8,stroke:#4f4f89,color:#fff
    classDef consumer fill:#ba5d16,stroke:#8c4d16,color:#fff
    
    class EnhancedMapping module
    class AnalyzeQuality,IsValidPoint,DetectGeneric,SuggestBetter mainFunc
    class LoadSchema,GetValid,ValidatePattern,ExtractDevice,FindPattern,ApplyHeuristics utilFunc
    class EnOSSchema schema
    class UseBMSClient,MappingContext consumer
```

## Implementation Status (Detailed)

| Phase | Task | Status | Details |
|-------|------|--------|---------|
| **1. Setup and Configuration** | Configure TypeScript | ✅ Complete | Strict typing, no implicit any |
| | Set up project structure | ✅ Complete | Feature-based organization |
| | Configure API client | ✅ Complete | Type-safe request/response handling |
| **2. Core Components and State** | Points Context | ✅ Complete | Global state for points data |
| | Mapping Context | ✅ Complete | State management for mapping operations |
| | BMS Client | ✅ Complete | BMS-specific API client |
| **3. Feature Implementation** | T1: Mapping Quality Assessment | ✅ Complete | Added quality analysis and validation |
| | | | - analyzeMappingQuality function |
| | | | - Schema validation |
| | | | - Generic mapping detection |
| | | | - Quality indicators (good/fair/poor) |
| | T2: CSV/JSON Parsing | ❌ Not Started | Tools for parsing input data |
| | T3: MapPoints Page | ❌ Not Started | UI for mapping functionality |
| | T4: Data Grid Integration | ❌ Not Started | Displaying mapping results |
| | T5: Second-round Mapping | ✅ Complete | Enhanced mapping improvements |
| | | | - improveMappingResults method |
| | | | - Quality feedback mechanism |
| | | | - Suggestion system |
| | T6: Batch Processing | ✅ Complete | Process points in batches |
| | | | - Device type analysis |
| | | | - Progress tracking |
| | | | - Batch mode API support |
| | T7: Export Functionality | ❌ Not Started | Exporting mapping results |
| **4. Cross-Domain Adaptability** | Protocol Adapters | ❌ Not Started | Support for different data sources |
| | Dynamic UI | ❌ Not Started | Adaptable UI components |
| | Template Configuration | ❌ Not Started | Configurable mapping templates |
| **5. Testing and Optimization** | Unit Tests | ❌ Not Started | Component and function tests |
| | Integration Tests | ❌ Not Started | End-to-end workflow tests |
| | Performance Optimization | ❌ Not Started | Improve rendering and processing |

## Technical Dependencies

```mermaid
graph TD
    Frontend["Frontend Application"] --> React["React 18.x<br/><font size=2>UI Framework</font>"]
    Frontend --> TypeScript["TypeScript 4.9+<br/><font size=2>Type System</font>"]
    Frontend --> ReactRouter["React Router 6.x<br/><font size=2>Routing</font>"]
    Frontend --> Axios["Axios<br/><font size=2>HTTP Client</font>"]
    Frontend --> HandsonTable["Handsontable<br/><font size=2>Data Grid</font>"]
    Frontend --> ReactContext["React Context API<br/><font size=2>State Management</font>"]
    
    HandsonTable --> DataExport["Export Plugin<br/><font size=2>CSV/Excel Export</font>"]
    
    TypeScript --> ESLint["ESLint<br/><font size=2>Code Quality</font>"]
    TypeScript --> Prettier["Prettier<br/><font size=2>Code Formatting</font>"]
    
    classDef core fill:#1168BD,stroke:#0B4884,color:#fff
    classDef lib fill:#70ad47,stroke:#507c36,color:#fff
    classDef tool fill:#ba5d16,stroke:#8c4d16,color:#fff
    classDef plugin fill:#6b6bb8,stroke:#4f4f89,color:#fff
    
    class Frontend core
    class React,TypeScript,ReactRouter,Axios,HandsonTable,ReactContext lib
    class ESLint,Prettier tool
    class DataExport plugin
```