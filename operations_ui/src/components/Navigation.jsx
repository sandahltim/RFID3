// Navigation Component
// Version: 1.0.0
// Date: 2025-09-20

import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Box,
  Badge,
  Chip,
  Divider
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard,
  QrCodeScanner,
  Assignment,
  AssignmentReturn,
  Build,
  LocalLaundryService,
  Inventory,
  Sync,
  Settings,
  AttachMoney
} from '@mui/icons-material';

function Navigation({ apiStatus }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const location = useLocation();

  const menuItems = [
    { path: '/', label: 'Dashboard', icon: <Dashboard /> },
    { path: '/inventory', label: 'Rental Inventory', icon: <Inventory /> },
    { path: '/contracts', label: 'Open Contracts', icon: <Assignment /> },
    { path: '/service', label: 'Service', icon: <Build /> },
    { path: '/laundry', label: 'Laundry', icon: <LocalLaundryService /> },
    { path: '/resale', label: 'Resale Items', icon: <AttachMoney /> },
    { path: '/scan', label: 'Scanning', icon: <QrCodeScanner /> },
    { path: '/items', label: 'Item Search', icon: <Inventory /> },
    { path: '/sync', label: 'Sync & Settings', icon: <Settings /> },
  ];

  const getStatusColor = () => {
    switch (apiStatus) {
      case 'online': return 'success';
      case 'offline': return 'error';
      case 'checking': return 'warning';
      default: return 'default';
    }
  };

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => setDrawerOpen(true)}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>

          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            RFID Operations
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip
              label={apiStatus.toUpperCase()}
              color={getStatusColor()}
              size="small"
            />

            {/* Store indicator - will be dynamic */}
            <Chip
              label="Store: 3607"
              variant="outlined"
              color="primary"
              size="small"
            />
          </Box>
        </Toolbar>
      </AppBar>

      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        <Box
          sx={{ width: 250 }}
          role="presentation"
          onClick={() => setDrawerOpen(false)}
        >
          <Box sx={{ p: 2 }}>
            <Typography variant="h6">
              Operations Menu
            </Typography>
            <Typography variant="caption" color="text.secondary">
              v1.0.0 - Chainway SR160
            </Typography>
          </Box>

          <Divider />

          <List>
            {menuItems.map((item) => (
              <ListItem
                button
                key={item.path}
                component={Link}
                to={item.path}
                selected={location.pathname === item.path}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItem>
            ))}
          </List>

          <Divider />

          <Box sx={{ p: 2, position: 'absolute', bottom: 0 }}>
            <Typography variant="caption" display="block">
              Scanner: {window.navigator.userAgent.includes('Chainway') ? 'Connected' : 'Not Connected'}
            </Typography>
            <Typography variant="caption" display="block" color="text.secondary">
              User: Operator
            </Typography>
          </Box>
        </Box>
      </Drawer>
    </>
  );
}

export default Navigation;