// Main App Component
// Version: 1.0.0
// Date: 2025-09-20

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Toaster } from 'react-hot-toast';

// Pages
import Dashboard from './pages/Dashboard';
import ScanPage from './pages/ScanPage';
import ItemsPage from './pages/ItemsPage';
import ContractsPage from './pages/ContractsPage';
import RentalInventory from './pages/RentalInventory';
import ServicePage from './pages/ServicePage';
import LaundryPage from './pages/LaundryPage';
import ResalePage from './pages/ResalePage';

// Components
import Navigation from './components/Navigation';
import { healthAPI } from './services/api';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    success: {
      main: '#2e7d32',
    },
  },
});

function App() {
  const [apiStatus, setApiStatus] = useState('checking');

  useEffect(() => {
    checkAPI();
    const interval = setInterval(checkAPI, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const checkAPI = async () => {
    try {
      const response = await healthAPI.check();
      setApiStatus(response.data.status === 'healthy' ? 'online' : 'error');
    } catch (error) {
      setApiStatus('offline');
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Navigation apiStatus={apiStatus} />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/inventory" element={<RentalInventory />} />
          <Route path="/contracts" element={<ContractsPage />} />
          <Route path="/service" element={<ServicePage />} />
          <Route path="/laundry" element={<LaundryPage />} />
          <Route path="/resale" element={<ResalePage />} />
          <Route path="/scan" element={<ScanPage />} />
          <Route path="/items" element={<ItemsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
      <Toaster
        position="bottom-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
        }}
      />
    </ThemeProvider>
  );
}

export default App;