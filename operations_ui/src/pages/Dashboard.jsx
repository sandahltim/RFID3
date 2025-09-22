// Dashboard Page
// Version: 1.0.0
// Date: 2025-09-20

import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Chip
} from '@mui/material';
import {
  Inventory,
  LocalShipping,
  Build,
  TrendingUp,
  CloudQueue,
  Refresh,
  CheckCircle,
  Warning
} from '@mui/icons-material';
import api, { itemsAPI, scanAPI, syncAPI } from '../services/api';
import toast from 'react-hot-toast';

function Dashboard() {
  const [stats, setStats] = useState({
    itemsOut: 0,
    itemsAvailable: 0,
    itemsService: 0,
    todayScans: 0,
    activeContracts: 0,
    pendingReturns: 0
  });
  const [recentActivity, setRecentActivity] = useState([]);
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncStatus, setSyncStatus] = useState(null);

  useEffect(() => {
    loadDashboard();
    const interval = setInterval(loadDashboard, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadDashboard = async () => {
    try {
      // Get sync status
      const syncResponse = await syncAPI.getSyncStatus();
      setSyncStatus(syncResponse.data);

      // Get dashboard statistics from the new endpoint
      const statsResponse = await api.get('/items/dashboard-stats');
      const dashboardStats = statsResponse.data;

      const stats = {
        itemsOut: dashboardStats.items_on_rent,
        itemsAvailable: dashboardStats.items_available,
        itemsService: dashboardStats.items_in_service,
        todayScans: dashboardStats.today_scans,
        activeContracts: dashboardStats.active_contracts,
        pendingReturns: dashboardStats.pending_returns
      };

      setStats(stats);

      // Set real recent activity from API
      if (dashboardStats.recent_activity && dashboardStats.recent_activity.length > 0) {
        setRecentActivity(dashboardStats.recent_activity.slice(0, 4)); // Show top 4
      } else {
        setRecentActivity([]); // No recent activity
      }

      // Remove weather for now - not needed for operations
      setWeather(null);

      setLoading(false);
    } catch (error) {
      toast.error('Failed to load dashboard');
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    loadDashboard();
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case 'checkout': return <LocalShipping color="primary" />;
      case 'return': return <CheckCircle color="success" />;
      case 'service': return <Build color="warning" />;
      default: return <Inventory />;
    }
  };

  const StatCard = ({ title, value, icon, color }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="caption">
              {title}
            </Typography>
            <Typography variant="h4">
              {value}
            </Typography>
          </Box>
          <Avatar sx={{ bgcolor: color }}>
            {icon}
          </Avatar>
        </Box>
      </CardContent>
    </Card>
  );

  if (loading) {
    return <LinearProgress />;
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 2 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4" gutterBottom>
          Operations Dashboard
        </Typography>
        <IconButton onClick={handleRefresh}>
          <Refresh />
        </IconButton>
      </Box>

      <Grid container spacing={3}>
        {/* KPI Cards */}
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="Items Out"
            value={stats.itemsOut}
            icon={<LocalShipping />}
            color="primary.main"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="Available"
            value={stats.itemsAvailable}
            icon={<Inventory />}
            color="success.main"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="In Service"
            value={stats.itemsService}
            icon={<Build />}
            color="warning.main"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="Today's Scans"
            value={stats.todayScans}
            icon={<TrendingUp />}
            color="info.main"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="Active Contracts"
            value={stats.activeContracts}
            icon={<CheckCircle />}
            color="secondary.main"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="Pending Returns"
            value={stats.pendingReturns}
            icon={<Warning />}
            color="error.main"
          />
        </Grid>


        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            {recentActivity.length > 0 ? (
              <List dense>
                {recentActivity.map((activity) => (
                  <ListItem key={activity.id}>
                    <ListItemAvatar>
                      {getActivityIcon(activity.type)}
                    </ListItemAvatar>
                    <ListItemText
                      primary={activity.item}
                      secondary={`${activity.time} - ${activity.user}`}
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No recent activity
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* Sync Status */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Sync Status
            </Typography>
            {syncStatus && (
              <Box>
                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary">
                    Manager DB
                  </Typography>
                  <Typography variant="body1">
                    {syncStatus.manager_db.last_sync
                      ? new Date(syncStatus.manager_db.last_sync).toLocaleString()
                      : 'Never synced'}
                  </Typography>
                  <Chip
                    label={`${syncStatus.manager_db.total_records} records`}
                    size="small"
                    color="primary"
                  />
                </Box>

                <Box>
                  <Typography variant="body2" color="text.secondary">
                    RFIDpro Sync
                  </Typography>
                  <Typography variant="body1">
                    {syncStatus.rfidpro.last_sync || 'Not configured'}
                  </Typography>
                  <Chip
                    label={syncStatus.rfidpro.status === 'manual_only' ? 'Executive Dashboard Control' : syncStatus.rfidpro.status}
                    size="small"
                    variant="outlined"
                    color="info"
                  />
                </Box>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default Dashboard;