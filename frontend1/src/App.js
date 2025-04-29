import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { SnackbarProvider } from 'notistack';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import FetchPoints from './pages/FetchPoints';
import GroupPoints from './pages/GroupPoints';
import MappingPoints from './pages/MappingPoints';
import SavedMappings from './pages/SavedMappings';

// Create a dark theme
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <SnackbarProvider maxSnack={3}>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/fetch-points" element={<FetchPoints />} />
            <Route path="/group-points" element={<GroupPoints />} />
            <Route path="/mapping-points" element={<MappingPoints />} />
            <Route path="/saved-mappings" element={<SavedMappings />} />
          </Routes>
        </Layout>
      </SnackbarProvider>
    </ThemeProvider>
  );
}

export default App;
