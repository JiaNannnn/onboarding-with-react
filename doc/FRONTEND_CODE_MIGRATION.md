# Frontend Code Migration Guide

This document outlines the process for migrating existing frontend code to the new standardized format.

## Migration Steps

### 1. File Extension Standardization

| Current Extension | Action | Target Extension |
|-------------------|--------|------------------|
| `.js` | Convert to TypeScript if component contains JSX | `.tsx` |
| `.js` | Convert to TypeScript if utility/non-component | `.ts` |
| `.jsx` | Convert to TypeScript | `.tsx` |

Script to identify files that need migration:
```bash
# Find all JavaScript files
find ./src -type f -name "*.js" -o -name "*.jsx" > js_files.txt

# Count files by extension
echo "JavaScript files to convert:"
grep -e "\.js$" js_files.txt | wc -l
echo "JSX files to convert:"
grep -e "\.jsx$" js_files.txt | wc -l
```

### 2. Component Structure Migration

For each component:

1. Define interfaces/types at the top of the file
2. Convert class components to functional components
3. Apply proper TypeScript typing to props and state
4. Structure code according to the guidelines in FRONTEND_ENGINEERING.md

Example migration for a simple component:

**Before: Button.js**
```jsx
import React from 'react';
import { Button as MuiButton } from '@mui/material';

function Button(props) {
  const { children, loading, disabled, ...rest } = props;
  
  return (
    <MuiButton
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? 'Loading...' : children}
    </MuiButton>
  );
}

export default Button;
```

**After: Button.tsx**
```tsx
import React from 'react';
import { Button as MuiButton, ButtonProps as MuiButtonProps } from '@mui/material';

export interface ButtonProps extends MuiButtonProps {
  loading?: boolean;
}

const Button: React.FC<ButtonProps> = ({ 
  children, 
  loading = false, 
  disabled, 
  ...rest 
}) => {
  return (
    <MuiButton
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? 'Loading...' : children}
    </MuiButton>
  );
};

export default Button;
```

### 3. Context Migration

For context files:

1. Create proper TypeScript interfaces for context values
2. Implement custom hooks for accessing context
3. Use proper TypeScript generics

**Before: SomeContext.js**
```jsx
import React, { createContext, useState, useContext } from 'react';

const SomeContext = createContext();

export function SomeProvider({ children }) {
  const [value, setValue] = useState('');
  
  return (
    <SomeContext.Provider value={{ value, setValue }}>
      {children}
    </SomeContext.Provider>
  );
}

export function useSomeContext() {
  return useContext(SomeContext);
}
```

**After: SomeContext.tsx**
```tsx
import React, { createContext, useState, useContext } from 'react';

interface SomeContextType {
  value: string;
  setValue: (value: string) => void;
}

const SomeContext = createContext<SomeContextType | null>(null);

export const SomeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [value, setValue] = useState<string>('');
  
  return (
    <SomeContext.Provider value={{ value, setValue }}>
      {children}
    </SomeContext.Provider>
  );
};

export const useSomeContext = (): SomeContextType => {
  const context = useContext(SomeContext);
  if (!context) {
    throw new Error('useSomeContext must be used within a SomeProvider');
  }
  return context;
};

export default SomeContext;
```

### 4. Add Types for API Services

For API service files:

1. Define proper request and response type interfaces
2. Use TypeScript generics for API methods

**Before: someApi.js**
```js
import { request } from './apiClient';

export const fetchData = async (params) => {
  return request({
    url: '/api/data',
    method: 'GET',
    params
  });
};

export const updateData = async (data) => {
  return request({
    url: '/api/data',
    method: 'POST',
    data
  });
};
```

**After: someApi.ts**
```ts
import { request } from './apiClient';

export interface DataItem {
  id: string;
  name: string;
  value: number;
}

export interface FetchDataParams {
  filter?: string;
  limit?: number;
}

export interface FetchDataResponse {
  items: DataItem[];
  total: number;
}

export const fetchData = async (params: FetchDataParams): Promise<FetchDataResponse> => {
  return request<FetchDataResponse>({
    url: '/api/data',
    method: 'GET',
    params
  });
};

export const updateData = async (data: DataItem): Promise<void> => {
  return request<void>({
    url: '/api/data',
    method: 'POST',
    data
  });
};
```

### 5. Migration Tools

You can use these tools to help with the migration:

1. TypeScript compiler's automatic JSX to TSX conversion
2. ESLint to fix formatting issues:
   ```bash
   npx eslint --fix src/
   ```
3. Prettier to format code:
   ```bash
   npx prettier --write "src/**/*.{ts,tsx}"
   ```

## Best Practices During Migration

1. **Migration in Phases**
   - Start with utility functions and simpler components
   - Move on to more complex components
   - Finish with context providers and pages

2. **Testing Each Change**
   - Run TypeScript compiler after each file migration
   - Test components after migration to ensure functionality remains

3. **Code Review**
   - Use pull requests for significant migrations
   - Have another developer review the changes

4. **Documentation**
   - Update component documentation during migration
   - Add JSDoc comments to functions and components

## File Naming Convention Migration

1. **Component Files**
   - Rename component files to use PascalCase
   - Example: `button.js` → `Button.tsx`

2. **Utility Files**
   - Rename utility files to use camelCase
   - Example: `Helper.js` → `helper.ts`

3. **Directory Structure**
   - Organize files into appropriate directories
   - Ensure each component/utility is in the correct location

By following this guide, the frontend codebase can be gradually migrated to the new standardized format with minimal disruption to development activities.