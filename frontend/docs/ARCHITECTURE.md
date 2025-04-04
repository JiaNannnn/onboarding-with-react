# Frontend Architecture Documentation

## Overview

This document provides a comprehensive overview of the frontend architecture for the BMS to EnOS Onboarding Tool. The architecture is designed with strict type safety as a fundamental principle, implemented using React with TypeScript, and following a feature-based organization approach.

## C4 Model Architecture

### System Context Diagram

```
┌───────────────────────────┐          ┌───────────────────────────┐
│                           │          │                           │
│                           │          │                           │
│        BMS Engineer       │◄────────►│  BMS Onboarding Frontend  │
│                           │          │                           │
│                           │          │                           │
└───────────────────────────┘          └─────────────┬─────────────┘
                                                     │
                                                     │
                                                     │
                                                     ▼
                                       ┌───────────────────────────┐
                                       │                           │
                                       │                           │
                                       │   BMS Onboarding Backend  │
                                       │                           │
                                       │                           │
                                       └───────────────────────────┘
```

**Elements:**
- **BMS Engineer**: The primary user who needs to onboard BMS points to the EnOS system
- **BMS Onboarding Frontend**: The React application that provides the user interface for the onboarding workflow
- **BMS Onboarding Backend**: The Python Flask application that processes BMS data and communicates with LLMs

**Relationships:**
- BMS Engineer interacts with the Frontend to upload, group, and map BMS points
- Frontend communicates with Backend to process data and use AI services

### Container Diagram (React Application)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         BMS Onboarding Frontend                             │
│                                                                             │
│  ┌───────────────┐      ┌───────────────┐      ┌───────────────────────┐   │
│  │               │      │               │      │                       │   │
│  │  React Router │      │  React Contexts │    │  Type-Safe API Client │   │
│  │               │      │               │      │                       │   │
│  └───────┬───────┘      └───────┬───────┘      └─────────┬─────────────┘   │
│          │                      │                        │                  │
│          ▼                      ▼                        ▼                  │
│  ┌───────────────┐      ┌───────────────┐      ┌───────────────────────┐   │
│  │               │      │               │      │                       │   │
│  │  UI Components │     │  Custom Hooks │      │  Utility Functions    │   │
│  │               │      │               │      │                       │   │
│  └───────────────┘      └───────────────┘      └───────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Elements:**
- **React Router**: Handles navigation between different views
- **React Contexts**: Global state management
- **Type-Safe API Client**: Communication with the backend
- **UI Components**: Reusable visual components
- **Custom Hooks**: Business logic and data handling
- **Utility Functions**: Helper functions for data transformation

### Component Diagram (React App)

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                                 React Application                                  │
│                                                                                   │
│  ┌─────────────────┐    ┌──────────────────┐    ┌───────────────────────────┐    │
│  │                 │    │                  │    │                           │    │
│  │  Group Points   │    │   Map Points     │    │   View/Export Results     │    │
│  │     Page        │    │     Page         │    │         Page              │    │
│  │                 │    │                  │    │                           │    │
│  └────────┬────────┘    └────────┬─────────┘    └───────────────┬───────────┘    │
│           │                      │                              │                 │
│           │                      │                              │                 │
│           ▼                      ▼                              ▼                 │
│  ┌────────────────┐     ┌─────────────────┐         ┌────────────────────┐       │
│  │                │     │                 │         │                    │       │
│  │ Points Context │     │ Mapping Context │         │  Results Context   │       │
│  │                │     │                 │         │                    │       │
│  └────────┬───────┘     └────────┬────────┘         └──────────┬─────────┘       │
│           │                      │                             │                  │
│           │                      │                             │                  │
│           ▼                      ▼                             ▼                  │
│  ┌────────────────┐     ┌─────────────────┐         ┌────────────────────┐       │
│  │                │     │                 │         │                    │       │
│  │ API Client     │────►│  BMS Client     │─────────►  File Export       │       │
│  │                │     │                 │         │                    │       │
│  └────────────────┘     └─────────────────┘         └────────────────────┘       │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

