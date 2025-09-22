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
  Collapse,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Badge,
  Divider
} from '@mui/material';
import {
  LocalLaundryService,
  ExpandMore,
  ExpandLess,
  Add,
  Print,
  Check,
  Refresh,
  History,
  Assignment
} from '@mui/icons-material';
import { serviceAPI, itemsAPI } from '../services/api';
import toast from 'react-hot-toast';

const LaundryPage = () => {
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedContracts, setExpandedContracts] = useState({});
  const [handCountDialog, setHandCountDialog] = useState(false);
  const [selectedContract, setSelectedContract] = useState(null);
  const [handCountForm, setHandCountForm] = useState({
    category: '',
    subcategory: '',
    commonName: '',
    quantity: 1,
    notes: ''
  });
  const [categories, setCategories] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const [commonNames, setCommonNames] = useState([]);
  const [stats, setStats] = useState({
    active: 0,
    finalized: 0,
    returned: 0,
    totalItems: 0
  });

  useEffect(() => {
    loadLaundryContracts();
    loadCategories();
  }, []);

  const loadLaundryContracts = async () => {
    setLoading(true);
    try {
      const response = await serviceAPI.getLaundryContracts();
      setContracts(response.data);
      calculateStats(response.data);
    } catch (error) {
      toast.error('Failed to load laundry contracts');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (contractsData) => {
    const newStats = {
      active: contractsData.filter(c => c.status === 'PreWash Count').length,
      finalized: contractsData.filter(c => c.status === 'Sent to Laundry').length,
      returned: contractsData.filter(c => c.status === 'Returned').length,
      totalItems: contractsData.reduce((sum, c) => sum + (c.item_count || 0), 0)
    };
    setStats(newStats);
  };

  const loadCategories = async () => {
    try {
      const response = await itemsAPI.getCategories();
      setCategories(response.data);
    } catch (error) {
      console.error('Failed to load categories', error);
    }
  };

  const loadSubcategories = async (categoryId) => {
    try {
      const response = await itemsAPI.getSubcategories(categoryId);
      setSubcategories(response.data);
    } catch (error) {
      console.error('Failed to load subcategories', error);
    }
  };

  const loadCommonNames = async (subcategoryId) => {
    try {
      const response = await itemsAPI.getCommonNames(subcategoryId);
      setCommonNames(response.data);
    } catch (error) {
      console.error('Failed to load common names', error);
    }
  };

  const toggleContract = (contractId) => {
    setExpandedContracts(prev => ({
      ...prev,
      [contractId]: !prev[contractId]
    }));
  };

  const handleFinalizeContract = async (contractId) => {
    try {
      await serviceAPI.finalizeLaundryContract(contractId);
      toast.success('Contract finalized and sent to laundry');
      loadLaundryContracts();
    } catch (error) {
      toast.error('Failed to finalize contract');
    }
  };

  const handleMarkReturned = async (contractId) => {
    try {
      await serviceAPI.markLaundryReturned(contractId);
      toast.success('Contract marked as returned');
      loadLaundryContracts();
    } catch (error) {
      toast.error('Failed to mark as returned');
    }
  };

  const handleReactivateContract = async (contractId) => {
    try {
      await serviceAPI.reactivateLaundryContract(contractId);
      toast.success('Contract reactivated');
      loadLaundryContracts();
    } catch (error) {
      toast.error('Failed to reactivate contract');
    }
  };

  const openHandCountDialog = (contract) => {
    setSelectedContract(contract);
    setHandCountDialog(true);
    setHandCountForm({
      category: '',
      subcategory: '',
      commonName: '',
      quantity: 1,
      notes: ''
    });
  };

  const handleAddHandCount = async () => {
    if (!handCountForm.commonName || !handCountForm.quantity) {
      toast.error('Please select an item and quantity');
      return;
    }

    try {
      await serviceAPI.addHandCountedItem({
        contract_id: selectedContract.id,
        common_name: handCountForm.commonName,
        quantity: handCountForm.quantity,
        notes: handCountForm.notes
      });
      toast.success('Hand-counted item added');
      setHandCountDialog(false);
      loadLaundryContracts();
    } catch (error) {
      toast.error('Failed to add hand-counted item');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'PreWash Count':
        return 'success';
      case 'Sent to Laundry':
        return 'warning';
      case 'Returned':
        return 'info';
      default:
        return 'default';
    }
  };

  const formatDate = (date) => {
    if (!date) return 'N/A';
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Laundry Contracts</Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<History />}
            onClick={() => toast.info('History view coming soon')}
          >
            History
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => {
              const newContract = { id: 'new', status: 'PreWash Count' };
              openHandCountDialog(newContract);
            }}
          >
            New Contract
          </Button>
          <Button
            variant="contained"
            startIcon={<Refresh />}
            onClick={loadLaundryContracts}
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
              <Typography color="textSecondary" gutterBottom>Active (PreWash)</Typography>
              <Typography variant="h5" color="success.main">{stats.active}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>At Laundry</Typography>
              <Typography variant="h5" color="warning.main">{stats.finalized}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Returned</Typography>
              <Typography variant="h5" color="info.main">{stats.returned}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Total Items</Typography>
              <Typography variant="h5">{stats.totalItems}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Contracts Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell width={40}></TableCell>
              <TableCell>Contract #</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Finalized</TableCell>
              <TableCell align="right">Items</TableCell>
              <TableCell align="right">Hand Counted</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {contracts.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Alert severity="info">No laundry contracts found</Alert>
                </TableCell>
              </TableRow>
            ) : (
              contracts.map((contract) => (
                <React.Fragment key={contract.id}>
                  <TableRow hover>
                    <TableCell>
                      <IconButton size="small" onClick={() => toggleContract(contract.id)}>
                        {expandedContracts[contract.id] ? <ExpandLess /> : <ExpandMore />}
                      </IconButton>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="bold">
                        L-{contract.contract_number || contract.id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={contract.status}
                        color={getStatusColor(contract.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{formatDate(contract.created_at)}</TableCell>
                    <TableCell>{formatDate(contract.finalized_at)}</TableCell>
                    <TableCell align="right">
                      <Badge badgeContent={contract.item_count || 0} color="primary">
                        <LocalLaundryService />
                      </Badge>
                    </TableCell>
                    <TableCell align="right">
                      <Badge badgeContent={contract.hand_counted || 0} color="secondary">
                        <Assignment />
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        {contract.status === 'PreWash Count' && (
                          <>
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => openHandCountDialog(contract)}
                            >
                              Add Items
                            </Button>
                            <Button
                              size="small"
                              variant="contained"
                              color="warning"
                              onClick={() => handleFinalizeContract(contract.id)}
                            >
                              Finalize
                            </Button>
                          </>
                        )}
                        {contract.status === 'Sent to Laundry' && (
                          <Button
                            size="small"
                            variant="contained"
                            color="info"
                            onClick={() => handleMarkReturned(contract.id)}
                          >
                            Mark Returned
                          </Button>
                        )}
                        {contract.status === 'Returned' && (
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => handleReactivateContract(contract.id)}
                          >
                            Reactivate
                          </Button>
                        )}
                        <IconButton size="small">
                          <Print />
                        </IconButton>
                      </Box>
                    </TableCell>
                  </TableRow>

                  {/* Expanded Contract Details */}
                  <TableRow>
                    <TableCell colSpan={8} sx={{ p: 0 }}>
                      <Collapse in={expandedContracts[contract.id]} timeout="auto" unmountOnExit>
                        <Box sx={{ p: 2, bgcolor: 'background.default' }}>
                          <Grid container spacing={2}>
                            <Grid item xs={12} md={6}>
                              <Typography variant="subtitle2" gutterBottom>
                                Contract Items
                              </Typography>
                              <List dense>
                                {contract.items?.map((item, idx) => (
                                  <ListItem key={idx}>
                                    <ListItemText
                                      primary={item.common_name}
                                      secondary={`Qty: ${item.quantity}`}
                                    />
                                    {item.is_hand_counted && (
                                      <Chip label="Hand Counted" size="small" />
                                    )}
                                  </ListItem>
                                )) || (
                                  <ListItem>
                                    <ListItemText secondary="No items added yet" />
                                  </ListItem>
                                )}
                              </List>
                            </Grid>
                            <Grid item xs={12} md={6}>
                              <Typography variant="subtitle2" gutterBottom>
                                Contract Timeline
                              </Typography>
                              <List dense>
                                <ListItem>
                                  <ListItemText
                                    primary="Created"
                                    secondary={formatDate(contract.created_at)}
                                  />
                                </ListItem>
                                {contract.finalized_at && (
                                  <ListItem>
                                    <ListItemText
                                      primary="Sent to Laundry"
                                      secondary={formatDate(contract.finalized_at)}
                                    />
                                  </ListItem>
                                )}
                                {contract.returned_at && (
                                  <ListItem>
                                    <ListItemText
                                      primary="Returned"
                                      secondary={formatDate(contract.returned_at)}
                                    />
                                  </ListItem>
                                )}
                              </List>
                            </Grid>
                          </Grid>
                        </Box>
                      </Collapse>
                    </TableCell>
                  </TableRow>
                </React.Fragment>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Hand Count Dialog */}
      <Dialog open={handCountDialog} onClose={() => setHandCountDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Hand-Counted Items</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Category</InputLabel>
                  <Select
                    value={handCountForm.category}
                    onChange={(e) => {
                      setHandCountForm({ ...handCountForm, category: e.target.value });
                      loadSubcategories(e.target.value);
                    }}
                    label="Category"
                  >
                    {categories.map(cat => (
                      <MenuItem key={cat.id} value={cat.id}>{cat.name}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <FormControl fullWidth disabled={!handCountForm.category}>
                  <InputLabel>Subcategory</InputLabel>
                  <Select
                    value={handCountForm.subcategory}
                    onChange={(e) => {
                      setHandCountForm({ ...handCountForm, subcategory: e.target.value });
                      loadCommonNames(e.target.value);
                    }}
                    label="Subcategory"
                  >
                    {subcategories.map(sub => (
                      <MenuItem key={sub.id} value={sub.id}>{sub.name}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <FormControl fullWidth disabled={!handCountForm.subcategory}>
                  <InputLabel>Item Name</InputLabel>
                  <Select
                    value={handCountForm.commonName}
                    onChange={(e) => setHandCountForm({ ...handCountForm, commonName: e.target.value })}
                    label="Item Name"
                  >
                    {commonNames.map(cn => (
                      <MenuItem key={cn.name} value={cn.name}>{cn.name}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Quantity"
                  type="number"
                  value={handCountForm.quantity}
                  onChange={(e) => setHandCountForm({ ...handCountForm, quantity: parseInt(e.target.value) || 1 })}
                  inputProps={{ min: 1 }}
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Notes (optional)"
                  multiline
                  rows={2}
                  value={handCountForm.notes}
                  onChange={(e) => setHandCountForm({ ...handCountForm, notes: e.target.value })}
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHandCountDialog(false)}>Cancel</Button>
          <Button onClick={handleAddHandCount} variant="contained">Add Item</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LaundryPage;