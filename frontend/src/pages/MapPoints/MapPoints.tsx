import * as React from 'react';
import { useState, useEffect, useRef } from 'react';
import { Card } from '../../components';
import { HotTable } from '@handsontable/react';
import { registerAllModules } from 'handsontable/registry';
import type { GridSettings } from 'handsontable/settings';
import Handsontable from 'handsontable';
import type { CellProperties } from 'handsontable/settings';
import 'handsontable/dist/handsontable.full.css';
import { useMappingContext } from '../../contexts/MappingContext';
import { BMSPoint, PointMapping } from '../../types/apiTypes';
import { useBMSClient } from '../../hooks/useBMSClient';
import './MapPoints.css';

// Define a custom interface for the ref to avoid TypeScript errors
interface HotTableRefType {
  hotInstance?: Handsontable;
}

// Register all Handsontable modules
registerAllModules();

/**
 * MapPoints page component
 * Allows users to map grouped HVAC device points to EnOS model points
 */
const MapPoints: React.FC = () => {
  const [points, setPoints] = useState<BMSPoint[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isMapping, setIsMapping] = useState<boolean>(false);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  // Using a mutable ref object to track the hot instance
  const hotInstanceRef = useRef<Handsontable | null>(null);
  
  const { mappings, setMappings, setFilename } = useMappingContext();
  const bmsClient = useBMSClient();

  // Handle file upload
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setIsLoading(true);
    setSelectedFile(file);
    const fileExtension = file.name.split('.').pop()?.toLowerCase();

    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        let parsedData: BMSPoint[] = [];

        if (fileExtension === 'csv') {
          parsedData = parseCSV(content);
        } else if (fileExtension === 'json') {
          parsedData = JSON.parse(content);
          
          if (!Array.isArray(parsedData)) {
            throw new Error('JSON must contain an array of points');
          }
        } else {
          throw new Error('Unsupported file format. Please upload CSV or JSON files only.');
        }

        setPoints(parsedData);
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Failed to parse file');
        setPoints([]);
      } finally {
        setIsLoading(false);
      }
    };

    reader.onerror = () => {
      setError('Error reading file');
      setIsLoading(false);
    };

    if (fileExtension === 'csv' || fileExtension === 'json') {
      reader.readAsText(file);
    } else {
      setError('Unsupported file format. Please upload CSV or JSON files only.');
      setIsLoading(false);
    }
  };

  // Parse CSV content
  const parseCSV = (csvText: string): BMSPoint[] => {
    const lines = csvText.split('\n');
    if (lines.length <= 1) {
      throw new Error('CSV file appears to be empty or has only headers');
    }

    const headers = lines[0].split(',').map(header => header.trim());
    
    return lines.slice(1).filter(line => line.trim() !== '').map((line, index) => {
      // Handle potential commas inside quoted values
      const values: string[] = [];
      let isInQuotes = false;
      let currentValue = '';
      
      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') {
          isInQuotes = !isInQuotes;
          currentValue += char;
        } else if (char === ',' && !isInQuotes) {
          values.push(currentValue.trim());
          currentValue = '';
        } else {
          currentValue += char;
        }
      }
      
      // Add the last value
      values.push(currentValue.trim());
      
      // Create point object from CSV values
      const point: Record<string, any> = {};
      
      headers.forEach((header, idx) => {
        const value = values[idx] || '';
        
        // Remove quotes if they completely wrap the value
        let cleanValue = value;
        if (cleanValue.startsWith('"') && cleanValue.endsWith('"') && cleanValue.length >= 2) {
          cleanValue = cleanValue.substring(1, cleanValue.length - 1);
        }
        
        point[header] = cleanValue;
      });
      
      // Ensure minimum fields for BMSPoint
      return {
        id: point.id || point.pointId || `point-${index}`,
        pointName: point.pointName || point.objectName || '',
        pointType: point.pointType || point.objectType || '',
        unit: point.unit || '',
        description: point.description || '',
        deviceType: point.deviceType || '',
        deviceId: point.deviceId || ''
      } as BMSPoint;
    });
  };

  // Load data when component mounts
  useEffect(() => {
    // Set loading to false initially
    setIsLoading(false);
  }, []);
  
  // Update table data when pagination changes
  useEffect(() => {
    if (hotInstanceRef.current) {
      hotInstanceRef.current.loadData(getPagedData());
    }
  }, [currentPage, pageSize, points.length]);

  // Map points to EnOS using backend enos.json definitions
  const handleMapPoints = async () => {
    if (points.length === 0) {
      setError('Please upload points data first');
      return;
    }

    try {
      setIsMapping(true);
      setError(null);
      
      // Use the backend API for mapping which refers to backend/enos.json
      console.log(`Sending ${points.length} points to backend for EnOS mapping using enos.json definitions`);

      // Call the backend API to map points with special options to use the enos.json file
      const response = await bmsClient.mapPointsToEnOS(points, {
        targetSchema: 'enos', // Specify to use the EnOS schema from backend/enos.json
        matchingStrategy: 'ai' // Use AI-powered matching for best results
      });
      
      if (response.success && response.mappings && response.mappings.length > 0) {
        // Convert API response to PointMapping format for the UI
        const newMappings: PointMapping[] = response.mappings.map(mapping => {
          // Extract just the point name without device prefixes
          const pointNameParts = mapping.pointName.split('.');
          const pointName = pointNameParts.length > 1 ? pointNameParts[pointNameParts.length - 1] : mapping.pointName;
          
          return {
            enosEntity: mapping.deviceType || 'hvac',
            enosPoint: mapping.pointCategory || 'unknown',
            rawPoint: mapping.pointName,
            pointName: pointName,
            rawUnit: mapping.unit || '',
            rawFactor: 1,
            enosPath: mapping.enosPath || '',
            deviceId: mapping.deviceId || '',
            confidence: mapping.confidence || 0.5
          };
        });
        
        console.log(`Backend mapped ${newMappings.length} points successfully to EnOS schema`);
        setMappings(newMappings);
        
        // If the mapping succeeded but no points were returned, display a warning
        if (newMappings.length === 0) {
          setError('No points could be mapped. Check your data or try again.');
        }
      } else {
        // Handle mapping failure
        const errorMsg = response.error || 'Failed to map points with backend service';
        throw new Error(errorMsg);
      }
    } catch (err) {
      console.error('EnOS mapping error:', err);
      setError(err instanceof Error ? err.message : 'Failed to map points to EnOS');
      
      // In case of an error, we can still try to use local mapping as a fallback
      try {
        console.log('Attempting local mapping as fallback due to backend error');
        
        // Local mapping logic using knowledge of enos.json structure
        const fallbackMappings: PointMapping[] = points.map(point => {
          // Extract device type from point name
          const pointNameParts = point.pointName.split(/[-_.]/);
          let deviceType = pointNameParts[0].toUpperCase() || 'UNKNOWN';
          
          // Normalize device types to match enos.json
          if (deviceType === 'AHU' || deviceType === 'MAU' || deviceType === 'RTU') {
            deviceType = 'AHU'; // Map to Air Handling Unit
          } else if (deviceType === 'FCU' || deviceType === 'FAN') {
            deviceType = 'FCU'; // Map to Fan Coil Unit
          } else if (deviceType === 'CH' || deviceType === 'CHLR') {
            deviceType = 'CH'; // Map to Chiller
          } else if (deviceType === 'CT') {
            deviceType = 'CT'; // Cooling Tower
          } else if (deviceType.includes('PUMP') || deviceType === 'PMP') {
            deviceType = 'PUMP'; // Map to Pump
          }
          
          // Extract device ID if available
          let deviceId = '';
          if (pointNameParts.length > 1) {
            deviceId = pointNameParts[1];
            if (pointNameParts.length > 2 && !pointNameParts[1].match(/^\d+$/)) {
              deviceId += '-' + pointNameParts[2];
            }
          }
          
          // Determine point category and EnOS path based on the point name
          const pointNameLower = point.pointName.toLowerCase();
          let pointCategory = 'generic';
          let enosPath = '';
          let confidence = 0.75;
          
          // Extract the actual point name from the full string (e.g., "CTL_FanSpeed" from "FCU_01_26.27_3.CTL_FanSpeed")
          let specificPointName = '';
          if (pointNameParts.length > 1) {
            // Assuming the actual point identifier is the last part after the last dot or underscore
            const lastPartMatch = point.pointName.match(/[._]([^._]+)$/);
            if (lastPartMatch && lastPartMatch[1]) {
              specificPointName = lastPartMatch[1].toLowerCase();
            } else {
              specificPointName = pointNameParts[pointNameParts.length - 1].toLowerCase();
            }
          }
          
          // Extract actual point name for more accurate mapping
          
          // Map to specific EnOS paths from the enos.json file
          if (deviceType === 'AHU') {
            // Handle specific AHU point naming patterns
            if (specificPointName.includes('status') || specificPointName === 'on' || specificPointName === 'off' || specificPointName === 'run') {
              enosPath = 'AHU_raw_status';
              pointCategory = 'status';
              confidence = 0.95;
            } else if (specificPointName.includes('supplytemp') || specificPointName.includes('satemp') || specificPointName === 'sat') {
              enosPath = 'AHU_raw_supply_air_temp';
              pointCategory = 'supplyTemperature';
              confidence = 0.95;
            } else if (specificPointName.includes('returntemp') || specificPointName.includes('ratemp') || specificPointName === 'rat') {
              enosPath = 'AHU_raw_return_air_temp';
              pointCategory = 'returnTemperature';
              confidence = 0.95;
            } else if (specificPointName.includes('staticpressure') || specificPointName.includes('statpr') || specificPointName === 'sp') {
              enosPath = 'AHU_raw_static_pressure';
              pointCategory = 'staticPressure';
              confidence = 0.95;
            } else if (specificPointName.includes('fanspeed') || specificPointName === 'speed' || specificPointName === 'safspeed') {
              enosPath = 'AHU_raw_supply_air_fan_speed';
              pointCategory = 'fanSpeed';
              confidence = 0.95;
            } else if (specificPointName.includes('damper') || specificPointName === 'dmpr' || specificPointName === 'oadmpr') {
              enosPath = 'AHU_raw_oa_damper_position';
              pointCategory = 'damperPosition';
              confidence = 0.95;
            } else if (specificPointName.includes('valve') || specificPointName === 'vlv') {
              enosPath = 'AHU_raw_valve_position';
              pointCategory = 'valvePosition';
              confidence = 0.95;
            } else if (specificPointName.includes('fancommand') || specificPointName === 'fanctrl') {
              enosPath = 'AHU_write_fan_speed';
              pointCategory = 'fanControl';
              confidence = 0.95;
            }
            // Fall back to checking the full name if specific point name didn't match
            else if (pointNameLower.includes('status') || pointNameLower.includes('on_off')) {
              enosPath = 'AHU_raw_status';
              pointCategory = 'status';
              confidence = 0.9;
            } else if (pointNameLower.includes('temp') && pointNameLower.includes('supply')) {
              enosPath = 'AHU_raw_supply_air_temp';
              pointCategory = 'supplyTemperature';
              confidence = 0.9;
            } else if (pointNameLower.includes('temp') && pointNameLower.includes('return')) {
              enosPath = 'AHU_raw_return_air_temp';
              pointCategory = 'returnTemperature';
              confidence = 0.9;
            } else if (pointNameLower.includes('static') && pointNameLower.includes('pressure')) {
              enosPath = 'AHU_raw_static_pressure';
              pointCategory = 'staticPressure';
              confidence = 0.85;
            } else if (pointNameLower.includes('fan') && pointNameLower.includes('speed')) {
              enosPath = 'AHU_raw_supply_air_fan_speed';
              pointCategory = 'fanSpeed';
              confidence = 0.85;
            }
          } else if (deviceType === 'FCU') {
            // Handle specific FCU point naming patterns like FCU_01_26.27_3.CTL_FanSpeed -> FCU_write_fan_speed
            if (specificPointName === 'fanspeed' || specificPointName === 'ctl_fanspeed') {
              enosPath = 'FCU_write_fan_speed';
              pointCategory = 'fanControl';
              confidence = 0.98;
            } else if (specificPointName === 'roomtemp' || specificPointName === 'zonetemp') {
              enosPath = 'FCU_raw_zone_air_temp';
              pointCategory = 'zoneTemperature';
              confidence = 0.98;
            } else if (specificPointName === 'status' || specificPointName === 'run') {
              enosPath = 'FCU_raw_status';
              pointCategory = 'status';
              confidence = 0.98;
            } else if (specificPointName === 'setpoint' || specificPointName === 'sp' || specificPointName === 'tempsp') {
              enosPath = 'FCU_raw_sp_zone_air_temp';
              pointCategory = 'temperatureSetpoint';
              confidence = 0.98;
            } else if (specificPointName === 'chwvalve' || specificPointName === 'coolingvalve') {
              enosPath = 'FCU_raw_chw_valve_status';
              pointCategory = 'valvePosition';
              confidence = 0.98;
            } else if (specificPointName === 'hwvalve' || specificPointName === 'heatingvalve') {
              enosPath = 'FCU_raw_hw_valve_status';
              pointCategory = 'valvePosition';
              confidence = 0.98;
            } else if (specificPointName === 'mode' || specificPointName === 'coolheatmode') {
              enosPath = 'FCU_raw_cooling_heating_mode';
              pointCategory = 'mode';
              confidence = 0.98;
            } else if (specificPointName === 'command' || specificPointName === 'onoffcmd') {
              enosPath = 'FCU_raw_on_off_command';
              pointCategory = 'command';
              confidence = 0.98;
            }
            // Fall back to checking the full name if specific point name didn't match
            else if (pointNameLower.includes('status') || pointNameLower.includes('on_off')) {
              enosPath = 'FCU_raw_status';
              pointCategory = 'status';
              confidence = 0.9;
            } else if (pointNameLower.includes('temp') && (pointNameLower.includes('zone') || pointNameLower.includes('room'))) {
              enosPath = 'FCU_raw_zone_air_temp';
              pointCategory = 'zoneTemperature';
              confidence = 0.9;
            } else if (pointNameLower.includes('setpoint') || pointNameLower.includes('sp')) {
              enosPath = 'FCU_raw_sp_zone_air_temp';
              pointCategory = 'temperatureSetpoint';
              confidence = 0.85;
            } else if (pointNameLower.includes('valve') && (pointNameLower.includes('cool') || pointNameLower.includes('chw'))) {
              enosPath = 'FCU_raw_chw_valve_status';
              pointCategory = 'valvePosition';
              confidence = 0.85;
            } else if (pointNameLower.includes('valve') && (pointNameLower.includes('heat') || pointNameLower.includes('hw'))) {
              enosPath = 'FCU_raw_hw_valve_status';
              pointCategory = 'valvePosition';
              confidence = 0.85;
            } else if (pointNameLower.includes('fan') && pointNameLower.includes('speed') && !pointNameLower.includes('cmd') && !pointNameLower.includes('ctl')) {
              enosPath = 'FCU_raw_fan_speed';
              pointCategory = 'fanSpeed';
              confidence = 0.85;
            } else if (pointNameLower.includes('fan') && (pointNameLower.includes('cmd') || pointNameLower.includes('ctl') || pointNameLower.includes('command'))) {
              enosPath = 'FCU_write_fan_speed';
              pointCategory = 'fanControl';
              confidence = 0.85;
            } else if (pointNameLower.includes('mode')) {
              enosPath = 'FCU_raw_cooling_heating_mode';
              pointCategory = 'mode';
              confidence = 0.8;
            }
          } else if (deviceType === 'CH') {
            // Handle specific Chiller point naming patterns
            if (specificPointName === 'status' || specificPointName === 'run') {
              enosPath = 'CH_raw_status';
              pointCategory = 'status';
              confidence = 0.98;
            } else if (specificPointName === 'trip' || specificPointName === 'fault' || specificPointName === 'alarm') {
              enosPath = 'CH_raw_trip';
              pointCategory = 'trip';
              confidence = 0.98;
            } else if (specificPointName === 'chwstemp' || specificPointName === 'supplytemp') {
              enosPath = 'CH_raw_temp_chws';
              pointCategory = 'supplyTemperature';
              confidence = 0.98;
            } else if (specificPointName === 'chwrtemp' || specificPointName === 'returntemp') {
              enosPath = 'CH_raw_temp_chwr';
              pointCategory = 'returnTemperature';
              confidence = 0.98;
            } else if (specificPointName === 'power' || specificPointName === 'kw') {
              enosPath = 'CH_raw_power_active_total';
              pointCategory = 'power';
              confidence = 0.98;
            } else if (specificPointName === 'energy' || specificPointName === 'kwh') {
              enosPath = 'CH_raw_energy_active_total';
              pointCategory = 'energy';
              confidence = 0.98;
            } else if (specificPointName === 'valve' || specificPointName === 'chwvalve') {
              enosPath = 'CH_raw_chilled_valve_status';
              pointCategory = 'valvePosition';
              confidence = 0.98;
            } else if (specificPointName === 'evaptemp') {
              enosPath = 'CH_raw_temp_evap';
              pointCategory = 'evaporatorTemperature';
              confidence = 0.98;
            } else if (specificPointName === 'condtemp') {
              enosPath = 'CH_raw_temp_cond';
              pointCategory = 'condenserTemperature';
              confidence = 0.98;
            }
            // Fall back to checking the full name if specific point name didn't match
            else if (pointNameLower.includes('status')) {
              enosPath = 'CH_raw_status';
              pointCategory = 'status';
              confidence = 0.9;
            } else if (pointNameLower.includes('trip') || pointNameLower.includes('fault')) {
              enosPath = 'CH_raw_trip';
              pointCategory = 'trip';
              confidence = 0.85;
            } else if (pointNameLower.includes('temp') && (pointNameLower.includes('chws') || pointNameLower.includes('supply'))) {
              enosPath = 'CH_raw_temp_chws';
              pointCategory = 'supplyTemperature';
              confidence = 0.9;
            } else if (pointNameLower.includes('temp') && (pointNameLower.includes('chwr') || pointNameLower.includes('return'))) {
              enosPath = 'CH_raw_temp_chwr';
              pointCategory = 'returnTemperature';
              confidence = 0.9;
            } else if (pointNameLower.includes('temp') && pointNameLower.includes('evap')) {
              enosPath = 'CH_raw_temp_evap';
              pointCategory = 'evaporatorTemperature';
              confidence = 0.9;
            } else if (pointNameLower.includes('temp') && pointNameLower.includes('cond')) {
              enosPath = 'CH_raw_temp_cond';
              pointCategory = 'condenserTemperature';
              confidence = 0.9;
            } else if (pointNameLower.includes('power')) {
              enosPath = 'CH_raw_power_active_total';
              pointCategory = 'power';
              confidence = 0.85;
            } else if (pointNameLower.includes('energy')) {
              enosPath = 'CH_raw_energy_active_total';
              pointCategory = 'energy';
              confidence = 0.85;
            } else if (pointNameLower.includes('valve')) {
              enosPath = 'CH_raw_chilled_valve_status';
              pointCategory = 'valvePosition';
              confidence = 0.8;
            }
          } else if (deviceType === 'PUMP') {
            // Handle specific Pump point naming patterns
            if (specificPointName === 'status' || specificPointName === 'run') {
              enosPath = 'PUMP_raw_status';
              pointCategory = 'status';
              confidence = 0.98;
            } else if (specificPointName === 'trip' || specificPointName === 'fault' || specificPointName === 'alarm') {
              enosPath = 'PUMP_raw_trip';
              pointCategory = 'trip';
              confidence = 0.98;
            } else if (specificPointName === 'power' || specificPointName === 'kw') {
              enosPath = 'PUMP_raw_power_active_total';
              pointCategory = 'power';
              confidence = 0.98;
            } else if (specificPointName === 'energy' || specificPointName === 'kwh') {
              enosPath = 'PUMP_raw_energy_active_total'; 
              pointCategory = 'energy';
              confidence = 0.98;
            } else if (specificPointName === 'flow' || specificPointName === 'flowrate') {
              enosPath = 'PUMP_raw_flow';
              pointCategory = 'flow';
              confidence = 0.98;
            } else if (specificPointName === 'pressure' || specificPointName === 'press') {
              enosPath = 'PUMP_raw_pressure';
              pointCategory = 'pressure';
              confidence = 0.98;
            }
            // Fall back to checking the full name if specific point name didn't match
            else if (pointNameLower.includes('status')) {
              enosPath = 'PUMP_raw_status';
              pointCategory = 'status';
              confidence = 0.9;
            } else if (pointNameLower.includes('trip') || pointNameLower.includes('fault')) {
              enosPath = 'PUMP_raw_trip';
              pointCategory = 'trip';
              confidence = 0.85;
            } else if (pointNameLower.includes('power')) {
              enosPath = 'PUMP_raw_power_active_total';
              pointCategory = 'power';
              confidence = 0.85;
            } else if (pointNameLower.includes('energy')) {
              enosPath = 'PUMP_raw_energy_active_total';
              pointCategory = 'energy';
              confidence = 0.85;
            } else if (pointNameLower.includes('flow')) {
              enosPath = 'PUMP_raw_flow';
              pointCategory = 'flow';
              confidence = 0.85;
            } else if (pointNameLower.includes('pressure')) {
              enosPath = 'PUMP_raw_pressure';
              pointCategory = 'pressure';
              confidence = 0.85;
            }
          }
          
          // If no specific mapping was found, create a generic one based on device type
          if (!enosPath) {
            if (deviceType === 'AHU') {
              enosPath = `AHU_raw_${pointCategory}`;
            } else if (deviceType === 'FCU') {
              enosPath = `FCU_raw_${pointCategory}`;
            } else if (deviceType === 'CH') {
              enosPath = `CH_raw_${pointCategory}`;
            } else if (deviceType === 'PUMP') {
              enosPath = `PUMP_raw_${pointCategory}`;
            } else {
              enosPath = `${deviceType}_raw_${pointCategory}`;
            }
            confidence = 0.5; // Lower confidence for generic mappings
          }
          
          return {
            enosEntity: deviceType,
            enosPoint: pointCategory,
            rawPoint: point.pointName,
            pointName: pointNameParts.length > 1 ? pointNameParts[pointNameParts.length - 1] : point.pointName,
            rawUnit: point.unit || '',
            rawFactor: 1,
            enosPath: enosPath,
            deviceId: deviceId,
            confidence: confidence
          };
        });
        
        setMappings(fallbackMappings);
        setError('Warning: Using local fallback mapping based on enos.json knowledge');
      } catch (fallbackErr) {
        console.error('Fallback mapping also failed:', fallbackErr);
        // If even the fallback fails, keep the original error message
      }
    } finally {
      setIsMapping(false);
    }
  };

  // Export mappings to CSV and apply to EnOS
  const exportMappingsToCSV = async () => {
    if (mappings.length === 0) {
      setError('No mappings to export');
      return;
    }

    try {
      setIsExporting(true);
      setError(null);

      const filename = selectedFile ? selectedFile.name.replace(/\.[^/.]+$/, '') + '_mapped' : 'points_mapping';
      setFilename(filename);

      // Convert our PointMapping objects to the format expected by the API
      const mappingData = mappings.map(mapping => ({
        enosEntity: mapping.enosEntity,
        enosPoint: mapping.enosPoint,
        rawPoint: mapping.rawPoint,
        rawUnit: mapping.rawUnit || '',
        rawFactor: mapping.rawFactor || 1
      }));

      // First, save the mapping to CSV
      const saveResponse = await bmsClient.saveMappingToCSV(mappingData, filename);

      if (!saveResponse.success) {
        throw new Error(saveResponse.error || 'Failed to save mappings to CSV');
      }

      // Then, export to EnOS
      const exportResponse = await bmsClient.exportMappingToEnOS(mappingData);
      
      if (!exportResponse.success) {
        throw new Error(exportResponse.error || 'Failed to apply mappings to EnOS');
      }

      // Create a download link for the CSV
      if (saveResponse.filepath) {
        const downloadUrl = bmsClient.getFileDownloadURL(saveResponse.filepath);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.setAttribute('download', `${filename}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
      
      // Show success message
      console.log(`Mappings exported to CSV and applied to EnOS successfully`);
      setError(null);
    } catch (err) {
      console.error('Export error:', err);
      setError(err instanceof Error ? err.message : 'Failed to export mappings');
    } finally {
      setIsExporting(false);
    }
  };

  // Get table columns and settings
  const getSettings = (): GridSettings => {
    const columns = [
      { data: 'pointName', title: 'Point Name', width: 200 },
      { data: 'pointType', title: 'Type', width: 100 },
      { data: 'deviceType', title: 'Device Type', width: 120 },
      { data: 'deviceId', title: 'Device ID', width: 120 },
      { data: 'unit', title: 'Unit', width: 80 },
      { data: 'description', title: 'Description', width: 200 },
      { 
        data: 'enosPath', 
        title: 'EnOS Mapping',
        width: 200,
        renderer: function(
          instance: Handsontable, 
          td: HTMLTableCellElement, 
          row: number, 
          col: number, 
          prop: string | number, 
          value: any, 
          cellProperties: CellProperties
        ) {
          if (value) {
            td.innerHTML = `<span class="mapping-badge">${value}</span>`;
          } else {
            td.innerHTML = '<span class="unmapped-badge">Unmapped</span>';
          }
          return td;
        }
      },
      { 
        data: 'confidence', 
        title: 'Confidence',
        width: 100,
        type: 'numeric',
        numericFormat: {
          pattern: '0.00'
        },
        renderer: function(
          instance: Handsontable, 
          td: HTMLTableCellElement, 
          row: number, 
          col: number, 
          prop: string | number, 
          value: any, 
          cellProperties: CellProperties
        ) {
          if (value) {
            const confValue = parseFloat(value);
            let className = 'low-confidence';
            
            if (confValue >= 0.9) {
              className = 'high-confidence';
            } else if (confValue >= 0.75) {
              className = 'medium-confidence';
            }
            
            td.innerHTML = `<span class="${className}">${(confValue * 100).toFixed(0)}%</span>`;
          } else {
            td.innerHTML = '-';
          }
          return td;
        }
      }
    ];

    // Get paginated data
    const paginatedData = getPagedData();

    return {
      data: paginatedData,
      columns,
      colHeaders: true,
      rowHeaders: true,
      height: 500,
      width: '100%',
      licenseKey: 'non-commercial-and-evaluation',
      stretchH: 'all',
      columnSorting: true,
      filters: true,
      dropdownMenu: true,
      readOnly: true,
      manualRowMove: false,
      contextMenu: ['row_above', 'row_below', 'remove_row', 'undo', 'redo'],
      wordWrap: true,
      className: 'htCenter'
    };
  };

  // Calculate total pages for pagination
  const totalPoints = points.length;
  const totalPages = Math.max(1, Math.ceil(totalPoints / pageSize));

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(Math.min(Math.max(1, page), totalPages));
    if (hotInstanceRef.current) {
      hotInstanceRef.current.loadData(getPagedData());
    }
  };

  // Update page size
  const handlePageSizeChange = (size: number) => {
    setPageSize(size);
    setCurrentPage(1);
    if (hotInstanceRef.current) {
      hotInstanceRef.current.loadData(getPagedData());
    }
  };
  
  // Helper to get the current page of data
  const getPagedData = () => {
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return points.slice(startIndex, endIndex);
  };

  return (
    <div className="map-points-container">
      <h1>Map Points to EnOS</h1>
      
      <Card className="upload-card">
        <h2>Upload Points</h2>
        <div className="file-upload-container">
          <input
            type="file"
            id="file-upload"
            onChange={handleFileUpload}
            accept=".csv,.json"
            disabled={isLoading}
            className="file-upload-input"
          />
          <label htmlFor="file-upload" className="file-upload-label">
            {isLoading ? 'Loading...' : 'Choose File'}
          </label>
          <span className="file-name">
            {selectedFile ? selectedFile.name : 'No file selected'}
          </span>
        </div>
        {error && <div className="error-message">{error}</div>}
      </Card>

      {points.length > 0 && (
        <Card className="points-card">
          <div className="card-header">
            <h2>Points Data</h2>
            <div className="action-buttons">
              <button
                className="primary-button"
                onClick={handleMapPoints}
                disabled={isMapping || points.length === 0}
              >
                {isMapping ? 'Mapping...' : 'Map to EnOS'}
              </button>
              <button
                className="secondary-button"
                onClick={exportMappingsToCSV}
                disabled={isExporting || mappings.length === 0}
              >
                {isExporting ? 'Exporting...' : 'Export & Apply to EnOS'}
              </button>
            </div>
          </div>

          <div className="pagination-container">
            <div className="pagination-controls">
              <label>
                Show
                <select
                  value={pageSize}
                  onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                  disabled={isLoading}
                >
                  <option value="10">10</option>
                  <option value="25">25</option>
                  <option value="50">50</option>
                  <option value="100">100</option>
                </select>
                entries
              </label>
            </div>
            <div className="pagination-buttons">
              <button
                onClick={() => handlePageChange(1)}
                disabled={currentPage === 1}
                className="pagination-button"
              >
                First
              </button>
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="pagination-button"
              >
                Previous
              </button>
              <span className="pagination-info">
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="pagination-button"
              >
                Next
              </button>
              <button
                onClick={() => handlePageChange(totalPages)}
                disabled={currentPage === totalPages}
                className="pagination-button"
              >
                Last
              </button>
            </div>
          </div>

          <div className="table-container">
            <HotTable
              ref={(ref: any) => { 
                if (ref) {
                  hotInstanceRef.current = ref.hotInstance;
                }
              }}
              settings={getSettings()}
            />
          </div>
        </Card>
      )}
    </div>
  );
};

export default MapPoints;