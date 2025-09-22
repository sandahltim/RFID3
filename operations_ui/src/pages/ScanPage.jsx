import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Alert,
  IconButton,
  Divider
} from '@mui/material';
import {
  QrCodeScanner,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  Inventory,
  Build,
  LocalLaundryService,
  PhotoCamera
} from '@mui/icons-material';
import toast from 'react-hot-toast';

const ScanPage = () => {
  const [scanMode, setScanMode] = useState('checkout'); // checkout, return, service, laundry
  const [lastScan, setLastScan] = useState('');
  const [scanHistory, setScanHistory] = useState([]);
  const [currentContract, setCurrentContract] = useState(null);
  const [manualEntry, setManualEntry] = useState('');
  const [isScanning, setIsScanning] = useState(false);

  // Listen for scanner input (HID mode)
  useEffect(() => {
    let scanBuffer = '';
    let scanTimeout;

    const handleKeyPress = (e) => {
      // Clear timeout on each keypress
      clearTimeout(scanTimeout);

      // Add character to buffer
      if (e.key === 'Enter') {
        // Process scan when Enter is pressed
        if (scanBuffer.length > 0) {
          handleScan(scanBuffer);
          scanBuffer = '';
        }
      } else if (e.key.length === 1) {
        scanBuffer += e.key;
        // Set timeout to clear buffer if no input for 100ms
        scanTimeout = setTimeout(() => {
          scanBuffer = '';
        }, 100);
      }
    };

    window.addEventListener('keypress', handleKeyPress);
    return () => window.removeEventListener('keypress', handleKeyPress);
  }, [scanMode, currentContract]);

  const handleScan = async (tagId) => {
    setLastScan(tagId);
    setIsScanning(true);

    try {
      let endpoint = '';
      let body = {};

      switch(scanMode) {
        case 'checkout':
          if (!currentContract) {
            toast.error('Select a contract first');
            return;
          }
          endpoint = '/api/contracts/assign-tag';
          body = {
            contract_no: currentContract.contract_no,
            tag_id: tagId,
            item_number: 'SCAN' // Will be matched on backend
          };
          break;
        case 'return':
          endpoint = '/api/operations/return';
          body = { tag_id: tagId };
          break;
        case 'service':
          endpoint = '/api/operations/service';
          body = { tag_id: tagId, service_type: 'repair' };
          break;
        case 'laundry':
          endpoint = '/api/operations/laundry';
          body = { tag_id: tagId, action: 'check_in' };
          break;
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      const data = await response.json();

      if (response.ok) {
        toast.success(`Tag ${tagId} processed`);
        setScanHistory(prev => [{
          tagId,
          mode: scanMode,
          timestamp: new Date().toISOString(),
          status: 'success'
        }, ...prev.slice(0, 9)]);
      } else {
        toast.error(data.detail || 'Scan failed');
        setScanHistory(prev => [{
          tagId,
          mode: scanMode,
          timestamp: new Date().toISOString(),
          status: 'error',
          error: data.detail
        }, ...prev.slice(0, 9)]);
      }
    } catch (error) {
      toast.error('Network error');
      console.error('Scan error:', error);
    } finally {
      setIsScanning(false);
    }
  };

  const handleManualSubmit = () => {
    if (manualEntry.trim()) {
      handleScan(manualEntry.trim());
      setManualEntry('');
    }
  };

  const loadContract = async (contractNo) => {
    try {
      const response = await fetch(`/api/contracts/${contractNo}/items`);
      const data = await response.json();
      setCurrentContract(data);
      toast.success(`Contract ${contractNo} loaded`);
    } catch (error) {
      toast.error('Failed to load contract');
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Scan Operations
      </Typography>

      <Grid container spacing={3}>
        {/* Mode Selection */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Scan Mode</Typography>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant={scanMode === 'checkout' ? 'contained' : 'outlined'}
                startIcon={<Inventory />}
                onClick={() => setScanMode('checkout')}
              >
                Checkout
              </Button>
              <Button
                variant={scanMode === 'return' ? 'contained' : 'outlined'}
                startIcon={<CheckCircle />}
                onClick={() => setScanMode('return')}
              >
                Return
              </Button>
              <Button
                variant={scanMode === 'service' ? 'contained' : 'outlined'}
                startIcon={<Build />}
                onClick={() => setScanMode('service')}
              >
                Service
              </Button>
              <Button
                variant={scanMode === 'laundry' ? 'contained' : 'outlined'}
                startIcon={<LocalLaundryService />}
                onClick={() => setScanMode('laundry')}
              >
                Laundry
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Contract Selection (for checkout mode) */}
        {scanMode === 'checkout' && (
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Contract Selection</Typography>
              {currentContract ? (
                <Alert severity="info">
                  Working on Contract: {currentContract.contract_no}
                </Alert>
              ) : (
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                  <TextField
                    placeholder="Enter contract number"
                    size="small"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        loadContract(e.target.value);
                      }
                    }}
                  />
                  <Button variant="contained" onClick={() => {
                    // Load open contracts
                    window.location.href = '#/contracts';
                  }}>
                    Select from Open Contracts
                  </Button>
                </Box>
              )}
            </Paper>
          </Grid>
        )}

        {/* Scanner Status */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <QrCodeScanner sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography variant="h6">Scanner Status</Typography>
                  <Chip
                    label={isScanning ? "Scanning..." : "Ready"}
                    color={isScanning ? "warning" : "success"}
                    size="small"
                  />
                </Box>
              </Box>

              {lastScan && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  Last Scan: {lastScan}
                </Alert>
              )}

              <Divider sx={{ my: 2 }} />

              {/* Manual Entry */}
              <Typography variant="subtitle2" gutterBottom>Manual Entry</Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Enter tag ID manually"
                  value={manualEntry}
                  onChange={(e) => setManualEntry(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleManualSubmit();
                    }
                  }}
                />
                <Button variant="contained" onClick={handleManualSubmit}>
                  Submit
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Scan History */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Recent Scans</Typography>
              <List dense>
                {scanHistory.map((scan, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      {scan.status === 'success' ?
                        <CheckCircle color="success" /> :
                        <ErrorIcon color="error" />
                      }
                    </ListItemIcon>
                    <ListItemText
                      primary={scan.tagId}
                      secondary={`${scan.mode} - ${new Date(scan.timestamp).toLocaleTimeString()}`}
                    />
                  </ListItem>
                ))}
                {scanHistory.length === 0 && (
                  <ListItem>
                    <ListItemText secondary="No recent scans" />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Instructions */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
            <Typography variant="h6" gutterBottom>Instructions</Typography>
            <Typography variant="body2">
              1. Select the scan mode (Checkout, Return, Service, or Laundry)
              {scanMode === 'checkout' && <><br />2. Select or enter a contract number</>}
              <br />{scanMode === 'checkout' ? '3' : '2'}. Scan items with the Chainway SR160 scanner or enter tag ID manually
              <br />{scanMode === 'checkout' ? '4' : '3'}. Items will be automatically processed based on the selected mode
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ScanPage;