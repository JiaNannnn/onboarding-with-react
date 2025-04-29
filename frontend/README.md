# BMS to EnOS API Migration Tools

This repository contains the API migration tools for the Building Management System (BMS) to EnOS platform onboarding tool. It provides utilities for monitoring and migrating from deprecated API functions to the new architecture.

## Migration Tools

- **API Analytics**: Dashboard for monitoring deprecated API usage
- **Migration Assistant**: Tool for automated code refactoring

## Technology Stack

- React 18
- TypeScript 4.9+
- Axios for API requests
- React Router for navigation
- Zod for runtime type validation
- date-fns for date formatting

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm 8+ or yarn 1.22+

### Installation

1. Clone the repository
2. Install dependencies:

```bash
npm install
# or
yarn install
```

3. Start the development server:

```bash
npm start
# or
yarn start
```

The application will be available at http://localhost:3000.

### Environment Variables

Create a `.env` file in the project root with the following variables:

```
REACT_APP_API_BASE_URL=http://localhost:5000/api
```

Adjust the URL as needed for your backend server.

## Project Structure

```
frontend/
├── src/
│   ├── api/          # API integration services
│   ├── components/   # UI components (simplified)
│   ├── pages/        # Only migration tool pages
│   │   └── DevTools/   # API Analytics and Migration Assistant
│   ├── router/       # Application routing
│   ├── types/        # TypeScript type definitions
│   └── utils/        # Utility functions
├── public/           # Static assets
├── .env              # Environment variables
├── package.json      # Project dependencies
└── tsconfig.json     # TypeScript configuration
```

## Migration Guide

The API migration process involves:

1. Identifying usage of deprecated functions using API Analytics
2. Refactoring code with the Migration Assistant
3. Following the migration patterns described in the documentation

For detailed migration guidelines, see the `/docs/MIGRATION_GUIDE.md` file.

## Project Commands

- `npm start`: Start the development server
- `npm build`: Build the application for production
- `npm test`: Run the test suite
- `npm run typecheck`: Verify TypeScript types
- `npm run lint`: Lint the codebase
- `npm run lint:fix`: Fix linting issues
- `npm run format`: Format code with Prettier

## License

This project is licensed under the MIT License.