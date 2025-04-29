# Frontend Engineering Documentation

## Overview

This document details the frontend implementation of the BMS to EnOS Onboarding Tool. The frontend is built using React with TypeScript, utilizing Material UI for components and styling, and the Context API for state management.

## Architecture

### Component Structure

The frontend follows a feature-based organization:

```
frontend/
├── components/          # Reusable UI components
│   ├── common/          # Generic UI elements
│   └── feature/         # Feature-specific components
├── context/             # Global state management
├── hooks/               # Custom React hooks
├── pages/               # Main application pages
├── api/                 # API integration services
├── types/               # TypeScript type definitions
└── utils/               # Utility functions
```

### Key Pages

1. **Dashboard** - Overview and entry point to workflows
2. **FetchPoints** - Discovery and retrieval of BMS points
3. **GroupPoints** - Organization and grouping of points
4. **MappingPoints** - Mapping BMS points to EnOS points
5. **SavedMappings** - Management of saved mapping configurations

### State Management

The application uses React Context API for global state management:

- **AppContext** - Global application state
- **PointsContext** - State related to BMS points
- **GroupingContext** - State related to point grouping
- **MappingContext** - State related to point mappings

## Implementation Standards

### File Naming & Organization

1. **File Extensions**
   - Use `.tsx` for files containing JSX/TSX (React components)
   - Use `.ts` for TypeScript files without JSX/TSX
   - Avoid using `.js` and `.jsx` extensions for consistency

2. **File Naming Conventions**
   - Use `PascalCase` for component files (e.g., `GroupPoints.tsx`, `DataTable.tsx`)
   - Use `camelCase` for non-component files (e.g., `apiClient.ts`, `useToast.ts`)
   - Use `index.tsx` or `index.ts` for barrel files that export multiple components

3. **Directory Structure**
   - Each feature area should have its own directory
   - Common components should be placed in `components/common/`
   - Feature-specific components should be in `components/feature/`
   - All pages should be placed in the `pages/` directory

### Coding Style

1. **Component Structure**
   - Define interfaces/types at the top of the file
   - Place helper functions and hooks next
   - Main component implementation follows
   - Export statements at the bottom

2. **Component Format**
   ```tsx
   import React, { useState, useEffect } from 'react';
   import { SomeComponent } from '../components';
   
   // Define props interface
   interface MyComponentProps {
     title: string;
     onAction?: () => void;
   }
   
   // Define any helper functions or custom hooks
   const useHelperHook = () => {
     // ...implementation
   };
   
   // Main component implementation
   const MyComponent: React.FC<MyComponentProps> = ({ title, onAction }) => {
     // State and hooks
     const [state, setState] = useState<string>('');
     
     // Effects
     useEffect(() => {
       // ...side effects
     }, []);
     
     // Event handlers
     const handleClick = () => {
       if (onAction) onAction();
     };
     
     // Render methods
     const renderContent = () => {
       return (
         <div>{state}</div>
       );
     };
     
     // Component return
     return (
       <div>
         <h2>{title}</h2>
         <button onClick={handleClick}>Click me</button>
         {renderContent()}
       </div>
     );
   };
   
   export default MyComponent;
   ```

3. **Imports Order**
   - React imports first
   - External library imports
   - Internal absolute imports
   - Internal relative imports
   - CSS/SCSS imports last

4. **Naming Conventions**
   - `PascalCase` for components and interfaces
   - `camelCase` for variables, functions, and methods
   - `UPPER_SNAKE_CASE` for constants
   - Prefix event handlers with `handle` (e.g., `handleClick`)
   - Prefix render methods with `render` (e.g., `renderHeader`)
   - Prefix boolean variables with `is`, `has`, or `should` (e.g., `isLoading`)

5. **TypeScript Usage**
   - Always define prop types with interfaces
   - Use type annotations for all function parameters and return types
   - Avoid using `any` whenever possible
   - Use TypeScript generics with hooks, e.g., `useState<string>('')`
   - Create dedicated type files for complex or shared types

### Component Guidelines

1. **Functional Components**
   - Use functional components with hooks
   - Implement proper separation of concerns
   - Extract reusable logic to custom hooks
   - Use React.memo for performance optimization when appropriate

2. **Type Safety**
   - Define interfaces for component props
   - Use TypeScript for type checking
   - Document complex type structures
   - Avoid implicit any types

3. **Performance Optimization**
   - Implement memoization where appropriate
   - Avoid unnecessary re-renders
   - Use virtualization for large lists
   - Implement code splitting for large components

### State Management

1. **Context Structure**
   - Separate contexts by domain (points, mapping, etc.)
   - Provide clear type definitions for context values
   - Implement custom hooks for accessing context
   - Use reducer pattern for complex state logic

