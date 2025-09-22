// Contracts Page with Tag Assignment
// Version: 1.0.0
// Date: 2025-09-20
// Critical Feature: Assign RFID tags to POS contract items

import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Paper,
  Tabs,
  Tab,
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  IconButton,
  Grid,
  Card,
  CardContent,
  Alert,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Badge
} from '@mui/material';
import {
  QrCodeScanner,
  PhotoCamera,
  CheckCircle,
  Warning,
  Add,
  Assignment,
  Person,
  CalendarToday,
  Store
} from '@mui/icons-material';
import toast from 'react-hot-toast';
import { contractsAPI } from '../services/api';

// Date formatter
const formatDate = (date) => {
  if (!date) return 'N/A';
  return new Date(date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

function ContractsPage() {
  const [tabValue, setTabValue] = useState(0);
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedContract, setSelectedContract] = useState(null);
  const [tagAssignDialog, setTagAssignDialog] = useState(false);
  const [manualContractDialog, setManualContractDialog] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [scannedTag, setScannedTag] = useState('');
  const [photoCapture, setPhotoCapture] = useState(null);
  const scanInputRef = useRef(null);


  useEffect(() => {
    loadContracts();
  }, [tabValue]);

  const loadContracts = async () => {
    setLoading(true);
    try {
      // Determine days ahead based on tab
      const daysAhead = tabValue <= 1 ? 0 : tabValue - 1;

      const response = await contractsAPI.getOpen({
        days_ahead: daysAhead
      });

      setContracts(response.data);
      setLoading(false);
    } catch (error) {
      toast.error('Failed to load contracts');
      setLoading(false);
    }
  };

  const handleContractClick = (contract) => {
    setSelectedContract(contract);
  };

  const handleTagAssignment = (contractNo, item) => {
    setSelectedItem({ ...item, contract_no: contractNo });
    setTagAssignDialog(true);
    setTimeout(() => scanInputRef.current?.focus(), 100);
  };

  const processTagAssignment = async () => {
    if (!scannedTag) {
      toast.error('Please scan or enter a tag');
      return;
    }

    try {
      const response = await contractsAPI.assignTag({
        contract_no: selectedItem.contract_no,
        item_number: selectedItem.item_number,
        tag_id: scannedTag,
        quantity: 1
      });

      toast.success(`Tag ${scannedTag} assigned successfully`);

      // Refresh contract data
      loadContracts();

      // Close dialog and reset
      setTagAssignDialog(false);
      setScannedTag('');
      setSelectedItem(null);
      setPhotoCapture(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to assign tag');
    }
  };

  const handlePhotoCapture = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhotoCapture(reader.result);
        toast.success('Photo captured for quantity verification');
      };
      reader.readAsDataURL(file);
    }
  };

  const createManualContract = async (contractData) => {
    try {
      const response = await axios.post(`${API_URL}/contracts/manual`, contractData);
      toast.success('Manual contract created successfully');
      setManualContractDialog(false);
      loadContracts();
    } catch (error) {
      toast.error('Failed to create manual contract');
    }
  };

  const getItemStatus = (item, rfidItems) => {
    const assignedCount = rfidItems.filter(
      rfid => rfid.rental_class_num === item.item_number
    ).length;

    if (assignedCount === 0) return 'unassigned';
    if (assignedCount < item.quantity) return 'partial';
    return 'complete';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'complete': return 'success';
      case 'partial': return 'warning';
      case 'unassigned': return 'error';
      default: return 'default';
    }
  };

  const tabLabels = [
    'Today',
    'Active',
    'Tomorrow',
    'Day +2',
    'Day +3',
    'Custom Date'
  ];

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 2 }}>
      <Typography variant="h4" gutterBottom>
        Contracts & Reservations
      </Typography>

      <Paper sx={{ mb: 2 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          {tabLabels.map((label, index) => (
            <Tab key={index} label={label} />
          ))}
        </Tabs>
      </Paper>

      <Box display="flex" justifyContent="flex-end" mb={2}>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setManualContractDialog(true)}
        >
          Manual Contract
        </Button>
      </Box>

      {loading ? (
        <LinearProgress />
      ) : (
        <Grid container spacing={3}>
          {/* Contracts List */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                {contracts.length} Contracts
              </Typography>

              <List>
                {contracts.map((contract) => {
                  const totalItems = contract.items.length;
                  const assignedItems = contract.rfid_items.length;

                  return (
                    <React.Fragment key={contract.contract_no}>
                      <ListItem
                        button
                        onClick={() => handleContractClick(contract)}
                        selected={selectedContract?.contract_no === contract.contract_no}
                      >
                        <ListItemText
                          primary={
                            <Box display="flex" alignItems="center" gap={1}>
                              <Typography variant="subtitle1">
                                {contract.contract_no}
                              </Typography>
                              {contract.is_manual && (
                                <Chip label="Manual" size="small" color="warning" />
                              )}
                            </Box>
                          }
                          secondary={
                            <Box>
                              <Typography variant="body2">
                                <Person fontSize="small" /> {contract.customer_name || 'No customer'}
                              </Typography>
                              <Typography variant="body2">
                                <CalendarToday fontSize="small" /> {formatDate(contract.delivery_date)}
                              </Typography>
                              <Typography variant="body2">
                                <Store fontSize="small" /> Store {contract.store_no}
                              </Typography>
                            </Box>
                          }
                        />
                        <ListItemSecondaryAction>
                          <Badge
                            badgeContent={`${assignedItems}/${totalItems}`}
                            color={assignedItems === totalItems ? 'success' : 'warning'}
                          >
                            <Assignment />
                          </Badge>
                        </ListItemSecondaryAction>
                      </ListItem>
                      <Divider />
                    </React.Fragment>
                  );
                })}
              </List>
            </Paper>
          </Grid>

          {/* Contract Details */}
          <Grid item xs={12} md={6}>
            {selectedContract ? (
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Contract Details: {selectedContract.contract_no}
                </Typography>

                <Box mb={2}>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Customer
                      </Typography>
                      <Typography variant="body1">
                        {selectedContract.customer_name || 'Not specified'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Delivery Date
                      </Typography>
                      <Typography variant="body1">
                        {formatDate(selectedContract.delivery_date)}
                      </Typography>
                    </Grid>
                  </Grid>
                </Box>

                <Divider sx={{ my: 2 }} />

                <Typography variant="subtitle1" gutterBottom>
                  Contract Items
                </Typography>

                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Item</TableCell>
                        <TableCell align="center">Qty</TableCell>
                        <TableCell align="center">Tagged</TableCell>
                        <TableCell align="center">Status</TableCell>
                        <TableCell align="center">Action</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedContract.items.map((item, index) => {
                        const status = getItemStatus(item, selectedContract.rfid_items);
                        const assignedCount = selectedContract.rfid_items.filter(
                          rfid => rfid.rental_class_num === item.item_number
                        ).length;

                        return (
                          <TableRow key={index}>
                            <TableCell>
                              <Typography variant="body2">
                                {item.description || item.item_number}
                              </Typography>
                            </TableCell>
                            <TableCell align="center">{item.quantity}</TableCell>
                            <TableCell align="center">{assignedCount}</TableCell>
                            <TableCell align="center">
                              <Chip
                                label={status}
                                size="small"
                                color={getStatusColor(status)}
                              />
                            </TableCell>
                            <TableCell align="center">
                              <IconButton
                                size="small"
                                color="primary"
                                onClick={() => handleTagAssignment(
                                  selectedContract.contract_no,
                                  item
                                )}
                              >
                                <QrCodeScanner />
                              </IconButton>
                              {item.equipment?.needs_photo && (
                                <IconButton size="small" color="secondary">
                                  <PhotoCamera />
                                </IconButton>
                              )}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>

                {selectedContract.rfid_items.length > 0 && (
                  <>
                    <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                      Assigned RFID Tags
                    </Typography>
                    <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                      {selectedContract.rfid_items.map((item) => (
                        <Chip
                          key={item.tag_id}
                          label={`${item.tag_id.slice(-6)} - ${item.common_name}`}
                          size="small"
                          sx={{ m: 0.5 }}
                          icon={<CheckCircle />}
                        />
                      ))}
                    </Box>
                  </>
                )}
              </Paper>
            ) : (
              <Paper sx={{ p: 4, textAlign: 'center' }}>
                <Assignment sx={{ fontSize: 64, color: 'action.disabled' }} />
                <Typography variant="h6" color="text.secondary">
                  Select a contract to view details
                </Typography>
              </Paper>
            )}
          </Grid>
        </Grid>
      )}

      {/* Tag Assignment Dialog */}
      <Dialog
        open={tagAssignDialog}
        onClose={() => setTagAssignDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Assign Tag to Item
        </DialogTitle>
        <DialogContent>
          {selectedItem && (
            <Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                Assigning tag to: {selectedItem.description || selectedItem.item_number}
                <br />
                Contract: {selectedItem.contract_no}
              </Alert>

              <TextField
                fullWidth
                inputRef={scanInputRef}
                label="Scan or Enter Tag ID"
                value={scannedTag}
                onChange={(e) => setScannedTag(e.target.value.toUpperCase())}
                placeholder="RFID or QR Code"
                autoFocus
                sx={{ mb: 2 }}
                InputProps={{
                  endAdornment: <QrCodeScanner />
                }}
              />

              {selectedItem.equipment?.needs_photo && (
                <Box>
                  <Typography variant="body2" gutterBottom>
                    Photo required for quantity verification
                  </Typography>
                  <input
                    accept="image/*"
                    type="file"
                    capture="environment"
                    onChange={handlePhotoCapture}
                    style={{ display: 'none' }}
                    id="photo-capture"
                  />
                  <label htmlFor="photo-capture">
                    <Button
                      variant="outlined"
                      component="span"
                      startIcon={<PhotoCamera />}
                      fullWidth
                    >
                      Capture Photo
                    </Button>
                  </label>
                  {photoCapture && (
                    <Box mt={2}>
                      <img
                        src={photoCapture}
                        alt="Item verification"
                        style={{ width: '100%', maxHeight: 200, objectFit: 'contain' }}
                      />
                    </Box>
                  )}
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTagAssignDialog(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={processTagAssignment}
            disabled={!scannedTag || (selectedItem?.equipment?.needs_photo && !photoCapture)}
          >
            Assign Tag
          </Button>
        </DialogActions>
      </Dialog>

      {/* Manual Contract Dialog */}
      <Dialog
        open={manualContractDialog}
        onClose={() => setManualContractDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create Manual Contract</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Use this when POS system is lagging. Contract will auto-merge when POS updates.
          </Alert>
          {/* Manual contract form would go here */}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setManualContractDialog(false)}>
            Cancel
          </Button>
          <Button variant="contained">
            Create Contract
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default ContractsPage;