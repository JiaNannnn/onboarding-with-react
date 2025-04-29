# Type Safety Guidelines

This document outlines our approach to maintaining strict type safety throughout the frontend codebase.

## Core Principles

1. **No `any` Type Usage**
2. **Explicit Typing for All Functions and Components**
3. **Comprehensive Error Handling**
4. **Task-By-Task Implementation with Type-First Approach**

## Type Safety Rules

### 1. Avoid Using `any`

```typescript
// ❌ BAD
function processData(data: any) {
  return data.value * 2;
}

// ✅ GOOD
function processData(data: { value: number }) {
  return data.value * 2;
}
```

When type is not known, use `unknown` with type guards:

```typescript
// ✅ GOOD
function processUnknownData(data: unknown) {
  if (typeof data === 'object' && data !== null && 'value' in data) {
    const typedData = data as { value: number };
    return typedData.value * 2;
  }
  throw new Error('Invalid data format');
}
```

### 2. Use Type Guards

Create custom type guards to check types:

```typescript
// ✅ GOOD
interface User {
  id: string;
  name: string;
  role: 'admin' | 'user';
}

function isUser(value: unknown): value is User {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'name' in value &&
    'role' in value &&
    typeof (value as User).id === 'string' &&
    typeof (value as User).name === 'string' &&
    ((value as User).role === 'admin' || (value as User).role === 'user')
  );
}

function processUser(data: unknown) {
  if (isUser(data)) {
    // TypeScript knows data is User now
    console.log(data.name);
  }
}
```

### 3. Type Component Props Explicitly

Always define a props interface for React components:

```typescript
// ✅ GOOD
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
  return (
    <button 
      className={`button button--${variant}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};
```

### 4. Type API Requests and Responses

```typescript
// ✅ GOOD
interface FetchPointsRequest {
  assetId: string;
  deviceId?: string;
}

interface FetchPointsResponse {
  points: Point[];
  totalCount: number;
}

async function fetchPoints(request: FetchPointsRequest): Promise<ApiResponse<FetchPointsResponse>> {
  return request<FetchPointsResponse>({
    url: '/points/fetch',
    method: 'POST',
    data: request
  });
}
```

### 5. Use Discriminated Unions for State

```typescript
// ✅ GOOD
type FetchState<T> = 
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: string };

function useFetchData<T>(url: string) {
  const [state, setState] = useState<FetchState<T>>({ status: 'idle' });
  
  useEffect(() => {
    setState({ status: 'loading' });
    
    fetch(url)
      .then(res => res.json())
      .then(data => setState({ status: 'success', data }))
      .catch(error => setState({ 
        status: 'error', 
        error: error instanceof Error ? error.message : 'Unknown error' 
      }));
  }, [url]);
  
  return state;
}

// Using the hook with type safety
const pointsState = useFetchData<Point[]>('/api/points');

// Type-safe state handling
if (pointsState.status === 'loading') {
  return <div>Loading...</div>;
} else if (pointsState.status === 'error') {
  return <div>Error: {pointsState.error}</div>;
} else if (pointsState.status === 'success') {
  return <div>{pointsState.data.length} points found</div>;
}
```

### 6. Type Form Events Properly

```typescript
// ✅ GOOD
const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  setName(e.target.value);
};

const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault();
  // Form submission logic
};
```

### 7. Type Asynchronous Code

```typescript
// ✅ GOOD
async function loadData(): Promise<void> {
  try {
    const response = await fetch('/api/data');
    
    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}`);
    }
    
    const data: ApiResponse<DataType> = await response.json();
    // Process data
  } catch (error: unknown) {
    if (error instanceof Error) {
      console.error(error.message);
    } else {
      console.error(String(error));
    }
  }
}
```

## Task-By-Task Implementation Approach

1. **Start with Types**
   - Define all interfaces and types needed for the task first
   - Document type constraints and relationships

2. **Implement with Type Safety in Mind**
   - Write type-safe code from the beginning
   - Use type guards and assertions where needed
   - Handle all possible states explicitly

3. **Test Type Safety**
   - Verify that TypeScript raises appropriate errors for incorrect usage
   - Ensure edge cases are handled

4. **Document Type Requirements**
   - Add JSDoc comments to explain complex types
   - Document expected formats and constraints

## Common Type Safety Patterns

### Pattern 1: Type-Safe Context Creation

```typescript
interface AppContextType {
  user: User | null;
  setUser: (user: User | null) => void;
}

const AppContext = createContext<AppContextType | null>(null);

export function useAppContext(): AppContextType {
  const context = useContext(AppContext);
  if (context === null) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
}
```

### Pattern 2: Generic Components

```typescript
interface SelectProps<T> {
  options: T[];
  value: T | null;
  onChange: (value: T) => void;
  getLabel: (option: T) => string;
  getValue: (option: T) => string;
}

function Select<T>({
  options,
  value,
  onChange,
  getLabel,
  getValue
}: SelectProps<T>) {
  // Implementation
}
```

### Pattern 3: Type-Safe API Responses

```typescript
async function fetchData<TResponse>(url: string): Promise<TResponse> {
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`HTTP error ${response.status}`);
  }
  
  const data = await response.json();
  return data as TResponse;
}
```

## Review Checklist

Before completing a task, ensure:

1. No `any` types are used
2. All props have explicit interfaces
3. All functions have return types
4. Edge cases are handled with proper types
5. API requests and responses are properly typed
6. State transitions are fully typed (especially for complex states)
7. Error handling is comprehensive and typed 