const { createProxyMiddleware } = require('http-proxy-middleware');
const bodyParser = require('body-parser');

module.exports = function(app) {
  // Log proxy activity to help debug issues
  console.log('Setting up proxy middleware');
  
  // Parse JSON request bodies
  app.use(bodyParser.json());
  
  // Handle OPTIONS preflight for /api
  app.options('/api', (req, res) => {
    console.log('Handling OPTIONS preflight for /api');
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-access-key, x-secret-key, AccessKey, SecretKey, Access-Control-Allow-Origin');
    res.status(200).end();
  });
  
  // Add a test API endpoint
  app.get('/api', (req, res) => {
    console.log('Mock API endpoint called');
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-access-key, x-secret-key, AccessKey, SecretKey');
    
    // Return a success response
    res.json({
      success: true,
      status: 'ok',
      message: 'Backend API is accessible',
      apiVersion: 'v1',
      baseUrl: '/api/v1'
    });
  });
  
  // Handle OPTIONS preflight for network-config
  app.options('/api/network-config', (req, res) => {
    console.log('Handling OPTIONS preflight for network-config');
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-access-key, x-secret-key, AccessKey, SecretKey, Access-Control-Allow-Origin');
    res.status(200).end();
  });
  
  // Add a mock network-config endpoint
  app.post('/api/network-config', (req, res) => {
    console.log('Mock network-config endpoint called with data:', req.body);
    
    // Check for required fields
    const { apiGateway, accessKey, secretKey, orgId, assetId } = req.body;
    if (!apiGateway || !accessKey || !secretKey || !orgId || !assetId) {
      console.log('Missing required fields in request');
      return res.status(400).json({
        success: false,
        error: 'Missing required fields',
        details: 'apiGateway, accessKey, secretKey, orgId, and assetId are required'
      });
    }
    
    // Return a mock network configuration
    res.status(200).json({
      success: true,
      status: 'completed',
      networks: ['BACnet/IP', 'Modbus TCP', 'KNX/IP']
    });
  });
  
  // Handle OPTIONS preflight for discover-devices
  app.options('/api/discover-devices', (req, res) => {
    console.log('Handling OPTIONS preflight for discover-devices');
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-access-key, x-secret-key, AccessKey, SecretKey');
    res.status(200).end();
  });
  
  // Add a mock discover-devices endpoint
  app.post('/api/discover-devices', (req, res) => {
    console.log('Mock discover-devices endpoint called with data:', req.body);
    
    // Return a mock task ID
    res.status(202).json({
      message: "Device discovery initiated",
      task_id: "discovery-mock" + Date.now(),
      status: "processing"
    });
  });
  
  // Handle OPTIONS preflight for fetch-points
  app.options('/api/fetch-points', (req, res) => {
    console.log('Handling OPTIONS preflight for fetch-points');
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-access-key, x-secret-key, AccessKey, SecretKey, Access-Control-Allow-Origin');
    res.status(200).end();
  });
  
  // Handle OPTIONS preflight for map-points
  app.options('/api/bms/map-points', (req, res) => {
    console.log('Handling OPTIONS preflight for map-points');
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-access-key, x-secret-key, AccessKey, SecretKey, Access-Control-Allow-Origin');
    res.status(200).end();
  });
  
  // Add a mock fetch-points endpoint
  app.post('/api/fetch-points', (req, res) => {
    console.log('Mock fetch-points endpoint called with data:', req.body);
    
    // Return a mock response with some points
    res.status(200).json({
      success: true,
      status: 'completed',
      record: [
        {
          id: 'point1',
          pointName: 'AHU-1 Supply Temp',
          pointType: 'Temperature',
          unit: '°C',
          description: 'Supply air temperature sensor'
        },
        {
          id: 'point2',
          pointName: 'AHU-1 Return Temp',
          pointType: 'Temperature',
          unit: '°C',
          description: 'Return air temperature sensor'
        }
      ],
      totalCount: 2,
      hasMore: false
    });
  });
  
  // Add a mock map-points endpoint with improved implementation
  app.post('/api/bms/map-points', (req, res) => {
    console.log('Mock map-points endpoint called with data (IMPROVED IMPLEMENTATION)');
    console.log('Number of points:', req.body.points?.length || 0);
    
    const { points, matchingStrategy, confidence } = req.body;
    // targetSchema is unused but kept here for reference
    
    // Enhanced HVAC equipment type mapping templates
    const hvacEquipmentTypes = {
      "ahu": "AHU",
      "vav": "VAV",
      "fcu": "FCU",
      "pump": "PUMP",
      "fan": "FAN",
      "damper": "DAMPER",
      "valve": "VALVE",
      "chiller": "CHILLER",
      "boiler": "BOILER",
      "rtu": "RTU",
      "ctu": "CTU",
      "controller": "CONTROLLER"
    };
    
    // Map point types to likely equipment type when not specified
    const pointTypeToEquipmentMap = {
      "temperature": "AHU",
      "temp": "AHU",
      "humidity": "AHU",
      "pressure": "AHU",
      "flow": "VAV",
      "speed": "FCU",
      "status": "CONTROLLER",
      "setpoint": "CONTROLLER",
      "sp": "CONTROLLER",
      "cooling": "CHILLER",
      "heating": "BOILER"
    };
    
    // First, group points by deviceId
    const deviceGroups = {};
    
    // Process each point to extract/infer deviceId and deviceType
    (points || []).forEach(point => {
      const pointName = point.pointName || '';
      const pointNameLower = pointName.toLowerCase();
      
      // Try to extract deviceId from point name using common patterns
      let deviceId = point.deviceId || '';
      if (!deviceId) {
        // Look for common patterns like AHU-01, FCU_02, etc.
        const devicePatterns = [
          /([A-Za-z]+)[-_]?(\d+)/,         // Match AHU-01, VAV_23, etc.
          /([A-Za-z]+)(\d+)/,               // Match AHU01, FCU2, etc.
          /([A-Za-z]+)[-_]?(\d+)[-_]?(\d+)/ // Match AHU-01-02, FCU_01_23, etc.
        ];
        
        for (const pattern of devicePatterns) {
          const match = pointNameLower.match(pattern);
          if (match) {
            // Use the full match as deviceId
            const prefix = match[1].toUpperCase(); // e.g., "AHU"
            const number = match[2]; // e.g., "01"
            deviceId = `${prefix}-${number}`;
            break;
          }
        }
      }
      
      // If still no deviceId, use a fallback
      if (!deviceId) {
        deviceId = "UNKNOWN";
      }
      
      // Determine HVAC equipment type
      let equipmentType = point.deviceType || '';
      
      // If equipment type is provided, normalize it
      if (equipmentType) {
        const equipTypeLower = equipmentType.toLowerCase();
        for (const [key, value] of Object.entries(hvacEquipmentTypes)) {
          if (equipTypeLower.includes(key)) {
            equipmentType = value;
            break;
          }
        }
      } 
      // If not provided, try to infer from deviceId
      else if (deviceId !== "UNKNOWN") {
        const deviceIdParts = deviceId.split(/[-_]/)[0].toLowerCase();
        for (const [key, value] of Object.entries(hvacEquipmentTypes)) {
          if (deviceIdParts.includes(key)) {
            equipmentType = value;
            break;
          }
        }
      }
      
      // If still no equipment type, try to infer from point properties
      if (!equipmentType) {
        const pointType = (point.pointType || '').toLowerCase();
        
        // Check point type
        for (const [key, value] of Object.entries(pointTypeToEquipmentMap)) {
          if (pointType.includes(key) || pointNameLower.includes(key)) {
            equipmentType = value;
            break;
          }
        }
      }
      
      // Last resort fallback
      if (!equipmentType) {
        equipmentType = "UNKNOWN";
      }
      
      // Create a device group key
      const deviceKey = `${equipmentType}-${deviceId}`;
      
      // Add to device groups
      if (!deviceGroups[deviceKey]) {
        deviceGroups[deviceKey] = {
          deviceId: deviceId,
          equipmentType: equipmentType,
          points: []
        };
      }
      
      deviceGroups[deviceKey].points.push(point);
    });
    
    // Now map each point with its device context
    const mappings = [];
    
    Object.values(deviceGroups).forEach(group => {
      const { deviceId, equipmentType, points } = group;
      
      // Create EnOS model base path for this device
      const enosBasePath = `${equipmentType}/${deviceId}`;
      
      // Map each point in this device group
      points.forEach(point => {
        const pointId = point.id || '';
        const pointName = point.pointName || '';
        const pointType = point.pointType || '';
        const unit = point.unit || '';
        
        // Determine point category and subpath based on point name/type
        const pointNameLower = pointName.toLowerCase();
        let pointCategory = 'generic';
        let mappingConfidence = 0.75;
        
        // Temperature patterns
        if (pointNameLower.includes("temp") || pointNameLower.includes("tmp") || 
            (pointType || '').toLowerCase().includes("temp")) {
          mappingConfidence = 0.9;
          if (pointNameLower.includes("supply") || pointNameLower.includes("sa") || 
              pointNameLower.includes("sat") || pointNameLower.includes("discharge")) {
            pointCategory = 'supplyTemperature';
            mappingConfidence = 0.95;
          } else if (pointNameLower.includes("return") || pointNameLower.includes("ra") || 
                     pointNameLower.includes("rat")) {
            pointCategory = 'returnTemperature';
            mappingConfidence = 0.95;
          } else if (pointNameLower.includes("out") || pointNameLower.includes("oa") || 
                     pointNameLower.includes("oat") || pointNameLower.includes("ambient")) {
            pointCategory = 'outdoorTemperature';
            mappingConfidence = 0.93;
          } else if (pointNameLower.includes("zone") || pointNameLower.includes("room") || 
                     pointNameLower.includes("space")) {
            pointCategory = 'zoneTemperature';
            mappingConfidence = 0.94;
          } else {
            pointCategory = 'temperature';
          }
        } 
        // Humidity patterns
        else if (pointNameLower.includes("hum") || pointNameLower.includes("rh") || 
                (pointType || '').toLowerCase().includes("humid")) {
          pointCategory = 'humidity';
          mappingConfidence = 0.92;
        } 
        // Pressure patterns
        else if (pointNameLower.includes("press") || pointNameLower.includes("pres") || 
                (pointType || '').toLowerCase().includes("press")) {
          pointCategory = 'pressure';
          mappingConfidence = 0.88;
        } 
        // Flow patterns
        else if (pointNameLower.includes("flow") || pointNameLower.includes("cfm") || 
                (pointType || '').toLowerCase().includes("flow")) {
          pointCategory = 'airflow';
          mappingConfidence = 0.87;
        } 
        // Fan patterns
        else if (pointNameLower.includes("fan") || 
                (pointType || '').toLowerCase().includes("fan")) {
          if (pointNameLower.includes("status") || pointNameLower.includes("state") || 
              pointNameLower.includes("on") || pointNameLower.includes("off")) {
            pointCategory = 'fanStatus';
            mappingConfidence = 0.93;
          } else if (pointNameLower.includes("speed") || pointNameLower.includes("freq")) {
            pointCategory = 'fanSpeed';
            mappingConfidence = 0.92;
          } else {
            pointCategory = 'fan';
            mappingConfidence = 0.85;
          }
        } 
        // Damper patterns
        else if (pointNameLower.includes("damp") || 
                (pointType || '').toLowerCase().includes("damper")) {
          pointCategory = 'damperPosition';
          mappingConfidence = 0.91;
        }
        // Valve patterns
        else if (pointNameLower.includes("valve") || 
                (pointType || '').toLowerCase().includes("valve")) {
          pointCategory = 'valvePosition';
          mappingConfidence = 0.90;
        }
        // Status patterns
        else if (pointNameLower.includes("status") || pointNameLower.includes("state") || 
                pointNameLower.includes("on") || pointNameLower.includes("off") ||
                (pointType || '').toLowerCase().includes("status")) {
          pointCategory = 'status';
          mappingConfidence = 0.84;
        } 
        // Setpoint patterns
        else if (pointNameLower.includes("set") || pointNameLower.includes("sp") || 
                (pointType || '').toLowerCase().includes("setpoint")) {
          pointCategory = 'setpoint';
          if (pointNameLower.includes("temp")) {
            pointCategory = 'temperatureSetpoint';
            mappingConfidence = 0.92;
          } else if (pointNameLower.includes("flow")) {
            pointCategory = 'flowSetpoint';
            mappingConfidence = 0.91;
          } else if (pointNameLower.includes("press")) {
            pointCategory = 'pressureSetpoint';
            mappingConfidence = 0.91;
          } else {
            mappingConfidence = 0.89;
          }
        }
        
        // Construct the EnOS path for this point
        const enosPath = `${enosBasePath}/points/${pointCategory}`;
        
        // Create the mapping result
        mappings.push({
          pointId,
          pointName,
          pointType,
          unit,
          deviceId,
          deviceType: equipmentType,
          pointCategory,
          enosPath,
          confidence: Math.min(mappingConfidence, confidence || 0.85),
          mappingSource: matchingStrategy || 'ai',
          status: 'mapped'
        });
      });
    });
    
    // Log a sample of the mappings and device groups
    if (mappings.length > 0) {
      console.log('Sample mapping:', mappings[0]);
      console.log('Number of device groups:', Object.keys(deviceGroups).length);
      console.log('Device groups:', Object.keys(deviceGroups));
    }
    
    // Return a mock mapping response with detailed statistics
    res.status(200).json({
      success: true,
      status: 'completed',
      mappings: mappings,
      statistics: {
        total: points?.length || 0,
        mapped: mappings.length,
        unmapped: 0,
        errors: 0,
        timeouts: 0,
        deviceCount: Object.keys(deviceGroups).length,
        deviceTypes: [...new Set(Object.values(deviceGroups).map(g => g.equipmentType))].length,
        confidenceAvg: mappings.reduce((sum, m) => sum + m.confidence, 0) / (mappings.length || 1)
      },
      // targetSchema removed to fix lint warning
    });
  });
  
  // Handle v1 API endpoints
  app.options('/api/v1/*', (req, res) => {
    console.log('Handling OPTIONS preflight for v1 API:', req.path);
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-access-key, x-secret-key, AccessKey, SecretKey');
    res.status(200).end();
  });
  
  // Add v1 endpoints for networks
  app.post('/api/v1/networks', (req, res) => {
    console.log('Mock v1 networks endpoint called with data:', req.body);
    
    // Check for required fields
    const { apiGateway, accessKey, secretKey, orgId, assetId } = req.body;
    if (!apiGateway || !accessKey || !secretKey || !orgId || !assetId) {
      console.log('Missing required fields in request');
      return res.status(400).json({
        status: 'error',
        message: 'Missing required fields',
        details: 'apiGateway, accessKey, secretKey, orgId, and assetId are required'
      });
    }
    
    // Return a mock network configuration
    res.status(200).json({
      status: 'success',
      networks: [
        {
          id: 'network-1',
          name: 'BACnet/IP',
          description: 'BACnet/IP Network',
          ipAddress: '192.168.1.0/24',
          macAddress: '00:11:22:33:44:55',
          isActive: true
        },
        {
          id: 'network-2',
          name: 'Modbus TCP',
          description: 'Modbus TCP Network',
          ipAddress: '192.168.2.0/24',
          macAddress: '00:11:22:33:44:66',
          isActive: true
        }
      ]
    });
  });
  
  // Add v1 endpoints for device discovery
  app.post('/api/v1/devices/discover', (req, res) => {
    console.log('Mock v1 devices/discover endpoint called with data:', req.body);
    
    // Return a mock task ID
    res.status(202).json({
      status: 'processing',
      taskId: 'discovery-' + Date.now().toString(36),
      message: 'Device discovery initiated'
    });
  });
  
  // Add v1 endpoint for checking device discovery status
  app.get('/api/v1/devices/discover/:taskId', (req, res) => {
    console.log('Mock v1 device discovery status check for:', req.params.taskId);
    
    // Return a mock device list
    res.status(200).json({
      status: 'completed',
      result: {
        devices: [
          {
            instanceNumber: 1001,
            name: 'AHU-01',
            address: '192.168.1.101',
            model: 'JACE-8000',
            vendor: 'Tridium'
          },
          {
            instanceNumber: 1002,
            name: 'FCU-01',
            address: '192.168.1.102',
            model: 'JACE-8000',
            vendor: 'Tridium'
          }
        ],
        count: 2
      }
    });
  });
  
  // Add v1 endpoint for points search
  app.post('/api/v1/points/search', (req, res) => {
    console.log('Mock v1 points/search endpoint called with data:', req.body);
    
    // Return a mock task ID
    res.status(202).json({
      status: 'processing',
      taskId: 'search-' + Date.now().toString(36),
      message: 'Points search initiated'
    });
  });
  
  // Add v1 endpoint for task status checking
  app.get('/api/v1/tasks/:taskId', (req, res) => {
    console.log('Mock v1 task status check for:', req.params.taskId);
    const taskId = req.params.taskId;
    
    if (taskId.startsWith('search-')) {
      // Return a mock points search status
      res.status(200).json({
        status: 'completed',
        pointCount: 8,
        samplePoints: [
          {name: 'AHU01.SupplyTemp', value: 72.5, units: 'degF'},
          {name: 'AHU01.ReturnTemp', value: 75.0, units: 'degF'},
          {name: 'FCU01.SupplyTemp', value: 68.2, units: 'degF'}
        ]
      });
    } else if (taskId.startsWith('discovery-')) {
      // Return a mock device list
      res.status(200).json({
        status: 'completed',
        result: {
          devices: [
            {
              instanceNumber: 1001,
              name: 'AHU-01',
              address: '192.168.1.101'
            },
            {
              instanceNumber: 1002,
              name: 'FCU-01',
              address: '192.168.1.102'
            }
          ],
          count: 2
        }
      });
    } else {
      // Return a mock generic task status
      res.status(200).json({
        status: 'completed',
        result: {
          message: 'Task completed'
        }
      });
    }
  });
  
  // Add v1 endpoint for device points
  app.post('/api/v1/devices/:deviceId/points', (req, res) => {
    console.log(`Mock v1 device points for device ${req.params.deviceId} with data:`, req.body);
    
    // Return a mock task ID
    res.status(202).json({
      status: 'processing',
      taskId: `points-${req.params.deviceId}-` + Date.now().toString(36),
      message: `Fetching points for device ${req.params.deviceId}`
    });
  });
  
  // Add v1 endpoints for points grouping and mapping
  app.post('/api/v1/points/group', (req, res) => {
    console.log('Mock v1 points/group endpoint called with data:', req.body);
    
    const { points, useAi } = req.body;
    
    // Return a mock grouping result
    res.status(200).json({
      message: 'Points grouped successfully',
      groups: {
        AHU: {
          'AHU-01': ['AHU01.SupplyTemp', 'AHU01.ReturnTemp'],
          'AHU-02': ['AHU02.SupplyTemp', 'AHU02.ReturnTemp']
        },
        FCU: {
          'FCU-01': ['FCU01.SupplyTemp', 'FCU01.FanStatus']
        }
      },
      count: {
        totalPoints: points.length || 6,
        deviceTypes: 2,
        devices: 3
      },
      method: useAi ? 'ai' : 'pattern'
    });
  });
  
  app.post('/api/v1/points/map', (req, res) => {
    console.log('Mock v1 points/map endpoint called with data:', req.body);
    
    const { points, useAi } = req.body;
    
    // Return a mock mapping result
    res.status(200).json({
      message: 'Points mapped successfully',
      mappings: (points || []).map(point => ({
        ...point,
        enosPath: point.deviceType + '/points/temperature/zone',
        status: 'mapped'
      })),
      statistics: {
        total: points?.length || 4,
        mapped: points?.length || 4,
        unmapped: 0,
        errors: 0,
        timeouts: 0
      },
      method: useAi ? 'ai' : 'rule'
    });
  });
  
  // Handle preflight OPTIONS requests directly for any other routes
  app.use((req, res, next) => {
    if (req.method === 'OPTIONS') {
      console.log('Handling OPTIONS preflight request for:', req.path);
      res.header('Access-Control-Allow-Origin', '*');
      res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
      res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-access-key, x-secret-key, AccessKey, SecretKey, Access-Control-Allow-Origin');
      res.status(200).end();
      return;
    }
    next();
  });

  // Make sure our mock endpoint for map-points is used directly
  app.post('/api/bms/map-points', (req, res) => {
    console.log('*** Direct handler for /api/bms/map-points called ***');
    console.log('Number of points:', req.body.points?.length || 0);
    
    // This handler will override any attempted proxy to the backend
    // Execute the implementation defined above for this endpoint
    console.log('Delegating to mock implementation with EnOS paths...');
    
    const { points, matchingStrategy, confidence } = req.body;
    // targetSchema is unused but kept here for reference
    
    // EnOS equipment models from enos.json
    const enosModels = {
      "AHU": {
        "enos_model": "EnOS_HVAC_AHU",
        "points": {
          "supply_temp": "AHU_raw_supply_air_temp",
          "return_temp": "AHU_raw_return_air_temp",
          "outside_temp": "AHU_raw_outside_air_temp",
          "humidity": "AHU_raw_return_air_humidity",
          "pressure": "AHU_raw_static_pressure",
          "status": "AHU_raw_status",
          "speed": "AHU_raw_supply_air_fan_speed",
          "frequency": "AHU_raw_supply_air_fan_frequency",
          "damper": "AHU_raw_oa_damper_position",
          "valve": "AHU_raw_valve_position",
          "setpoint": "AHU_raw_sp_supply_air_temp"
        }
      },
      "FCU": {
        "enos_model": "EnOS_HVAC_FCU",
        "points": {
          "temp": "FCU_raw_zone_air_temp",
          "status": "FCU_raw_status",
          "speed": "FCU_raw_fan_speed",
          "valve": "FCU_raw_chw_valve_status",
          "setpoint": "FCU_raw_sp_zone_air_temp",
          "occupancy": "FCU_raw_zone_occupancy"
        }
      },
      "PUMP": {
        "enos_model": "EnOS_HVAC_PU",
        "points": {
          "status": "PUMP_raw_status",
          "power": "PUMP_raw_power_active_total",
          "flow": "PUMP_raw_flow",
          "pressure": "PUMP_raw_pressure"
        }
      },
      "CHILLER": {
        "enos_model": "EnOS_HVAC_CH",
        "points": {
          "status": "CH_raw_status",
          "supply_temp": "CH_raw_temp_chws",
          "return_temp": "CH_raw_temp_chwr",
          "power": "CH_raw_power_active_total",
          "energy": "CH_raw_energy_active_total"
        }
      }
    };
    
    // Enhanced HVAC equipment type mapping templates
    const hvacEquipmentTypes = {
      "ahu": "AHU",
      "vav": "AHU", // Map VAV to AHU for now
      "fcu": "FCU",
      "pump": "PUMP",
      "fan": "AHU", 
      "damper": "AHU",
      "valve": "AHU",
      "chiller": "CHILLER",
      "boiler": "PUMP", // Map boiler to pump for now
      "rtu": "AHU",  // Map RTU to AHU
      "ctu": "FCU",  // Map CTU to FCU
      "controller": "AHU"
    };
    
    // Process points and create mappings using the implementation from above
    // Group points by deviceId
    const deviceGroups = {};
    
    // Process each point
    (points || []).forEach(point => {
      const pointName = point.pointName || '';
      const pointNameLower = pointName.toLowerCase();
      
      // Try to extract deviceId from point name using patterns
      let deviceId = point.deviceId || '';
      if (!deviceId) {
        const devicePatterns = [
          /([A-Za-z]+)[-_]?(\d+)/,         // Match AHU-01, VAV_23, etc.
          /([A-Za-z]+)(\d+)/,               // Match AHU01, FCU2, etc.
          /([A-Za-z]+)[-_]?(\d+)[-_]?(\d+)/ // Match AHU-01-02, FCU_01_23, etc.
        ];
        
        for (const pattern of devicePatterns) {
          const match = pointNameLower.match(pattern);
          if (match) {
            const prefix = match[1].toUpperCase();
            const number = match[2];
            deviceId = `${prefix}-${number}`;
            break;
          }
        }
      }
      
      if (!deviceId) {
        deviceId = "UNKNOWN";
      }
      
      // Determine equipment type
      let equipmentType = point.deviceType || '';
      
      if (equipmentType) {
        const equipTypeLower = equipmentType.toLowerCase();
        for (const [key, value] of Object.entries(hvacEquipmentTypes)) {
          if (equipTypeLower.includes(key)) {
            equipmentType = value;
            break;
          }
        }
      } else if (deviceId !== "UNKNOWN") {
        const deviceIdParts = deviceId.split(/[-_]/)[0].toLowerCase();
        for (const [key, value] of Object.entries(hvacEquipmentTypes)) {
          if (deviceIdParts.includes(key)) {
            equipmentType = value;
            break;
          }
        }
      }
      
      // Default equipment type
      if (!equipmentType || !enosModels[equipmentType]) {
        equipmentType = "AHU";  // Default to AHU
      }
      
      // Create device group key
      const deviceKey = `${equipmentType}-${deviceId}`;
      
      // Add to device groups
      if (!deviceGroups[deviceKey]) {
        deviceGroups[deviceKey] = {
          deviceId: deviceId,
          equipmentType: equipmentType,
          points: []
        };
      }
      
      deviceGroups[deviceKey].points.push(point);
    });
    
    // Create mappings for each point
    const mappings = [];
    
    Object.values(deviceGroups).forEach(group => {
      const { deviceId, equipmentType, points } = group;
      
      // Get the EnOS model
      const model = enosModels[equipmentType] || enosModels.AHU;
      const enosModelName = model.enos_model;
      
      // Base EnOS path based on real EnOS equipment model
      const enosBase = `${enosModelName}/${deviceId}`;
      
      // Map each point in this device group
      points.forEach(point => {
        const pointId = point.id || '';
        const pointName = point.pointName || '';
        const pointType = point.pointType || '';
        const unit = point.unit || '';
        const pointNameLower = pointName.toLowerCase();
        
        // Determine the best EnOS point type based on point name
        let enosPointType = '';
        let mappingConfidence = 0.75;
        
        // Find the closest matching EnOS point type
        if (pointNameLower.includes("temp") || pointNameLower.includes("tmp")) {
          if (pointNameLower.includes("supply") || pointNameLower.includes("sa") || 
              pointNameLower.includes("sat") || pointNameLower.includes("discharge")) {
            enosPointType = model.points.supply_temp || 'AHU_raw_supply_air_temp';
            mappingConfidence = 0.95;
          } else if (pointNameLower.includes("return") || pointNameLower.includes("ra") || 
                     pointNameLower.includes("rat")) {
            enosPointType = model.points.return_temp || 'AHU_raw_return_air_temp';
            mappingConfidence = 0.95;
          } else if (pointNameLower.includes("out") || pointNameLower.includes("oa") || 
                     pointNameLower.includes("oat") || pointNameLower.includes("ambient")) {
            enosPointType = model.points.outside_temp || 'AHU_raw_outside_air_temp';
            mappingConfidence = 0.93;
          } else if (pointNameLower.includes("zone") || pointNameLower.includes("room") || 
                     pointNameLower.includes("space")) {
            enosPointType = model.points.temp || 'FCU_raw_zone_air_temp';
            mappingConfidence = 0.94;
          } else {
            enosPointType = model.points.supply_temp || 'AHU_raw_supply_air_temp';
            mappingConfidence = 0.9;
          }
        } else if (pointNameLower.includes("hum") || pointNameLower.includes("rh")) {
          enosPointType = model.points.humidity || 'AHU_raw_return_air_humidity';
          mappingConfidence = 0.92;
        } else if (pointNameLower.includes("press") || pointNameLower.includes("pres")) {
          enosPointType = model.points.pressure || 'AHU_raw_static_pressure';
          mappingConfidence = 0.88;
        } else if (pointNameLower.includes("flow")) {
          enosPointType = model.points.flow || 'AHU_raw_air_flow';
          mappingConfidence = 0.87;
        } else if (pointNameLower.includes("status") || pointNameLower.includes("state") ||
                  pointNameLower.includes("on") || pointNameLower.includes("off")) {
          enosPointType = model.points.status || 'AHU_raw_status';
          mappingConfidence = 0.90;
        } else if (pointNameLower.includes("speed")) {
          enosPointType = model.points.speed || 'AHU_raw_supply_air_fan_speed';
          mappingConfidence = 0.86;
        } else if (pointNameLower.includes("freq")) {
          enosPointType = model.points.frequency || 'AHU_raw_supply_air_fan_frequency';
          mappingConfidence = 0.86;
        } else if (pointNameLower.includes("damp")) {
          enosPointType = model.points.damper || 'AHU_raw_oa_damper_position';
          mappingConfidence = 0.88;
        } else if (pointNameLower.includes("valve")) {
          enosPointType = model.points.valve || 'AHU_raw_valve_position';
          mappingConfidence = 0.88;
        } else if (pointNameLower.includes("set") || pointNameLower.includes("sp")) {
          enosPointType = model.points.setpoint || 'AHU_raw_sp_supply_air_temp';
          mappingConfidence = 0.85;
        } else if (pointNameLower.includes("power")) {
          enosPointType = model.points.power || 'AHU_raw_power_active_total';
          mappingConfidence = 0.85;
        } else if (pointNameLower.includes("energy")) {
          enosPointType = model.points.energy || 'AHU_raw_energy_active_total';
          mappingConfidence = 0.85;
        } else if (pointNameLower.includes("occup")) {
          enosPointType = model.points.occupancy || 'FCU_raw_zone_occupancy';
          mappingConfidence = 0.85;
        } else {
          // Default to status if no match found
          enosPointType = model.points.status || 'AHU_raw_status';
          mappingConfidence = 0.75;
        }
        
        // Construct proper EnOS path based on the model structure
        const enosPath = `${enosBase}/${enosPointType}`;
        const pointCategory = enosPointType.split('_').pop() || 'generic';
        
        // Create mapping result
        mappings.push({
          pointId: pointId,
          pointName: pointName,
          pointType: pointType,
          unit: unit,
          deviceId: deviceId,
          deviceType: equipmentType,
          pointCategory: pointCategory,
          enosPath: enosPath,
          confidence: Math.min(mappingConfidence, confidence || 0.85),
          mappingSource: matchingStrategy || 'ai',
          status: 'mapped',
          enosModel: enosModelName
        });
      });
    });
    
    // Log sample mapping
    console.log('Device groups count:', Object.keys(deviceGroups).length);
    console.log('Mappings created:', mappings.length);
    if (mappings.length > 0) {
      console.log('Sample mapping:', mappings[0]);
    }
    
    // Return response
    res.status(200).json({
      success: true,
      status: 'completed',
      mappings: mappings,
      statistics: {
        total: points?.length || 0,
        mapped: mappings.length,
        unmapped: 0,
        errors: 0,
        timeouts: 0,
        deviceCount: Object.keys(deviceGroups).length,
        deviceTypes: [...new Set(Object.values(deviceGroups).map(g => g.equipmentType))].length
      }
    });
  });

  // For all other API requests, proxy to the backend
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:5000',
      changeOrigin: true,
      secure: false,
      pathRewrite: {
        '^/api': '/api'
      },
      // Don't proxy these endpoints - use our mock handlers instead
      filter: function(path, req) {
        return !path.includes('/api/bms/map-points');
      },
      onProxyReq: function(proxyReq, req, res) {
        // Remove the Access-Control-Allow-Origin header from the request as it's invalid
        proxyReq.removeHeader('Access-Control-Allow-Origin');
      },
      onProxyRes: function (proxyRes, req, res) {
        proxyRes.headers['Access-Control-Allow-Origin'] = '*';
        proxyRes.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, x-access-key, x-secret-key, AccessKey, SecretKey, Access-Control-Allow-Origin';
      },
      onError: function(err, req, res) {
        console.log('Proxy error:', err);
        
        // If the target connection fails, we need to handle it gracefully
        // Check which endpoint was requested
        if (req.path.includes('/bms/map-points')) {
          // Return a helpful error
          res.status(500).json({
            success: false,
            error: `Backend connection failed: ${err.message}`,
            message: "Using mock data instead"
          });
        } else {
          // Default error response
          res.status(500).json({
            success: false,
            error: `Proxy error: ${err.message}`
          });
        }
      }
    })
  );
}; 