**Elements:**
- **Pages**: Main UI screens (Group Points, Map Points, View Results)
- **Contexts**: State management for different domains (Points, Mapping, Results)
- **Clients**: API communication (API Client, BMS Client)
- **Services**: Business logic (File Export)

### Code Diagram (Key Classes and Functions)

```
┌─────────────────────┐      ┌────────────────────────┐      ┌───────────────────┐
│                     │      │                        │      │                   │
│   useBMSClient      │◄─────┤     bmsClient.ts      │◄─────┤    apiClient.ts   │
│                     │      │                        │      │                   │
└─────────┬───────────┘      └────────────────────────┘      └───────────────────┘
          │                                  ▲
          │                                  │
          ▼                                  │
┌─────────────────────┐      ┌────────────────────────┐      ┌───────────────────┐
│                     │      │                        │      │                   │
│ enhancedMapping.ts  │─────►│    MappingContext     │─────►│  MapPoints Page   │
│                     │      │                        │      │                   │
└─────────────────────┘      └────────────────────────┘      └───────────────────┘
```

**Key Components:**

1. **bmsClient.ts**:
   - Handles communication with BMS-specific backend endpoints
   - Methods for mapping points, checking mapping status, improving mapping results

2. **useBMSClient Hook**:
   - Provides React components with access to BMS client functionality
   - Manages loading, error states, and async operations
   - Adds device type analysis and enhanced mapping capabilities

3. **enhancedMapping.ts**:
   - Contains mapping quality assessment logic
   - Validates EnOS point mappings against known schemas
   - Suggests improved mappings based on patterns and known valid points
   - Handles batch processing for more efficient mapping

4. **MappingContext**:
   - Centralizes mapping state across components
   - Provides mapping-related functions to components
   - Manages mapping status, results, and error states

5. **MapPoints Page**:
   - Main UI for point mapping functionality
   - Displays mapping results with quality indicators
   - Allows users to trigger mapping improvements
   - Shows mapping progress and status updates

### Data Flow

1. **Point Mapping Flow**:
   ```
   User uploads CSV → Points parsed → Map button clicked → 
   bmsClient.mapPointsToEnOS() → Backend processes → 
   Polling for results → Mapping results displayed →
   Quality assessment → User requests improvement →
   bmsClient.improveMappingResults() → Enhanced results
   ```

2. **Mapping Improvement Flow**:
   ```
   Mapping results loaded → analyzeMappingQuality() →
   Poor mappings identified → improveMappingResults() →
   Backend reprocesses points → Enhanced results displayed
   ```

3. **Batch Processing Flow**:
   ```
   CSV analyzed → analyzeCSVDeviceTypes() → 
   Device types identified → Points grouped by device →
   Batch processing initiated → Progress tracking →
   Results aggregated → Complete mapping displayed
   ```

## Architectural Principles

1. **Strong Type Safety**: No `any` types, strict null checking, and complete type definitions
2. **Feature-Based Organization**: Components organized by feature and responsibility
3. **Context-Based State Management**: React Context API for global state management
4. **Task-Based Implementation**: Modular development approach with independent feature tasks
5. **Comprehensive Error Handling**: Type-safe error handling throughout the application

## Directory Structure

```
frontend-architecture/
├── src/
│   ├── api/              # API integration services
│   │   ├── apiClient.ts  # Type-safe API client
│   │   ├── bmsClient.ts  # BMS-specific API client
│   │   └── index.ts      # API exports
│   ├── components/       # UI components
│   │   ├── common/       # Reusable UI components
│   │   └── feature/      # Feature-specific components
│   ├── context/          # Global state management
│   │   ├── PointsContext.tsx
│   │   └── MappingContext.tsx
│   ├── hooks/            # Custom React hooks
│   │   ├── useBMSClient.ts
│   │   └── enhancedMapping.ts
│   ├── pages/            # Main application pages
│   │   ├── GroupPoints/
│   │   └── MapPoints/
│   ├── types/            # TypeScript type definitions
│   │   ├── apiTypes.ts
│   │   ├── bmsTypes.ts
│   │   └── mappingTypes.ts
│   ├── utils/            # Utility functions
│   └── App.tsx           # Main application component
└── docs/                 # Documentation
    └── ARCHITECTURE.md   # This document
```