2. **Example Context Pattern**
   ```tsx
   // context/MyContext.tsx
   import React, { createContext, useContext, useState } from 'react';

   // Define context type
   interface MyContextType {
     value: string;
     setValue: (value: string) => void;
   }

   // Create context
   const MyContext = createContext<MyContextType | null>(null);

   // Create provider component
   export const MyProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
     const [value, setValue] = useState<string>('');
     
     return (
       <MyContext.Provider value={{ value, setValue }}>
         {children}
       </MyContext.Provider>
     );
   };

   // Create custom hook
   export const useMyContext = () => {
     const context = useContext(MyContext);
     if (!context) {
       throw new Error('useMyContext must be used within a MyProvider');
     }
     return context;
   };

   export default MyContext;
   ```

### API Integration

The frontend communicates with the backend through a centralized API service:

```typescript
// api/myApi.ts
import { request } from './apiClient';
import { MyResponse, MyRequest } from '../types';

export const fetchData = async (params: MyRequest): Promise<MyResponse> => {
  return request<MyResponse>({
    url: '/api/v1/data',
    method: 'GET',
    params
  });
};

export const updateData = async (data: MyRequest): Promise<void> => {
  return request<void>({
    url: '/api/v1/data',
    method: 'POST',
    data
  });
};
```

## UI Component Examples

### Common Component Example

```tsx
// components/common/Button.tsx
import React from 'react';
import { Button as MuiButton, ButtonProps as MuiButtonProps } from '@mui/material';

export interface ButtonProps extends MuiButtonProps {
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({ 
  children, 
  isLoading = false, 
  disabled, 
  ...rest 
}) => {
  return (
    <MuiButton
      disabled={disabled || isLoading}
      {...rest}
    >
      {isLoading ? 'Loading...' : children}
    </MuiButton>
  );
};

export default Button;
```

### Feature Component Example

```tsx
// components/feature/PointCard.tsx
import React from 'react';
import { Card, CardContent, Typography, Chip } from '@mui/material';
import { BMSPoint } from '../../types';

interface PointCardProps {
  point: BMSPoint;
  onSelect: (point: BMSPoint) => void;
  isSelected: boolean;
}

export const PointCard: React.FC<PointCardProps> = ({ 
  point, 
  onSelect, 
  isSelected 
}) => {
  return (
    <Card 
      variant="outlined" 
      sx={{ 
        border: isSelected ? '2px solid primary.main' : '1px solid divider',
        mb: 2
      }}
      onClick={() => onSelect(point)}
    >
      <CardContent>
        <Typography variant="h6">{point.name}</Typography>
        <Typography color="textSecondary">{point.pointType}</Typography>
        <Typography variant="body2">{point.description || 'No description'}</Typography>
        {point.tags && (
          <Box mt={1}>
            {point.tags.map((tag, index) => (
              <Chip key={index} label={tag} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default PointCard;
```

## Best Practices & Coding Standards

1. **Component Structure**
   - One component per file
   - Props interface defined above component
   - Props destructured in function parameters
   - Separate logic from presentation when possible

2. **Naming Conventions**
   - PascalCase for components and interfaces
   - camelCase for variables and functions
   - Descriptive, clear names reflecting purpose

3. **File Organization**
   - Related files grouped in directories
   - Index files for clean exports
   - Consistent import ordering

4. **Code Formatting**
   - Use consistent indentation (2 spaces)
   - Use semicolons at the end of statements
   - Use single quotes for strings
   - Use trailing commas in multi-line objects and arrays
   - Maximum line length of 100 characters

5. **Error Handling**
   - Implement proper error boundaries
   - Handle API errors gracefully
   - Provide user-friendly error messages
   - Log errors for debugging

6. **Testing**
   - Write unit tests for components
   - Write integration tests for features
   - Use meaningful test descriptions
   - Mock API calls and external dependencies

## Performance Considerations

1. **Large Dataset Handling**
   - Implement virtualization for large lists
   - Paginate API requests where possible
   - Use memoization for expensive calculations

2. **Render Optimization**
   - Avoid unnecessary re-renders with React.memo
   - Use useCallback for event handlers
   - Implement lazy loading for components

3. **Network Optimization**
   - Implement request debouncing
   - Cache results where appropriate
   - Show loading states during network operations

## Code Review Checklist

When submitting or reviewing code, ensure it meets these standards:

1. **Functionality**
   - Code works as expected
   - Edge cases are handled
   - No console errors

2. **Code Quality**
   - Follows naming conventions
   - Proper TypeScript typing
   - No unnecessary code duplication
   - Clean and readable

3. **Performance**
   - No obvious performance issues
   - Proper memoization where needed
   - No memory leaks

4. **Accessibility**
   - Semantic HTML
   - Proper ARIA attributes
   - Keyboard navigation support

5. **Responsiveness**
   - Works on different screen sizes
   - Mobile-friendly UI

This documentation is maintained by the Frontend Engineer and should be updated as the implementation evolves.