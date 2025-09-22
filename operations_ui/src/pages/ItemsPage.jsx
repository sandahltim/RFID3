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
  TextField,
  Button,
  Chip,
  IconButton,
  InputAdornment
} from '@mui/material';
import {
  Search,
  FilterList,
  QrCode,
  LocationOn,
  Build
} from '@mui/icons-material';
import { itemsAPI } from '../services/api';
import toast from 'react-hot-toast';

const ItemsPage = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStore, setFilterStore] = useState('');

  useEffect(() => {
    loadItems();
  }, []);

  const loadItems = async () => {
    setLoading(true);
    try {
      const response = await itemsAPI.search({
        search: searchTerm,
        store: filterStore
      });
      setItems(response.data);
    } catch (error) {
      toast.error('Failed to load items');
      console.error('Load items error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadItems();
  };

  const getStatusColor = (status) => {
    const statusColors = {
      'available': 'success',
      'rented': 'warning',
      'service': 'error',
      'missing': 'error',
      'laundry': 'info'
    };
    return statusColors[status] || 'default';
  };

  const getIdentifierIcon = (type) => {
    return type === 'QR' ? <QrCode fontSize="small" /> : null;
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Item Inventory
      </Typography>

      {/* Search and Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            fullWidth
            placeholder="Search by tag ID, name, or rental class..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') handleSearch();
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
          />
          <TextField
            select
            label="Store"
            value={filterStore}
            onChange={(e) => setFilterStore(e.target.value)}
            sx={{ minWidth: 150 }}
            SelectProps={{
              native: true,
            }}
          >
            <option value="">All Stores</option>
            <option value="001">Store 001</option>
            <option value="002">Store 002</option>
            <option value="003">Store 003</option>
          </TextField>
          <Button
            variant="contained"
            onClick={handleSearch}
            startIcon={<FilterList />}
          >
            Search
          </Button>
        </Box>
      </Paper>

      {/* Results Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Tag ID</TableCell>
              <TableCell>Item Name</TableCell>
              <TableCell>Rental Class</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Quality</TableCell>
              <TableCell>Location</TableCell>
              <TableCell>Last Contract</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((item) => (
              <TableRow key={item.tag_id}>
                <TableCell>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                    {item.tag_id}
                  </Typography>
                </TableCell>
                <TableCell>{item.common_name}</TableCell>
                <TableCell>{item.rental_class_num}</TableCell>
                <TableCell>
                  <Chip
                    label={item.status}
                    color={getStatusColor(item.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>{item.quality || 'Good'}</TableCell>
                <TableCell>
                  {item.current_store ? (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <LocationOn fontSize="small" />
                      {item.current_store}
                      {item.bin_location && ` - ${item.bin_location}`}
                    </Box>
                  ) : '-'}
                </TableCell>
                <TableCell>{item.last_contract_num || '-'}</TableCell>
                <TableCell>
                  {getIdentifierIcon(item.identifier_type)}
                  {item.identifier_type}
                </TableCell>
                <TableCell>
                  {item.status === 'available' && (
                    <IconButton size="small" title="Send to Service">
                      <Build fontSize="small" />
                    </IconButton>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {items.length === 0 && !loading && (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <Typography variant="body2" color="textSecondary">
                    No items found. Try adjusting your search criteria.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Summary Stats */}
      <Paper sx={{ p: 2, mt: 2 }}>
        <Box sx={{ display: 'flex', gap: 4 }}>
          <Typography variant="body2">
            Total Items: {items.length}
          </Typography>
          <Typography variant="body2">
            Available: {items.filter(i => i.status === 'available').length}
          </Typography>
          <Typography variant="body2">
            Rented: {items.filter(i => i.status === 'rented').length}
          </Typography>
          <Typography variant="body2">
            In Service: {items.filter(i => i.status === 'service').length}
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};

export default ItemsPage;