## Core Components

### 1. Type System

The type system is the foundation of the architecture, providing:

- **Strict Type Checking**: Configured in `tsconfig.json` with the strictest TypeScript settings
- **Domain-Specific Types**: Defined in the `types/` directory for all domain objects
- **Type Guards**: Used for safely working with unknown data types
- **No `any` Types**: Strictly avoided throughout the codebase

### 2. API Layer

The API layer provides type-safe communication with the backend:

- **Generic API Client**: Ensures type safety through the request/response lifecycle
- **Typed Endpoints**: Domain-specific API endpoints with proper request/response typing
- **Error Handling**: Consistent error handling with typed error objects
- **Request/Response Types**: Explicit typing for all API interactions

### 3. State Management

State management is implemented using React Context API:

- **PointsContext**: Points-related state (fetching, selection)
- **MappingContext**: Mapping-related state (status, results, quality)
- **Type-Safe Hooks**: Custom hooks for accessing context with proper typing

### 4. Component Architecture

Components follow a hierarchical structure:

- **Pages**: Top-level components representing entire screens
- **Feature Components**: Domain-specific components tied to business functionality
- **Common Components**: Reusable UI elements with consistent behavior
- **Component Props**: Strictly typed with explicit interfaces

### 5. Error Handling

Error handling follows a consistent pattern:

- **Error Types**: Typed error objects with specific error categories
- **Type Guards**: Used to safely handle various error types
- **Context-Based Errors**: Global error state managed through context
- **Component-Level Errors**: Local error states for form validation and user feedback

## Implementation Approach

The implementation follows a task-based approach:

1. **Phase 1**: Setup and Configuration (Complete)
2. **Phase 2**: Core Components and State (Complete)
3. **Phase 3**: Feature Implementation (In Progress)
   - T1: Implement mapping quality assessment (Complete)
   - T2: Implement CSV/JSON parsing tools
   - T3: Create the MappingPage page layout and upload button
   - T4: Integrate Handsontable for point display
   - T5: Implement second-round mapping improvements (Complete)
   - T6: Add device type analysis for batch processing (Complete)
   - T7: Implement "Export to CSV" functionality
4. **Phase 4**: Cross-Domain Adaptability (Not Started)
5. **Phase 5**: Testing and Optimization (Not Started)

## Key Design Decisions

### TypeScript Configuration

- Strict type checking enabled
- No implicit `any` types
- Strict null checks
- Explicit return types required

### API Design

- Generic request function with typed responses
- Error handling with dedicated error types
- Promise-based API with proper typing

### Component Design

- Functional components with React hooks
- Explicit prop interfaces
- Consistent naming conventions
- Separation of concerns

### State Management

- Context API for global state
- Local component state for UI-specific state
- Custom hooks for accessing global state
- Type-safe state management

## Cross-Cutting Concerns

### Accessibility

- Semantic HTML
- ARIA attributes
- Keyboard navigation support
- Focus management

### Performance

- Memoization for expensive calculations
- Virtualization for large datasets
- Lazy loading for components
- Code splitting for optimized loading

### Security

- Input validation
- XSS prevention
- CSRF protection
- Authentication and authorization

## Integration Points

### Backend Integration

- Type-safe API client for backend communication
- Consistent error handling
- Automated type validation

### Cross-Domain Adaptability

- Protocol adapters for different data sources
- Dynamic UI components
- Template-based configuration

## Dependencies

Major dependencies include:

- React
- TypeScript
- React Router
- Handsontable (for data grid)