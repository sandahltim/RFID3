import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Collapse,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextField,
  Chip,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Badge,
  Tooltip
} from '@mui/material';
import {
  KeyboardArrowDown,
  KeyboardArrowRight,
  Print,
  Refresh,
  FilterList,
  Category,
  Inventory,
  Build,
  LocalLaundryService,
  CheckCircle,
  Warning
} from '@mui/icons-material';
import { itemsAPI } from '../services/api';
import toast from 'react-hot-toast';

const RentalInventory = () => {
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState([]);
  const [expandedCategories, setExpandedCategories] = useState({});
  const [expandedSubcategories, setExpandedSubcategories] = useState({});
  const [expandedCommonNames, setExpandedCommonNames] = useState({});
  const [filters, setFilters] = useState({
    store: '',
    inventoryType: 'all',
    status: ''
  });
  const [stats, setStats] = useState({
    totalItems: 0,
    available: 0,
    onRent: 0,
    service: 0,
    laundry: 0
  });

  // Load categories with aggregated counts
  useEffect(() => {
    loadCategories();
  }, [filters]);

  const loadCategories = async () => {
    setLoading(true);
    try {
      const response = await itemsAPI.getCategories(filters);
      setCategories(response.data);
      calculateStats(response.data);
    } catch (error) {
      toast.error('Failed to load inventory categories');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (data) => {
    const newStats = {
      totalItems: 0,
      available: 0,
      onRent: 0,
      service: 0,
      laundry: 0
    };

    data.forEach(category => {
      newStats.totalItems += category.item_count || 0;
      newStats.available += category.available_count || 0;
      newStats.onRent += category.rented_count || 0;
      newStats.service += category.service_count || 0;
      newStats.laundry += category.laundry_count || 0;
    });

    setStats(newStats);
  };

  const toggleCategory = async (categoryId) => {
    const isExpanded = expandedCategories[categoryId];

    if (!isExpanded) {
      // Load subcategories when expanding
      try {
        const response = await itemsAPI.getSubcategories(categoryId, filters);
        setCategories(prev => prev.map(cat =>
          cat.id === categoryId
            ? { ...cat, subcategories: response.data }
            : cat
        ));
      } catch (error) {
        toast.error('Failed to load subcategories');
      }
    }

    setExpandedCategories(prev => ({
      ...prev,
      [categoryId]: !isExpanded
    }));
  };

  const toggleSubcategory = async (categoryId, subcategoryId) => {
    const key = `${categoryId}-${subcategoryId}`;
    const isExpanded = expandedSubcategories[key];

    if (!isExpanded) {
      // Load common names when expanding
      try {
        const response = await itemsAPI.getCommonNames(categoryId, subcategoryId, filters);
        setCategories(prev => prev.map(cat => {
          if (cat.id === categoryId) {
            return {
              ...cat,
              subcategories: cat.subcategories.map(sub =>
                sub.id === subcategoryId
                  ? { ...sub, commonNames: response.data }
                  : sub
              )
            };
          }
          return cat;
        }));
      } catch (error) {
        toast.error('Failed to load items');
      }
    }

    setExpandedSubcategories(prev => ({
      ...prev,
      [key]: !isExpanded
    }));
  };

  const toggleCommonName = async (categoryId, subcategoryId, commonName) => {
    const key = `${categoryId}-${subcategoryId}-${commonName}`;
    const isExpanded = expandedCommonNames[key];

    if (!isExpanded) {
      // Load individual items when expanding
      try {
        const response = await itemsAPI.getItems({
          rental_class: commonName,
          ...filters
        });

        setCategories(prev => prev.map(cat => {
          if (cat.id === categoryId) {
            return {
              ...cat,
              subcategories: cat.subcategories.map(sub => {
                if (sub.id === subcategoryId) {
                  return {
                    ...sub,
                    commonNames: sub.commonNames.map(cn =>
                      cn.name === commonName
                        ? { ...cn, items: response.data }
                        : cn
                    )
                  };
                }
                return sub;
              })
            };
          }
          return cat;
        }));
      } catch (error) {
        toast.error('Failed to load item details');
      }
    }

    setExpandedCommonNames(prev => ({
      ...prev,
      [key]: !isExpanded
    }));
  };

  const updateItemStatus = async (itemId, newStatus) => {
    try {
      await itemsAPI.updateStatus(itemId, { status: newStatus });
      toast.success('Status updated');
      // Refresh the specific item
      loadCategories();
    } catch (error) {
      toast.error('Failed to update status');
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'available': 'success',
      'rented': 'warning',
      'service': 'error',
      'laundry': 'info',
      'missing': 'error'
    };
    return colors[status] || 'default';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Rental Inventory</Typography>
        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={loadCategories}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Total Items</Typography>
              <Typography variant="h5">{stats.totalItems}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Available</Typography>
              <Typography variant="h5" color="success.main">{stats.available}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>On Rent</Typography>
              <Typography variant="h5" color="warning.main">{stats.onRent}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Service/Laundry</Typography>
              <Typography variant="h5" color="error.main">{stats.service + stats.laundry}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Store Location</InputLabel>
              <Select
                value={filters.store}
                onChange={(e) => setFilters(prev => ({ ...prev, store: e.target.value }))}
                label="Store Location"
              >
                <MenuItem value="">All Stores</MenuItem>
                <MenuItem value="001">Brooklyn Park</MenuItem>
                <MenuItem value="002">Wayzata</MenuItem>
                <MenuItem value="003">Fridley</MenuItem>
                <MenuItem value="004">Elk River</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Inventory Type</InputLabel>
              <Select
                value={filters.inventoryType}
                onChange={(e) => setFilters(prev => ({ ...prev, inventoryType: e.target.value }))}
                label="Inventory Type"
              >
                <MenuItem value="all">All Types</MenuItem>
                <MenuItem value="RFID">RFID Tagged</MenuItem>
                <MenuItem value="QR">QR Code</MenuItem>
                <MenuItem value="Serialized">Serialized</MenuItem>
                <MenuItem value="Bulk">Bulk Items</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Status Filter</InputLabel>
              <Select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                label="Status Filter"
              >
                <MenuItem value="">All Status</MenuItem>
                <MenuItem value="available">Available</MenuItem>
                <MenuItem value="rented">On Rent</MenuItem>
                <MenuItem value="service">In Service</MenuItem>
                <MenuItem value="laundry">In Laundry</MenuItem>
                <MenuItem value="missing">Missing</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Inventory Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell width={40}></TableCell>
              <TableCell>Category / Item</TableCell>
              <TableCell align="right">Total</TableCell>
              <TableCell align="right">Available</TableCell>
              <TableCell align="right">On Rent</TableCell>
              <TableCell align="right">Service</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : categories.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Alert severity="info">No inventory items found</Alert>
                </TableCell>
              </TableRow>
            ) : (
              categories.map((category) => (
                <React.Fragment key={category.id}>
                  {/* Category Row */}
                  <TableRow hover>
                    <TableCell>
                      <IconButton size="small" onClick={() => toggleCategory(category.id)}>
                        {expandedCategories[category.id] ? <KeyboardArrowDown /> : <KeyboardArrowRight />}
                      </IconButton>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Category sx={{ mr: 1 }} />
                        <Typography variant="subtitle1" fontWeight="bold">
                          {category.name}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Badge badgeContent={category.item_count} color="primary" max={999}>
                        <Inventory />
                      </Badge>
                    </TableCell>
                    <TableCell align="right">
                      <Chip label={category.available_count} color="success" size="small" />
                    </TableCell>
                    <TableCell align="right">
                      <Chip label={category.rented_count} color="warning" size="small" />
                    </TableCell>
                    <TableCell align="right">
                      <Chip label={category.service_count} color="error" size="small" />
                    </TableCell>
                    <TableCell>
                      <Tooltip title="Print Category">
                        <IconButton size="small">
                          <Print />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>

                  {/* Subcategory Rows */}
                  <TableRow>
                    <TableCell colSpan={7} sx={{ p: 0 }}>
                      <Collapse in={expandedCategories[category.id]} timeout="auto" unmountOnExit>
                        <Table size="small">
                          <TableBody>
                            {category.subcategories?.map((subcat) => (
                              <React.Fragment key={subcat.id}>
                                <TableRow>
                                  <TableCell width={80}>
                                    <IconButton
                                      size="small"
                                      sx={{ ml: 4 }}
                                      onClick={() => toggleSubcategory(category.id, subcat.id)}
                                    >
                                      {expandedSubcategories[`${category.id}-${subcat.id}`]
                                        ? <KeyboardArrowDown />
                                        : <KeyboardArrowRight />}
                                    </IconButton>
                                  </TableCell>
                                  <TableCell>
                                    <Typography variant="body2" sx={{ ml: 2 }}>
                                      {subcat.name}
                                    </Typography>
                                  </TableCell>
                                  <TableCell align="right">{subcat.item_count}</TableCell>
                                  <TableCell align="right">
                                    <Chip label={subcat.available_count} size="small" variant="outlined" />
                                  </TableCell>
                                  <TableCell align="right">
                                    <Chip label={subcat.rented_count} size="small" variant="outlined" />
                                  </TableCell>
                                  <TableCell align="right">
                                    <Chip label={subcat.service_count} size="small" variant="outlined" />
                                  </TableCell>
                                  <TableCell></TableCell>
                                </TableRow>

                                {/* Common Names & Items */}
                                <TableRow>
                                  <TableCell colSpan={7} sx={{ p: 0 }}>
                                    <Collapse
                                      in={expandedSubcategories[`${category.id}-${subcat.id}`]}
                                      timeout="auto"
                                      unmountOnExit
                                    >
                                      {subcat.commonNames?.map((cn) => (
                                        <Box key={cn.name} sx={{ ml: 8, p: 1 }}>
                                          <Box
                                            sx={{
                                              display: 'flex',
                                              alignItems: 'center',
                                              cursor: 'pointer',
                                              '&:hover': { bgcolor: 'action.hover' },
                                              p: 1
                                            }}
                                            onClick={() => toggleCommonName(category.id, subcat.id, cn.name)}
                                          >
                                            <IconButton size="small">
                                              {expandedCommonNames[`${category.id}-${subcat.id}-${cn.name}`]
                                                ? <KeyboardArrowDown />
                                                : <KeyboardArrowRight />}
                                            </IconButton>
                                            <Typography variant="body2" sx={{ flex: 1 }}>
                                              {cn.name}
                                            </Typography>
                                            <Badge badgeContent={cn.count} color="primary">
                                              <Inventory fontSize="small" />
                                            </Badge>
                                          </Box>

                                          {/* Individual Items */}
                                          <Collapse
                                            in={expandedCommonNames[`${category.id}-${subcat.id}-${cn.name}`]}
                                            timeout="auto"
                                            unmountOnExit
                                          >
                                            <Box sx={{ ml: 4, mt: 1 }}>
                                              {cn.items?.map((item) => (
                                                <Box
                                                  key={item.tag_id}
                                                  sx={{
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: 2,
                                                    p: 1,
                                                    borderBottom: '1px solid',
                                                    borderColor: 'divider'
                                                  }}
                                                >
                                                  <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                                                    {item.tag_id}
                                                  </Typography>
                                                  <Chip
                                                    label={item.identifier_type}
                                                    size="small"
                                                    variant="outlined"
                                                  />
                                                  <Select
                                                    size="small"
                                                    value={item.status}
                                                    onChange={(e) => updateItemStatus(item.tag_id, e.target.value)}
                                                    sx={{ minWidth: 120 }}
                                                  >
                                                    <MenuItem value="available">Available</MenuItem>
                                                    <MenuItem value="rented">On Rent</MenuItem>
                                                    <MenuItem value="service">Service</MenuItem>
                                                    <MenuItem value="laundry">Laundry</MenuItem>
                                                    <MenuItem value="missing">Missing</MenuItem>
                                                  </Select>
                                                  <TextField
                                                    size="small"
                                                    placeholder="Bin location"
                                                    value={item.bin_location || ''}
                                                    sx={{ width: 100 }}
                                                  />
                                                  <Typography variant="caption" color="textSecondary">
                                                    Last: {item.last_contract_num || 'N/A'}
                                                  </Typography>
                                                </Box>
                                              ))}
                                            </Box>
                                          </Collapse>
                                        </Box>
                                      ))}
                                    </Collapse>
                                  </TableCell>
                                </TableRow>
                              </React.Fragment>
                            ))}
                          </TableBody>
                        </Table>
                      </Collapse>
                    </TableCell>
                  </TableRow>
                </React.Fragment>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default RentalInventory;