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
  Button,
  Chip,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Checkbox,
  Grid,
  Card,
  CardContent,
  CircularProgress
} from '@mui/material';
import {
  AttachMoney,
  Download,
  Print,
  Refresh,
  CheckBox,
  CheckBoxOutlineBlank
} from '@mui/icons-material';
import { itemsAPI } from '../services/api';
import toast from 'react-hot-toast';

const ResalePage = () => {
  const [loading, setLoading] = useState(false);
  const [resaleItems, setResaleItems] = useState([]);
  const [selectedItems, setSelectedItems] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedSubcategory, setSelectedSubcategory] = useState('');
  const [categories, setCategories] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const [confirmDialog, setConfirmDialog] = useState(false);
  const [stats, setStats] = useState({
    totalResale: 0,
    pendingSale: 0,
    sold: 0,
    totalValue: 0
  });

  useEffect(() => {
    loadCategories();
    loadResaleItems();
  }, []);

  useEffect(() => {
    if (selectedCategory) {
      loadSubcategories(selectedCategory);
    }
  }, [selectedCategory]);

  useEffect(() => {
    if (selectedSubcategory) {
      loadResaleItems();
    }
  }, [selectedSubcategory]);

  const loadCategories = async () => {
    try {
      const response = await itemsAPI.getCategories({ resale_only: true });
      setCategories(response.data);
    } catch (error) {
      console.error('Failed to load categories', error);
    }
  };

  const loadSubcategories = async (categoryId) => {
    try {
      const response = await itemsAPI.getSubcategories(categoryId, { resale_only: true });
      setSubcategories(response.data);
    } catch (error) {
      console.error('Failed to load subcategories', error);
    }
  };

  const loadResaleItems = async () => {
    setLoading(true);
    try {
      const params = {
        status: 'resale',
        category: selectedCategory,
        subcategory: selectedSubcategory
      };
      const response = await itemsAPI.getResaleItems(params);
      setResaleItems(response.data);
      calculateStats(response.data);
    } catch (error) {
      toast.error('Failed to load resale items');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (items) => {
    const stats = {
      totalResale: items.length,
      pendingSale: items.filter(i => i.status === 'resale').length,
      sold: items.filter(i => i.status === 'sold').length,
      totalValue: items.reduce((sum, i) => sum + (i.resale_price || 0), 0)
    };
    setStats(stats);
  };

  const handleSelectItem = (itemId) => {
    setSelectedItems(prev => {
      if (prev.includes(itemId)) {
        return prev.filter(id => id !== itemId);
      }
      return [...prev, itemId];
    });
  };

  const handleSelectAll = () => {
    if (selectedItems.length === resaleItems.length) {
      setSelectedItems([]);
    } else {
      setSelectedItems(resaleItems.map(item => item.tag_id));
    }
  };

  const handleMarkAsSold = async () => {
    if (selectedItems.length === 0) {
      toast.error('No items selected');
      return;
    }
    setConfirmDialog(true);
  };

  const confirmMarkAsSold = async () => {
    try {
      await itemsAPI.bulkUpdateStatus(selectedItems, 'sold');
      toast.success(`${selectedItems.length} items marked as sold`);
      setSelectedItems([]);
      setConfirmDialog(false);
      loadResaleItems();
    } catch (error) {
      toast.error('Failed to update items');
    }
  };

  const handleExportSoldItems = async () => {
    try {
      const response = await itemsAPI.exportSoldItems();
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `sold_items_${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      toast.success('Export completed');
    } catch (error) {
      toast.error('Failed to export sold items');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Resale Items</Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={handleExportSoldItems}
          >
            Export Sold
          </Button>
          <Button
            variant="contained"
            color="success"
            startIcon={<AttachMoney />}
            onClick={handleMarkAsSold}
            disabled={selectedItems.length === 0}
          >
            Mark as Sold ({selectedItems.length})
          </Button>
          <Button
            variant="contained"
            startIcon={<Refresh />}
            onClick={loadResaleItems}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Total Resale</Typography>
              <Typography variant="h5">{stats.totalResale}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Pending Sale</Typography>
              <Typography variant="h5" color="warning.main">{stats.pendingSale}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Sold</Typography>
              <Typography variant="h5" color="success.main">{stats.sold}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Total Value</Typography>
              <Typography variant="h5">{formatCurrency(stats.totalValue)}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={selectedCategory}
                onChange={(e) => {
                  setSelectedCategory(e.target.value);
                  setSelectedSubcategory('');
                }}
                label="Category"
              >
                <MenuItem value="">All Categories</MenuItem>
                {categories.map(cat => (
                  <MenuItem key={cat.id} value={cat.id}>{cat.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth disabled={!selectedCategory}>
              <InputLabel>Subcategory</InputLabel>
              <Select
                value={selectedSubcategory}
                onChange={(e) => setSelectedSubcategory(e.target.value)}
                label="Subcategory"
              >
                <MenuItem value="">All Subcategories</MenuItem>
                {subcategories.map(sub => (
                  <MenuItem key={sub.id} value={sub.id}>{sub.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Button
              fullWidth
              variant="outlined"
              onClick={handleSelectAll}
              startIcon={selectedItems.length === resaleItems.length ? <CheckBox /> : <CheckBoxOutlineBlank />}
            >
              {selectedItems.length === resaleItems.length ? 'Deselect All' : 'Select All'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Items Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  checked={selectedItems.length === resaleItems.length && resaleItems.length > 0}
                  indeterminate={selectedItems.length > 0 && selectedItems.length < resaleItems.length}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell>Tag ID</TableCell>
              <TableCell>Item Name</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Subcategory</TableCell>
              <TableCell>Quality</TableCell>
              <TableCell>Resale Price</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : resaleItems.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <Alert severity="info">No resale items found</Alert>
                </TableCell>
              </TableRow>
            ) : (
              resaleItems.map((item) => (
                <TableRow key={item.tag_id} selected={selectedItems.includes(item.tag_id)}>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selectedItems.includes(item.tag_id)}
                      onChange={() => handleSelectItem(item.tag_id)}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {item.tag_id}
                    </Typography>
                  </TableCell>
                  <TableCell>{item.common_name}</TableCell>
                  <TableCell>{item.category}</TableCell>
                  <TableCell>{item.subcategory}</TableCell>
                  <TableCell>
                    <Chip
                      label={item.quality || 'Good'}
                      color={item.quality === 'Poor' ? 'error' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="bold">
                      {formatCurrency(item.resale_price)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={item.status}
                      color={item.status === 'sold' ? 'success' : 'warning'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <IconButton size="small">
                      <Print />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Confirm Dialog */}
      <Dialog open={confirmDialog} onClose={() => setConfirmDialog(false)}>
        <DialogTitle>Confirm Sale</DialogTitle>
        <DialogContent>
          <Typography>
            Mark {selectedItems.length} items as sold?
          </Typography>
          <Typography variant="caption" color="textSecondary">
            This action cannot be undone. Items will be removed from rental inventory.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog(false)}>Cancel</Button>
          <Button onClick={confirmMarkAsSold} variant="contained" color="success">
            Confirm Sale
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ResalePage;