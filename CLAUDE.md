# Onboarding React App Development Guide

## Build Commands
- **Dev Environment**: `npm run dev` (starts frontend + backend)
- **Frontend Only**: `cd frontend && npm start`
- **Backend Only**: `python backend/run_server.py`
- **Build**: `cd frontend && npm run build`
- **Lint (Frontend)**: `cd frontend && npm run lint`
- **Format (Frontend)**: `cd frontend && npm run format` 
- **TypeCheck**: `cd frontend && npm run typecheck`

## Test Commands
- **Frontend Tests**: `cd frontend && npm test`
- **Single Test (Frontend)**: `cd frontend && npm test -- -t 'test name'`
- **Backend Tests**: `python -m unittest discover backend/tests`
- **Single Test (Backend)**: `python -m unittest backend/tests/test_file.py::TestClass::test_method`
- **Memory Tests**: `python tests/test_memory_usage.py test`

## Architecture Overview

The frontend follows a type-safe React architecture with:
- Feature-based organization
- Context-based state management
- Strict type safety
- Comprehensive error handling

### Directory Structure
```
frontend/
├── src/
│   ├── api/              # API integration services
│   │   ├── apiClient.ts  # Type-safe API client
│   │   └── pointsApi.ts  # Points-related endpoints
│   ├── components/       # UI components
│   │   ├── common/       # Reusable UI components
│   │   └── feature/      # Feature-specific components
│   ├── context/          # Global state management
│   │   ├── AppContext.tsx
│   │   └── PointsContext.tsx
│   ├── hooks/            # Custom React hooks
│   ├── pages/            # Main application pages
│   ├── types/            # TypeScript type definitions
│   ├── utils/            # Utility functions
│   └── App.tsx           # Main application component
└── docs/                 # Documentation
```

## Code Style Guidelines

### TypeScript
- **No `any` Types**: Use `unknown` with type guards instead
- **Explicit Function Return Types**: Always specify return types
- **Type Guards**: Use proper type guards for unknown data
- **Strict Null Checking**: Always check for null/undefined
- **Component Props**: Define explicit interfaces for all components
- **Discriminated Unions**: Use for complex state management
- **API Types**: Define request/response types for all endpoints
- **Path Aliases**: Use `@components/`, `@context/`, `@api/`, etc.

```typescript
// ✅ GOOD: Type-safe error handling
try {
  // Operation that might fail
} catch (error: unknown) {
  if (error instanceof Error) {
    console.error(error.message);
  } else {
    console.error('Unknown error occurred');
  }
}

// ✅ GOOD: Component with type-safe props
interface ButtonProps {
  variant?: 'primary' | 'secondary';
  onClick?: () => void;
  disabled?: boolean;
  children: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  onClick,
  disabled = false,
  children,
}) => {
  // Implementation
};
```

### Component Structure
- Use functional components with hooks (no class components)
- Use React Context API for global state management
- Break large components into smaller, focused ones
- Follow a clear organization with comments for sections
- Import order: React/libraries → components → contexts → utils

### Error Handling
- Catch errors at API level
- Use ErrorBoundary for components
- Type-safe error objects with specific error categories
- Global error state through context
- Component-level error states for form validation

## API Client Usage

The frontend communicates with the backend through a type-safe API client:

```typescript
// Example of type-safe API request
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

### Core API Endpoints
- `/api/bms/fetch-points`: Fetches points from BMS
- `/api/bms/ai-group-points`: Groups points using AI
- `/api/bms/save-mapping`: Saves mapping configuration
- `/api/bms/list-saved-files`: Lists saved mapping files
- `/api/bms/load-csv`: Loads CSV file from results directory
- `/api/bms/generate-tags`: Generates tags for BMS points

## Python Guidelines
- Use type hints for function parameters and return values
- Follow snake_case for variables/functions, PascalCase for classes
- Document with docstrings using triple double-quotes
- Validated input with Pydantic models
- Use consistent error handling with try/except blocks
- Log errors with the centralized logging module
- Always use `python backend/run_server.py` to run the backend server
- Python path setup: The script adds project root and backend dir to sys.path

## Issue Tracking

Issues are categorized with the following priorities:
- **P0 - Critical**: Must be fixed immediately, blocking development
- **P1 - High**: Should be fixed in the current sprint
- **P2 - Medium**: Should be addressed soon, but not blocking
- **P3 - Low**: Nice to have, can be addressed when time allows

## Implementation Progress

Current progress (as of last update):
- Phase 1 (Setup and Configuration): 100% Complete
- Phase 2 (Core Components and State): 100% Complete
- Phase 3 (Feature Implementation): 7% Complete
- Phase 4 (Cross-Domain Adaptability): Not Started
- Phase 5 (Testing and Optimization): Not Started

For more detailed documentation, refer to the following files:
- Architecture details: `/frontend/docs/ARCHITECTURE.md`
- Type safety guidelines: `/frontend/docs/TYPE_SAFETY_GUIDELINES.md`
- Technical guide: `/frontend/docs/TECHNICAL_GUIDE.md`
- Issue tracking: `/frontend/docs/ISSUE_TRACKING.md`
- Progress tracking: `/frontend/docs/PROGRESS_TRACKING.md`