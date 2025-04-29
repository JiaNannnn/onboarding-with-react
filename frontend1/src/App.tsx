import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { SnackbarProvider } from 'notistack';

// Custom components
import Layout from './components/layout/Layout';
import ErrorBoundary from './components/ui/ErrorBoundary';
import Loading from './components/ui/Loading';

// Context providers
import { AppContextProvider } from './store/AppContext';

// Pages
import Dashboard from './pages/Dashboard';

// Lazy-loaded pages
const FetchPoints = React.lazy(() => import('./pages/FetchPoints'));
const GroupPoints = React.lazy(() => import('./pages/GroupPoints'));
const MappingPoints = React.lazy(() => import('./pages/MappingPoints'));
const SavedMappings = React.lazy(() => import('./pages/SavedMappings'));

// Theme configuration
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
  },
});

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <SnackbarProvider 
          maxSnack={3} 
          anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
        >
          <AppContextProvider>
            <BrowserRouter>
              <Layout>
                <Suspense fallback={<Loading />}>
                  <Routes>
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/fetch-points" element={<FetchPoints />} />
                    <Route path="/group-points" element={<GroupPoints />} />
                    <Route path="/mapping-points" element={<MappingPoints />} />
                    <Route path="/saved-mappings" element={<SavedMappings />} />
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                  </Routes>
                </Suspense>
              </Layout>
            </BrowserRouter>
          </AppContextProvider>
        </SnackbarProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
};

export default App;
