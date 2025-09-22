import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Alert,
  LinearProgress,
  Badge,
  Grid,
  Card,
  CardContent
} from '@mui/material';
import {
  Build,
  Print,
  Download,
  CheckCircle,
  Warning,
  Refresh,
  QrCode,
  LocalLaundryService
} from '@mui/icons-material';
import { itemsAPI, serviceAPI } from '../services/api';
import toast from 'react-hot-toast';

const ServicePage = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [serviceItems, setServiceItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedItems, setSelectedItems] = useState([]);
  const [printDialog, setPrintDialog] = useState(false);
  const [printQuantity, setPrintQuantity] = useState(1);
  const [serviceTypes, setServiceTypes] = useState({
    dirtyMud: false,
    leaves: false,
    oil: false,
    mold: false,
    stain: false,
    oxidation: false,
    ripTear: false,
    sewingRepair: false,
    grommet: false,
    rope: false,
    buckle: false,
    wet: false,
    serviceRequired: false
  });

  const crews = ['All', 'Tent', 'Linen', 'Service Dept'];

  useEffect(() => {
    loadServiceItems();
  }, [activeTab]);

  const loadServiceItems = async () => {
    setLoading(true);
    try {
      const crew = activeTab === 0 ? '' : crews[activeTab];
      const response = await serviceAPI.getServiceItems({
        crew,
        status: 'service'
      });
      setServiceItems(response.data);
    } catch (error) {
      toast.error('Failed to load service items');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleItemSelect = (itemId) => {
    setSelectedItems(prev => {
      if (prev.includes(itemId)) {
        return prev.filter(id => id !== itemId);
      }
      return [...prev, itemId];
    });
  };

  const handleSelectAll = () => {
    if (selectedItems.length === serviceItems.length) {
      setSelectedItems([]);
    } else {
      setSelectedItems(serviceItems.map(item => item.tag_id));
    }
  };

  const handlePrintTags = async () => {
    if (selectedItems.length === 0) {
      toast.error('No items selected for printing');
      return;
    }

    setPrintDialog(true);
  };

  const confirmPrintTags = async () => {
    try {
      // Generate CSV for Zebra printer
      const response = await serviceAPI.generateTagCSV({
        tag_ids: selectedItems,
        quantity: printQuantity
      });

      // Download CSV file
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `rfid_tags_${new Date().getTime()}.csv`;
      link.click();

      toast.success(`Generated ${selectedItems.length * printQuantity} tags for printing`);

      // Update items as synced
      await serviceAPI.updateSyncedStatus(selectedItems);

      setPrintDialog(false);
      setSelectedItems([]);
      loadServiceItems();
    } catch (error) {
      toast.error('Failed to generate tag CSV');
      console.error(error);
    }
  };

  const handleStatusUpdate = async (itemId, newStatus) => {
    try {
      await itemsAPI.updateStatus(itemId, { status: newStatus });
      toast.success('Status updated');
      loadServiceItems();
    } catch (error) {
      toast.error('Failed to update status');
    }
  };

  const handleServiceComplete = async (itemId) => {
    try {
      await serviceAPI.completeService(itemId, {
        service_types: serviceTypes,
        notes: ''
      });
      toast.success('Service marked complete');
      loadServiceItems();
    } catch (error) {
      toast.error('Failed to complete service');
    }
  };

  const getCrewColor = (crew) => {
    const colors = {
      'Tent': 'primary',
      'Linen': 'secondary',
      'Service Dept': 'warning'
    };
    return colors[crew] || 'default';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Service & Maintenance</Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Print />}
            onClick={handlePrintTags}
            disabled={selectedItems.length === 0}
          >
            Print Tags ({selectedItems.length})
          </Button>
          <Button
            variant="contained"
            startIcon={<Refresh />}
            onClick={loadServiceItems}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Crew Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)}>
          {crews.map((crew, index) => (
            <Tab key={crew} label={crew} />
          ))}
        </Tabs>
      </Paper>

      {/* Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Total Items</Typography>
              <Typography variant="h5">{serviceItems.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Selected</Typography>
              <Typography variant="h5" color="primary.main">{selectedItems.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Needs Repair</Typography>
              <Typography variant="h5" color="error.main">
                {serviceItems.filter(i => i.service_required).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>In Laundry</Typography>
              <Typography variant="h5" color="info.main">
                {serviceItems.filter(i => i.status === 'laundry').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Service Items Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  checked={selectedItems.length === serviceItems.length && serviceItems.length > 0}
                  indeterminate={selectedItems.length > 0 && selectedItems.length < serviceItems.length}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell>Tag ID</TableCell>
              <TableCell>Item Name</TableCell>
              <TableCell>Crew</TableCell>
              <TableCell>Service Type</TableCell>
              <TableCell>Quality</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <LinearProgress />
                </TableCell>
              </TableRow>
            ) : serviceItems.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Alert severity="info">No items in service queue</Alert>
                </TableCell>
              </TableRow>
            ) : (
              serviceItems.map((item) => (
                <TableRow key={item.tag_id} selected={selectedItems.includes(item.tag_id)}>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selectedItems.includes(item.tag_id)}
                      onChange={() => handleItemSelect(item.tag_id)}
                    />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {item.identifier_type === 'QR' && <QrCode fontSize="small" />}
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {item.tag_id}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>{item.common_name}</TableCell>
                  <TableCell>
                    <Chip
                      label={item.crew || 'Unassigned'}
                      color={getCrewColor(item.crew)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {item.service_required && (
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        {item.dirty_mud && <Chip label="Mud" size="small" />}
                        {item.oil && <Chip label="Oil" size="small" />}
                        {item.rip_tear && <Chip label="Tear" size="small" />}
                        {item.sewing_repair && <Chip label="Sewing" size="small" />}
                      </Box>
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={item.quality || 'Good'}
                      color={item.quality === 'Poor' ? 'error' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Select
                      size="small"
                      value={item.status}
                      onChange={(e) => handleStatusUpdate(item.tag_id, e.target.value)}
                    >
                      <MenuItem value="service">In Service</MenuItem>
                      <MenuItem value="laundry">To Laundry</MenuItem>
                      <MenuItem value="available">Complete</MenuItem>
                    </Select>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <IconButton
                        size="small"
                        color="success"
                        onClick={() => handleServiceComplete(item.tag_id)}
                        title="Mark Complete"
                      >
                        <CheckCircle />
                      </IconButton>
                      {item.status === 'service' && (
                        <IconButton
                          size="small"
                          color="info"
                          onClick={() => handleStatusUpdate(item.tag_id, 'laundry')}
                          title="Send to Laundry"
                        >
                          <LocalLaundryService />
                        </IconButton>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Print Dialog */}
      <Dialog open={printDialog} onClose={() => setPrintDialog(false)}>
        <DialogTitle>Print RFID Tags</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            Generate CSV for {selectedItems.length} items
          </Typography>
          <TextField
            label="Quantity per tag"
            type="number"
            value={printQuantity}
            onChange={(e) => setPrintQuantity(parseInt(e.target.value) || 1)}
            fullWidth
            margin="normal"
            inputProps={{ min: 1, max: 10 }}
          />
          <Typography variant="caption" color="textSecondary">
            Total tags to print: {selectedItems.length * printQuantity}
          </Typography>

          {/* Service Type Checkboxes */}
          <Typography variant="subtitle2" sx={{ mt: 2 }}>Service Requirements:</Typography>
          <FormGroup row>
            <FormControlLabel
              control={<Checkbox checked={serviceTypes.dirtyMud} onChange={(e) =>
                setServiceTypes(prev => ({ ...prev, dirtyMud: e.target.checked }))} />}
              label="Dirty/Mud"
            />
            <FormControlLabel
              control={<Checkbox checked={serviceTypes.oil} onChange={(e) =>
                setServiceTypes(prev => ({ ...prev, oil: e.target.checked }))} />}
              label="Oil"
            />
            <FormControlLabel
              control={<Checkbox checked={serviceTypes.ripTear} onChange={(e) =>
                setServiceTypes(prev => ({ ...prev, ripTear: e.target.checked }))} />}
              label="Rip/Tear"
            />
            <FormControlLabel
              control={<Checkbox checked={serviceTypes.sewingRepair} onChange={(e) =>
                setServiceTypes(prev => ({ ...prev, sewingRepair: e.target.checked }))} />}
              label="Sewing"
            />
          </FormGroup>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPrintDialog(false)}>Cancel</Button>
          <Button onClick={confirmPrintTags} variant="contained" startIcon={<Download />}>
            Download CSV
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ServicePage;