import React, { useState, useEffect } from 'react';
// @ts-ignore
import {
  Box,
  Typography,
  Paper,
  Button,
  TextField,
  Divider,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  IconButton,
  CircularProgress,
  Alert,
  Snackbar,
  Stepper,
  Step,
  StepLabel,
  Checkbox,
  FormControlLabel,
  Radio,
  RadioGroup,
  FormControl,
  FormLabel
} from '@mui/material';
// @ts-ignore
import {
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Api as ApiIcon,
  NetworkCheck as NetworkIcon,
  DeviceHub as DeviceIcon,
  DataObject as PointsIcon
} from '@mui/icons-material';
import { useAppContext } from '../../store/AppContext';
import './FetchBMSPoints.css';

// Define Point type
interface Point {
  id: string;
  name: string;
  description: string;
  type: string;
  source: string;
}

// Define Device type
interface Device {
  id: string;
  name: string;
  instance: string;
  address: string;
  selected?: boolean;
}

// Backend API URLs - ensure this matches your actual backend URL
const API_BASE_URL = 'http://localhost:5000/api';

// Step labels
const steps = ['Connect to API', 'Select Network', 'Discover Devices', 'Fetch Points'];

// Renamed component
const FetchBMSPoints: React.FC = () => {
  const { state, dispatch } = useAppContext();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [healthStatus, setHealthStatus] = useState<string | null>(null);
  
  // API connection states
  const [apiUrl, setApiUrl] = useState<string>("https://ag-eu2.envisioniot.com");
  const [accessKey, setAccessKey] = useState<string>("974a84b0-2ec1-44f7-aa3d-5fe01b55b718");
  const [secretKey, setSecretKey] = useState<string>("04cc544f-ffcb-4b97-84fc-d7ecf8c4b8be");
  const [orgId, setOrgId] = useState<string>("o16975327606411181");
  const [assetId, setAssetId] = useState<string>("5xkIipSH");
  
  // Network and device states
  const [networks, setNetworks] = useState<string[]>([]);
  const [selectedNetwork, setSelectedNetwork] = useState<string>("");
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevices, setSelectedDevices] = useState<string[]>([]);
  
  // Check backend health on component mount
  useEffect(() => {
    const checkBackendHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
          const data = await response.json();
          setHealthStatus(`Backend is ${data.status}`);
          console.log('Backend health check successful:', data);
        } else {
          setHealthStatus('Backend is unreachable');
          console.error('Backend health check failed:', response.statusText);
        }
      } catch (err) {
        setHealthStatus('Backend is unreachable');
        console.error('Error checking backend health:', err);
      }
    };
    
    checkBackendHealth();
  }, []);

  // Handle API connection (Step 1)
  const handleConnect = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    
    console.log('Connecting to BMS API with credentials:', { 
      apiUrl, accessKey, secretKey: '***hidden***', orgId, assetId 
    });
    
    try {
      const connectResponse = await fetch(`${API_BASE_URL}/bms/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          apiUrl,
          accessKey,
          secretKey,
          orgId,
          assetId
        }),
      });

      console.log('Connect response status:', connectResponse.status);
      
      if (!connectResponse.ok) {
        const errorText = await connectResponse.text();
        console.error('Connect response error:', errorText);
        
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch (e) {
          throw new Error(`Failed to connect to BMS API: ${connectResponse.status} ${connectResponse.statusText}`);
        }
        
        throw new Error(errorData.details || 'Failed to connect to BMS API');
      }
      
      const connectData = await connectResponse.json();
      console.log('Connect response data:', connectData);
      
      // Check for network configurations in the response
      if (connectData.net_config && Array.isArray(connectData.net_config) && connectData.net_config.length > 0) {
        setNetworks(connectData.net_config);
        setSelectedNetwork(connectData.net_config[0]); // Default to first network
      } else {
        setNetworks(['No Network Card']); // Default fallback
        setSelectedNetwork('No Network Card');
      }
      
      setSuccess('Successfully connected to BMS API');
      // Move to next step
      setActiveStep(1);
      
    } catch (err) {
      console.error('Error connecting to BMS API:', err);
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Handle network selection (Step 2)
  const handleNetworkSelect = (network: string) => {
    setSelectedNetwork(network);
  };

  // Handle device discovery (Step 2 to 3)
  const handleDiscoverDevices = async () => {
    if (!selectedNetwork) {
      setError('Please select a network first');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      console.log(`Discovering devices on network: ${selectedNetwork}`);
      const response = await fetch(`${API_BASE_URL}/bms/discover-devices?assetId=${assetId}&network=${selectedNetwork}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Device discovery error:', errorText);
        
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch (e) {
          throw new Error(`Failed to discover devices: ${response.status} ${response.statusText}`);
        }
        
        throw new Error(errorData.details || 'Failed to discover devices');
      }
      
      const data = await response.json();
      console.log('Device discovery data:', data);
      
      if (data.all_devices && Array.isArray(data.all_devices) && data.all_devices.length > 0) {
        // Format devices
        const formattedDevices = data.all_devices.map((device: any) => ({
          id: device.id || device.otDeviceInst || String(Math.random()),
          name: device.deviceName || `Device ${device.otDeviceInst}`,
          instance: device.otDeviceInst || '',
          address: device.address || 'Unknown',
          selected: true // Default all to selected
        }));
        
        setDevices(formattedDevices);
        setSelectedDevices(formattedDevices.map((d: Device) => d.id));
        setSuccess(`Discovered ${formattedDevices.length} devices`);
      } else {
        // Fall back to dummy devices for demo
        const dummyDevices = [
          { id: '1', name: 'AHU-1', instance: '1001', address: '192.168.1.101', selected: true },
          { id: '2', name: 'AHU-2', instance: '1002', address: '192.168.1.102', selected: true },
          { id: '3', name: 'VAV-1', instance: '2001', address: '192.168.1.201', selected: true }
        ];
        
        setDevices(dummyDevices);
        setSelectedDevices(dummyDevices.map(d => d.id));
        setSuccess('No real devices found. Using sample devices for demonstration');
      }
      
      // Move to next step
      setActiveStep(2);
      
    } catch (err) {
      console.error('Error discovering devices:', err);
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Handle device selection
  const handleDeviceSelect = (deviceId: string) => {
    setSelectedDevices(prev => {
      if (prev.includes(deviceId)) {
        return prev.filter(id => id !== deviceId);
      } else {
        return [...prev, deviceId];
      }
    });
  };

  // Handle point fetching (Step 3 to 4)
  const handleFetchPoints = async () => {
    if (selectedDevices.length === 0) {
      setError('Please select at least one device to fetch points');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // Build selected devices array
      const deviceInstances = devices
        .filter(d => selectedDevices.includes(d.id))
        .map(d => d.instance);
      
      console.log(`Fetching points for devices: ${deviceInstances.join(', ')}`);
      
      const response = await fetch(`${API_BASE_URL}/bms/fetch-points`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          assetId: assetId,
          deviceInstances: deviceInstances
        }),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Points fetching error:', errorText);
        
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch (e) {
          throw new Error(`Failed to fetch points: ${response.status} ${response.statusText}`);
        }
        
        throw new Error(errorData.details || 'Failed to fetch points');
      }
      
      const data = await response.json();
      console.log('Points data:', data);
      
      if (data.points && Array.isArray(data.points)) {
        // Format points with detailed BACnet data
        const formattedPoints = data.points.map((point: any, index: number) => ({
          id: point.id || point.pointId || String(index + 1),
          name: point.name || point.pointName || point.objectName || `Point ${index + 1}`,
          description: point.description || '',
          type: point.type || point.pointType || point.objectType || 'Unknown',
          source: point.source || 'EnvisionIoT',
          // Additional BACnet fields
          objectType: point.objectType || point.type || '',
          otDeviceInst: point.otDeviceInst || '',
          objectInst: point.objectInst || '',
          objectIdentifier: point.objectIdentifier || '',
          objectName: point.objectName || point.name || '',
          presentValue: point.presentValue || '',
          covIncrement: point.covIncrement || '',
          unit: point.unit || '',
          timestamp: point.timestamp || '',
          assetId: point.assetId || '',
          deviceInst: point.deviceInst || '',
          deviceAddr: point.deviceAddr || '',
          pointName: point.pointName || point.name || '',
          pointType: point.pointType || point.type || '',
          pointId: point.pointId || point.id || ''
        }));
        
        // Update state with points
        dispatch({ type: 'SET_POINTS', payload: formattedPoints });
        setSuccess(`Successfully fetched ${formattedPoints.length} points`);
      } else if (data.all_points && Array.isArray(data.all_points)) {
        // Alternative format with detailed BACnet data
        const formattedPoints = data.all_points.map((point: any, index: number) => ({
          id: point.id || point.pointId || String(index + 1),
          name: point.name || point.pointName || point.objectName || `Point ${index + 1}`,
          description: point.description || '',
          type: point.type || point.pointType || point.objectType || 'Unknown',
          source: point.source || 'EnvisionIoT',
          // Additional BACnet fields
          objectType: point.objectType || point.type || '',
          otDeviceInst: point.otDeviceInst || '',
          objectInst: point.objectInst || '',
          objectIdentifier: point.objectIdentifier || '',
          objectName: point.objectName || point.name || '',
          presentValue: point.presentValue || '',
          covIncrement: point.covIncrement || '',
          unit: point.unit || '',
          timestamp: point.timestamp || '',
          assetId: point.assetId || '',
          deviceInst: point.deviceInst || '',
          deviceAddr: point.deviceAddr || '',
          pointName: point.pointName || point.name || '',
          pointType: point.pointType || point.type || '',
          pointId: point.pointId || point.id || ''
        }));
        
        // Update state with points
        dispatch({ type: 'SET_POINTS', payload: formattedPoints });
        setSuccess(`Successfully fetched ${formattedPoints.length} points`);
      } else {
        // Fallback to demo points
        const demoPoints = [
          { id: '1', name: 'AHU1.SAT', description: 'Supply Air Temperature', type: 'AI', source: 'EnvisionIoT' },
          { id: '2', name: 'AHU1.RAT', description: 'Return Air Temperature', type: 'AI', source: 'EnvisionIoT' },
          { id: '3', name: 'AHU1.MAT', description: 'Mixed Air Temperature', type: 'AI', source: 'EnvisionIoT' },
          { id: '4', name: 'AHU1.Fan.Speed', description: 'Fan Speed', type: 'AO', source: 'EnvisionIoT' },
          { id: '5', name: 'AHU1.Damper.Pos', description: 'Damper Position', type: 'AO', source: 'EnvisionIoT' }
        ];
        
        dispatch({ type: 'SET_POINTS', payload: demoPoints });
        setSuccess('Using demo points for demonstration');
      }
      
      // Move to next step
      setActiveStep(3);
      
    } catch (err) {
      console.error('Error fetching points:', err);
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  // Handle step back
  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };
  
  // Handle workflow reset
  const handleReset = () => {
    setActiveStep(0);
    setNetworks([]);
    setSelectedNetwork("");
    setDevices([]);
    setSelectedDevices([]);
    // Keep the points in the state if user wants to view them
  };
  
  // Clearing points
  const handleClearPoints = () => {
    dispatch({ type: 'SET_POINTS', payload: [] });
    setSuccess('Points cleared successfully');
  };
  
  // Function to close alerts
  const handleCloseAlert = () => {
    setError(null);
    setSuccess(null);
  };

  // Export points to CSV
  const exportPointsToCSV = () => {
    if (!state.points || state.points.length === 0) return;
    
    // Map to the columns shown in the image
    const headers = [
      'objectType', 
      'otDeviceInst', 
      'objectInst', 
      'objectId', 
      'objectName', 
      'description', 
      'presentValue', 
      'covIncrement', 
      'unit', 
      'timestamp', 
      'assetId', 
      'deviceInst', 
      'deviceAddr', 
      'pointName', 
      'pointType', 
      'source', 
      'pointId'
    ];
    
    let csvContent = headers.join(',') + '\n';
    
    state.points.forEach(point => {
      // Use actual values from the point data when available
      const row = [
        point.objectType || point.type || '', // objectType
        point.otDeviceInst || '', // otDeviceInst
        point.objectInst || '', // objectInst
        point.objectIdentifier || point.id || '', // objectId
        point.objectName || point.name || '', // objectName
        point.description || '', // description
        point.presentValue || '', // presentValue
        point.covIncrement || '', // covIncrement
        point.unit || '', // unit
        point.timestamp || '', // timestamp
        point.assetId || '', // assetId
        point.deviceInst || '', // deviceInst
        point.deviceAddr || '', // deviceAddr
        point.pointName || point.name || '', // pointName
        point.pointType || point.type || '', // pointType
        point.source || '', // source
        point.pointId || point.id || '' // pointId
      ];
      
      // Handle values that might contain commas or quotes
      const formattedRow = row.map(value => {
        if (value === null || value === undefined) return '';
        const str = String(value);
        return str.includes(',') || str.includes('"') ? 
          `"${str.replace(/"/g, '""')}"` : str;
      });
      
      csvContent += formattedRow.join(',') + '\n';
    });
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `bms-points-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Fetch BMS Points
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Follow the steps to connect to a BMS system and fetch points.
      </Typography>

      {/* Backend health status */}
      {healthStatus && (
        <Alert severity={healthStatus.includes('healthy') ? 'success' : 'warning'} sx={{ mb: 2 }}>
          {healthStatus}
        </Alert>
      )}

      {/* Error and Success notifications */}
      <Snackbar open={!!error} autoHideDuration={6000} onClose={handleCloseAlert}>
        <Alert onClose={handleCloseAlert} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
      
      <Snackbar open={!!success} autoHideDuration={6000} onClose={handleCloseAlert}>
        <Alert onClose={handleCloseAlert} severity="success" sx={{ width: '100%' }}>
          {success}
        </Alert>
      </Snackbar>

      {/* Stepper */}
      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Grid container spacing={3}>
        {/* Multi-step form section */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            {/* Step 1: Connect to API */}
            {activeStep === 0 && (
              <>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="h6" gutterBottom>
                    Step 1: Connect to BMS API
                  </Typography>
                  <ApiIcon color="primary" />
                </Box>
                <Divider sx={{ mb: 2 }} />

                <form onSubmit={handleConnect}>
                  <TextField
                    label="API URL"
                    fullWidth
                    margin="normal"
                    value={apiUrl}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setApiUrl(e.target.value)}
                    required
                  />
                  <TextField
                    label="Access Key"
                    fullWidth
                    margin="normal"
                    value={accessKey}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAccessKey(e.target.value)}
                    required
                  />
                  <TextField
                    label="Secret Key"
                    fullWidth
                    margin="normal"
                    type="password"
                    value={secretKey}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSecretKey(e.target.value)}
                    required
                  />
                  <TextField
                    label="Organization ID"
                    fullWidth
                    margin="normal"
                    value={orgId}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOrgId(e.target.value)}
                    required
                  />
                  <TextField
                    label="Asset ID"
                    fullWidth
                    margin="normal"
                    value={assetId}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAssetId(e.target.value)}
                    required
                  />
                  <Button
                    type="submit"
                    variant="contained"
                    fullWidth
                    disabled={loading}
                    sx={{ mt: 2 }}
                  >
                    {loading ? (
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <CircularProgress size={24} sx={{ mr: 1 }} />
                        Connecting...
                      </Box>
                    ) : 'Connect to API'}
                  </Button>
                </form>
              </>
            )}

            {/* Step 2: Select Network */}
            {activeStep === 1 && (
              <>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="h6" gutterBottom>
                    Step 2: Select Network
                  </Typography>
                  <NetworkIcon color="primary" />
                </Box>
                <Divider sx={{ mb: 2 }} />

                <FormControl component="fieldset" sx={{ width: '100%' }}>
                  <FormLabel component="legend">Available Networks</FormLabel>
                  <RadioGroup 
                    value={selectedNetwork} 
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleNetworkSelect(e.target.value)}
                  >
                    {networks.map((network) => (
                      <FormControlLabel 
                        key={network} 
                        value={network} 
                        control={<Radio />} 
                        label={network} 
                      />
                    ))}
                  </RadioGroup>
                </FormControl>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
                  <Button onClick={handleBack} disabled={loading}>
                    Back
                  </Button>
                  <Button
                    variant="contained"
                    onClick={handleDiscoverDevices}
                    disabled={!selectedNetwork || loading}
                  >
                    {loading ? (
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <CircularProgress size={24} sx={{ mr: 1 }} />
                        Discovering...
                      </Box>
                    ) : 'Discover Devices'}
                  </Button>
                </Box>
              </>
            )}

            {/* Step 3: Discover Devices */}
            {activeStep === 2 && (
              <>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="h6" gutterBottom>
                    Step 3: Select Devices
                  </Typography>
                  <DeviceIcon color="primary" />
                </Box>
                <Divider sx={{ mb: 2 }} />

                <Typography variant="body2" sx={{ mb: 2 }}>
                  Select the devices to fetch points from:
                </Typography>

                <List sx={{ width: '100%', maxHeight: 300, overflow: 'auto' }}>
                  {devices.map((device) => (
                    <ListItem key={device.id}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={selectedDevices.includes(device.id)}
                            onChange={() => handleDeviceSelect(device.id)}
                          />
                        }
                        label={
                          <Box>
                            <Typography variant="body1">{device.name}</Typography>
                            <Typography variant="body2" color="text.secondary">
                              Instance: {device.instance}, IP: {device.address}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
                  <Button onClick={handleBack} disabled={loading}>
                    Back
                  </Button>
                  <Button
                    variant="contained"
                    onClick={handleFetchPoints}
                    disabled={selectedDevices.length === 0 || loading}
                  >
                    {loading ? (
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <CircularProgress size={24} sx={{ mr: 1 }} />
                        Fetching...
                      </Box>
                    ) : 'Fetch Points'}
                  </Button>
                </Box>
              </>
            )}

            {/* Step 4: Points Fetched */}
            {activeStep === 3 && (
              <>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="h6" gutterBottom>
                    Step 4: Points Fetched
                  </Typography>
                  <PointsIcon color="primary" />
                </Box>
                <Divider sx={{ mb: 2 }} />

                <Box sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="h5">
                    Successfully Fetched {state.points.length} Points
                  </Typography>
                  <Typography variant="body1" sx={{ mt: 1 }}>
                    Your points are now available in the list. You can view them in the panel on the right.
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
                  <Button onClick={handleBack} disabled={loading}>
                    Back
                  </Button>
                  <Button
                    variant="contained"
                    onClick={handleReset}
                    disabled={loading}
                  >
                    Start Over
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={exportPointsToCSV}
                    disabled={state.points.length === 0}
                  >
                    Export Points to CSV
                  </Button>
                </Box>
              </>
            )}
          </Paper>
        </Grid>

        {/* Points List Section */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Available Points ({state.points.length})
                </Typography>
                <Box>
                  <IconButton onClick={handleReset} disabled={loading || activeStep !== 3}>
                    <RefreshIcon />
                  </IconButton>
                  <IconButton onClick={handleClearPoints} disabled={loading || state.points.length === 0}>
                    <DeleteIcon />
                  </IconButton>
                </Box>
              </Box>
              <Divider />

              {state.points.length === 0 ? (
                <Box sx={{ py: 4, textAlign: 'center' }}>
                  <Typography variant="body1" color="textSecondary">
                    No points available. Follow the steps to connect to a BMS system and fetch points.
                  </Typography>
                </Box>
              ) : (
                <List sx={{ maxHeight: 500, overflow: 'auto' }}>
                  {state.points.map((point: Point) => (
                    <ListItem
                      key={point.id}
                      divider
                      secondaryAction={
                        <Typography variant="caption" color="textSecondary">
                          {point.type}
                        </Typography>
                      }
                    >
                      <ListItemText
                        primary={point.name}
                        secondary={
                          <>
                            {point.description}
                            <Typography variant="caption" color="textSecondary" display="block">
                              Source: {point.source}
                            </Typography>
                          </>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default FetchBMSPoints; 