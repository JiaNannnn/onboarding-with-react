/**
 * Enhanced local mapping implementation for EnOS points
 * 
 * This implementation provides a comprehensive client-side mapping functionality
 * that maps BMS points to EnOS points based on device type and point name patterns.
 * It covers FCU, AHU, Chiller, Pump, Cooling Tower, and Chiller Plant device types.
 */

import { BMSPoint } from '../types/apiTypes';
import { MapPointsToEnOSResponse, MappingConfig } from '../api/bmsClient';

// Quality assessment for mapping results
export interface MappingQualityResult {
  mappingId: string;
  qualitySummary: {
    excellent: number;
    good: number;
    fair: number;
    poor: number;
    unacceptable: number;
  };
  pointsWithPoorQuality: Array<{
    pointId: string;
    pointName: string;
    mappingQuality: string;
    issues: string[];
  }>;
}

/**
 * Map BMS points to EnOS schema using enhanced local mapping only
 */
export function enhancedMapPointsToEnOS(
  points: BMSPoint[],
  mappingConfig: MappingConfig = {}
): Promise<MapPointsToEnOSResponse> {
  // Skip API call entirely and use pure local mapping
  console.log("Using enhanced local mapping to avoid backend issues");
  
  // Create a success response with locally mapped points
  const mappedPoints = points.map(point => {
    // Extract device type from point name (e.g., "FCU" from "FCU-B1-46A.RoomTemp")
    const pointNameParts = point.pointName.split(/[-_.]/);
    const deviceType = pointNameParts[0].toUpperCase();
    let deviceId = '';
    
    // Try to extract device ID (e.g., "B1-46A" from "FCU-B1-46A.RoomTemp")
    if (pointNameParts.length > 1) {
      deviceId = pointNameParts[1];
      if (pointNameParts.length > 2 && !pointNameParts[1].match(/^\d+$/)) {
        deviceId += '-' + pointNameParts[2];
      }
    }
    
    // Determine point category based on point name/type
    const pointNameLower = point.pointName.toLowerCase();
    let pointCategory = 'generic';
    // Note: confidence is no longer in the interface but we keep it for local processing
    let confidence = 0.75; 
    let enosPath = '';
    
    // Specialized mapping logic based on device type and point name
    switch (deviceType) {
      case 'FCU':
        if (pointNameLower.includes('temp') || pointNameLower.includes('tmp')) {
          if (pointNameLower.includes('zone') || pointNameLower.includes('room')) {
            pointCategory = 'zoneTemperature';
            confidence = 0.94;
            if (pointNameLower.includes('sp') || pointNameLower.includes('set')) {
              enosPath = 'FCU_raw_sp_zone_air_temp';
            } else {
              enosPath = 'FCU_raw_zone_air_temp';
            }
          } else if (pointNameLower.includes('supply')) {
            pointCategory = 'supplyTemperature';
            confidence = 0.92;
            enosPath = 'FCU_raw_supply_air_temp';
          }
        } else if (pointNameLower.includes('status') || pointNameLower.includes('state') || pointNameLower.includes('run')) {
          pointCategory = 'status';
          confidence = 0.93;
          enosPath = 'FCU_raw_status';
        } else if (pointNameLower.includes('trip') || pointNameLower.includes('fault') || pointNameLower.includes('alarm')) {
          pointCategory = 'status';
          confidence = 0.94;
          enosPath = 'FCU_raw_trip';
        } else if (pointNameLower.includes('mode')) {
          pointCategory = 'operationMode';
          confidence = 0.92;
          if (pointNameLower.includes('local')) {
            enosPath = 'FCU_raw_local_mode';
          } else if (pointNameLower.includes('cool') || pointNameLower.includes('heat')) {
            enosPath = 'FCU_raw_cooling_heating_mode';
          }
        } else if (pointNameLower.includes('valve')) {
          pointCategory = 'valvePosition';
          confidence = 0.92;
          if (pointNameLower.includes('cooling') || pointNameLower.includes('chw')) {
            enosPath = 'FCU_raw_chw_valve_status';
          } else if (pointNameLower.includes('heating') || pointNameLower.includes('hw')) {
            enosPath = 'FCU_raw_hw_valve_status';
          }
        } else if (pointNameLower.includes('fan') || pointNameLower.includes('speed')) {
          pointCategory = 'fanSpeed';
          confidence = 0.90;
          if (pointNameLower.includes('cmd') || pointNameLower.includes('command')) {
            enosPath = 'FCU_raw_fan_speed_command';
          } else {
            enosPath = 'FCU_raw_fan_speed';
          }
        } else if (pointNameLower.includes('power')) {
          pointCategory = 'power';
          confidence = 0.90;
          enosPath = 'FCU_raw_power_active_total';
        } else if (pointNameLower.includes('energy')) {
          pointCategory = 'energy';
          confidence = 0.90;
          enosPath = 'FCU_raw_energy_active_total';
        } else if (pointNameLower.includes('occup')) {
          pointCategory = 'occupancy';
          confidence = 0.90;
          enosPath = 'FCU_raw_zone_occupancy';
        } else if (pointNameLower.includes('co2')) {
          pointCategory = 'co2';
          confidence = 0.90;
          if (pointNameLower.includes('sp') || pointNameLower.includes('set')) {
            enosPath = 'FCU_raw_sp_supply_air_co2';
          }
        } else if (pointNameLower.includes('on') && pointNameLower.includes('off') && 
                  (pointNameLower.includes('cmd') || pointNameLower.includes('command'))) {
          pointCategory = 'command';
          confidence = 0.92;
          enosPath = 'FCU_raw_on_off_command';
        }
        break;
        
      case 'CH':
      case 'CHILLER':
        // Standardize to CH prefix for all chiller points
        const chillerPrefix = 'CH_raw_';
        
        if (pointNameLower.includes('status') || pointNameLower.includes('run') || 
            pointNameLower.includes('state') || pointNameLower.includes('on_off')) {
          pointCategory = 'status';
          confidence = 0.94;
          enosPath = chillerPrefix + 'status';
        } else if (pointNameLower.includes('trip') || pointNameLower.includes('fail') || 
                  pointNameLower.includes('fault') || pointNameLower.includes('alarm')) {
          pointCategory = 'status';
          confidence = 0.94;
          enosPath = chillerPrefix + 'trip';
        } else if (pointNameLower.includes('mode')) {
          pointCategory = 'operationMode';
          confidence = 0.92;
          enosPath = chillerPrefix + 'cooling_heating_mode';
        } else if (pointNameLower.includes('valve')) {
          pointCategory = 'valvePosition';
          confidence = 0.90;
          if (pointNameLower.includes('cooling') || pointNameLower.includes('cw')) {
            enosPath = chillerPrefix + 'cooling_valve_status';
          } else if (pointNameLower.includes('chilled') || pointNameLower.includes('chw')) {
            enosPath = chillerPrefix + 'chilled_valve_status';
          }
        } else if (pointNameLower.includes('temp') || pointNameLower.includes('tmp')) {
          pointCategory = 'temperature';
          confidence = 0.93;
          if (pointNameLower.includes('chws') || (pointNameLower.includes('chill') && pointNameLower.includes('supply'))) {
            enosPath = chillerPrefix + 'temp_chws';
          } else if (pointNameLower.includes('chwr') || (pointNameLower.includes('chill') && pointNameLower.includes('return'))) {
            enosPath = chillerPrefix + 'temp_chwr';
          } else if (pointNameLower.includes('cws') || (pointNameLower.includes('cond') && pointNameLower.includes('supply'))) {
            enosPath = chillerPrefix + 'temp_cws';
          } else if (pointNameLower.includes('cwr') || (pointNameLower.includes('cond') && pointNameLower.includes('return'))) {
            enosPath = chillerPrefix + 'temp_cwr';
          } else if (pointNameLower.includes('cond')) {
            enosPath = chillerPrefix + 'temp_cond';
          } else if (pointNameLower.includes('evap')) {
            enosPath = chillerPrefix + 'temp_evap';
          } else if (pointNameLower.includes('sp') || pointNameLower.includes('set')) {
            if (pointNameLower.includes('chw')) {
              enosPath = chillerPrefix + 'sp_temp_chws';
            }
          }
        } else if (pointNameLower.includes('power')) {
          pointCategory = 'power';
          confidence = 0.92;
          enosPath = chillerPrefix + 'power_active_total';
        } else if (pointNameLower.includes('energy')) {
          pointCategory = 'energy';
          confidence = 0.92;
          enosPath = chillerPrefix + 'energy_active_total';
        } else if (pointNameLower.includes('flow')) {
          pointCategory = 'flow';
          confidence = 0.91;
          if (pointNameLower.includes('chill') || pointNameLower.includes('chw')) {
            enosPath = chillerPrefix + 'chilled_water_flow';
          } else if (pointNameLower.includes('cool') || pointNameLower.includes('cw')) {
            enosPath = chillerPrefix + 'cooling_water_flow';
          }
        } else if (pointNameLower.includes('fla')) {
          pointCategory = 'fla';
          confidence = 0.90;
          enosPath = chillerPrefix + 'fla';
        }
        break;
        
      case 'AHU':
        if (pointNameLower.includes('status') || pointNameLower.includes('state') || pointNameLower.includes('run')) {
          pointCategory = 'status';
          confidence = 0.93;
          enosPath = 'AHU_raw_status';
        } else if (pointNameLower.includes('trip') || pointNameLower.includes('fault') || pointNameLower.includes('alarm')) {
          pointCategory = 'status';
          confidence = 0.93;
          enosPath = 'AHU_raw_trip';
        } else if (pointNameLower.includes('temp') || pointNameLower.includes('tmp')) {
          pointCategory = 'temperature';
          confidence = 0.94;
          if (pointNameLower.includes('supply') || pointNameLower.includes('sa')) {
            if (pointNameLower.includes('sp') || pointNameLower.includes('set')) {
              enosPath = 'AHU_raw_sp_supply_air_temp';
            } else {
              enosPath = 'AHU_raw_supply_air_temp';
            }
          } else if (pointNameLower.includes('return') || pointNameLower.includes('ra')) {
            if (pointNameLower.includes('sp') || pointNameLower.includes('set')) {
              enosPath = 'AHU_raw_sp_return_air_temp';
            } else {
              enosPath = 'AHU_raw_return_air_temp';
            }
          } else if (pointNameLower.includes('out') || pointNameLower.includes('oa')) {
            enosPath = 'AHU_raw_outside_air_temp';
          } else if (pointNameLower.includes('chwr')) {
            enosPath = 'AHU_raw_temp_chwr';
          } else if (pointNameLower.includes('chws')) {
            enosPath = 'AHU_raw_temp_chws';
          }
        } else if (pointNameLower.includes('static') || 
                  (pointNameLower.includes('pressure') && !pointNameLower.includes('filter'))) {
          pointCategory = 'pressure';
          confidence = 0.91;
          if (pointNameLower.includes('sp') || pointNameLower.includes('set')) {
            enosPath = 'AHU_raw_sp_static_pressure';
          } else {
            enosPath = 'AHU_raw_static_pressure';
          }
        } else if (pointNameLower.includes('damper')) {
          pointCategory = 'damperPosition';
          confidence = 0.90;
          if (pointNameLower.includes('return') || pointNameLower.includes('ra')) {
            if (pointNameLower.includes('sp') || pointNameLower.includes('set')) {
              enosPath = 'AHU_raw_sp_ra_damper_position';
            } else {
              enosPath = 'AHU_raw_ra_damper_position';
            }
          } else if (pointNameLower.includes('outside') || pointNameLower.includes('oa')) {
            if (pointNameLower.includes('sp') || pointNameLower.includes('set')) {
              enosPath = 'AHU_raw_sp_oa_damper_position';
            } else {
              enosPath = 'AHU_raw_oa_damper_position';
            }
          }
        } else if (pointNameLower.includes('fan')) {
          pointCategory = 'fan';
          confidence = 0.90;
          if (pointNameLower.includes('supply') || pointNameLower.includes('sa')) {
            if (pointNameLower.includes('speed')) {
              if (pointNameLower.includes('cmd') || pointNameLower.includes('command')) {
                enosPath = 'AHU_raw_supply_air_fan_speed_command';
              } else {
                enosPath = 'AHU_raw_supply_air_fan_speed';
              }
            } else if (pointNameLower.includes('freq')) {
              enosPath = 'AHU_raw_supply_air_fan_frequency';
            }
          } else if (pointNameLower.includes('return') || pointNameLower.includes('ra')) {
            if (pointNameLower.includes('freq')) {
              enosPath = 'AHU_raw_return_air_fan_frequency';
            }
          }
        } else if (pointNameLower.includes('valve')) {
          pointCategory = 'valve';
          confidence = 0.90;
          enosPath = 'AHU_raw_valve_position';
          if (pointNameLower.includes('heat') || pointNameLower.includes('hw')) {
            enosPath = 'AHU_raw_hw_valve_position';
          }
        } else if (pointNameLower.includes('filter')) {
          pointCategory = 'filter';
          confidence = 0.90;
          if (pointNameLower.includes('delta') || pointNameLower.includes('dp') || pointNameLower.includes('pressure')) {
            enosPath = 'AHU_raw_filter_delta_pressure';
          } else {
            enosPath = 'AHU_raw_filter_status';
          }
        } else if (pointNameLower.includes('flow')) {
          pointCategory = 'flow';
          confidence = 0.90;
          enosPath = 'AHU_raw_air_flow';
        } else if (pointNameLower.includes('co2')) {
          pointCategory = 'co2';
          confidence = 0.90;
          if (pointNameLower.includes('return') || pointNameLower.includes('ra')) {
            if (pointNameLower.includes('sp') || pointNameLower.includes('set')) {
              enosPath = 'AHU_raw_sp_return_air_co2';
            } else {
              enosPath = 'AHU_raw_return_air_co2';
            }
          } else if (pointNameLower.includes('supply') || pointNameLower.includes('sa')) {
            if (pointNameLower.includes('sp') || pointNameLower.includes('set')) {
              enosPath = 'AHU_raw_sp_supply_air_co2';
            }
          }
        } else if (pointNameLower.includes('hum')) {
          pointCategory = 'humidity';
          confidence = 0.90;
          if (pointNameLower.includes('return') || pointNameLower.includes('ra')) {
            enosPath = 'AHU_raw_return_air_humidity';
          }
        } else if (pointNameLower.includes('velocity') || pointNameLower.includes('vel')) {
          pointCategory = 'velocity';
          confidence = 0.85;
          if (pointNameLower.includes('mix')) {
            if (pointNameLower.includes('1') || pointNameLower.includes('one')) {
              enosPath = 'AHU_raw_mix_air_velocity1';
            } else if (pointNameLower.includes('2') || pointNameLower.includes('two')) {
              enosPath = 'AHU_raw_mix_air_velocity2';
            } else if (pointNameLower.includes('3') || pointNameLower.includes('three')) {
              enosPath = 'AHU_raw_mix_air_velocity3';
            } else if (pointNameLower.includes('4') || pointNameLower.includes('four')) {
              enosPath = 'AHU_raw_mix_air_velocity4';
            }
          }
        } else if (pointNameLower.includes('power')) {
          pointCategory = 'power';
          confidence = 0.90;
          enosPath = 'AHU_raw_power_active_total';
        } else if (pointNameLower.includes('energy')) {
          pointCategory = 'energy';
          confidence = 0.90;
          enosPath = 'AHU_raw_energy_active_total';
        } else if (pointNameLower.includes('cool') && pointNameLower.includes('demand')) {
          pointCategory = 'demand';
          confidence = 0.90;
          enosPath = 'AHU_raw_cooling_demand';
        } else if (pointNameLower.includes('mode')) {
          pointCategory = 'mode';
          confidence = 0.90;
          if (pointNameLower.includes('op') || pointNameLower.includes('operation')) {
            enosPath = 'AHU_raw_operation_mode';
          } else if (pointNameLower.includes('cool') || pointNameLower.includes('heat')) {
            if (pointNameLower.includes('cmd') || pointNameLower.includes('command')) {
              enosPath = 'AHU_raw_cooling_heating_mode_command';
            }
          }
        } else if (pointNameLower.includes('on') && pointNameLower.includes('off') && 
                  (pointNameLower.includes('cmd') || pointNameLower.includes('command'))) {
          pointCategory = 'command';
          confidence = 0.92;
          enosPath = 'AHU_raw_on_off_command';
        }
        break;
        
      case 'PUMP':
      case 'PU':
        const pumpPrefix = 'PUMP_raw_';
        
        if (pointNameLower.includes('status') || pointNameLower.includes('state') || pointNameLower.includes('run')) {
          pointCategory = 'status';
          confidence = 0.94;
          enosPath = pumpPrefix + 'status';
        } else if (pointNameLower.includes('trip') || pointNameLower.includes('fault') || pointNameLower.includes('alarm')) {
          pointCategory = 'status';
          confidence = 0.94;
          enosPath = pumpPrefix + 'trip';
        } else if (pointNameLower.includes('power')) {
          pointCategory = 'power';
          confidence = 0.92;
          enosPath = pumpPrefix + 'power_active_total';
        } else if (pointNameLower.includes('energy')) {
          pointCategory = 'energy';
          confidence = 0.92;
          enosPath = pumpPrefix + 'energy_active_total';
        } else if (pointNameLower.includes('flow')) {
          pointCategory = 'flow';
          confidence = 0.91;
          enosPath = pumpPrefix + 'flow';
        } else if (pointNameLower.includes('pressure')) {
          pointCategory = 'pressure';
          confidence = 0.90;
          enosPath = pumpPrefix + 'pressure';
        } else if (pointNameLower.includes('speed') || pointNameLower.includes('freq')) {
          pointCategory = 'speed';
          confidence = 0.90;
          // Note: This is not in the provided enos.json but is a common pump parameter
          enosPath = pumpPrefix + 'speed';
        }
        break;
        
      case 'CT':
      case 'COOLING TOWER':
        const ctPrefix = 'CT_raw_';
        
        if (pointNameLower.includes('status') || pointNameLower.includes('state') || pointNameLower.includes('run')) {
          pointCategory = 'status';
          confidence = 0.94;
          enosPath = ctPrefix + 'status';
        } else if (pointNameLower.includes('trip') || pointNameLower.includes('fault') || pointNameLower.includes('alarm')) {
          pointCategory = 'status';
          confidence = 0.94;
          enosPath = ctPrefix + 'trip';
        } else if (pointNameLower.includes('temp') || pointNameLower.includes('tmp')) {
          pointCategory = 'temperature';
          confidence = 0.92;
          if (pointNameLower.includes('enter') || pointNameLower.includes('cwe') || pointNameLower.includes('return')) {
            enosPath = ctPrefix + 'temp_cwe';
          } else if (pointNameLower.includes('leave') || pointNameLower.includes('cwl') || pointNameLower.includes('supply')) {
            enosPath = ctPrefix + 'temp_cwl';
          }
        } else if (pointNameLower.includes('valve')) {
          pointCategory = 'valve';
          confidence = 0.90;
          if (pointNameLower.includes('enter') || pointNameLower.includes('cwe') || pointNameLower.includes('return')) {
            enosPath = ctPrefix + 'valve_status_cwe';
          } else if (pointNameLower.includes('leave') || pointNameLower.includes('cwl') || pointNameLower.includes('supply')) {
            enosPath = ctPrefix + 'valve_status_cwl';
          }
        } else if (pointNameLower.includes('power')) {
          pointCategory = 'power';
          confidence = 0.92;
          enosPath = ctPrefix + 'power_active_total';
        } else if (pointNameLower.includes('energy')) {
          pointCategory = 'energy';
          confidence = 0.92;
          enosPath = ctPrefix + 'energy_active_total';
        } else if (pointNameLower.includes('on') && pointNameLower.includes('off') && 
                  (pointNameLower.includes('cmd') || pointNameLower.includes('command'))) {
          pointCategory = 'command';
          confidence = 0.92;
          enosPath = ctPrefix + 'on_off_command';
        }
        break;
        
      case 'CHPL':
      case 'CHILLER PLANT':
        const chplPrefix = 'CHPL_raw_';
        
        if (pointNameLower.includes('temp') || pointNameLower.includes('tmp')) {
          pointCategory = 'temperature';
          confidence = 0.93;
          if (pointNameLower.includes('chw') || pointNameLower.includes('chill')) {
            if (pointNameLower.includes('supply') || pointNameLower.includes('header')) {
              if (pointNameLower.includes('sp') || pointNameLower.includes('set')) {
                enosPath = chplPrefix + 'sp_temp_chws';
              } else {
                enosPath = chplPrefix + 'temp_chws_header';
              }
            } else if (pointNameLower.includes('return')) {
              enosPath = chplPrefix + 'temp_chwr_header';
            }
          } else if (pointNameLower.includes('cw') || pointNameLower.includes('cond')) {
            if (pointNameLower.includes('supply') || pointNameLower.includes('leave')) {
              if (pointNameLower.includes('sp') || pointNameLower.includes('set')) {
                enosPath = chplPrefix + 'sp_temp_cws';
              } else {
                enosPath = chplPrefix + 'temp_cws_header';
              }
            } else if (pointNameLower.includes('return') || pointNameLower.includes('enter')) {
              enosPath = chplPrefix + 'temp_cwr_header';
            }
          }
        } else if (pointNameLower.includes('flow')) {
          pointCategory = 'flow';
          confidence = 0.92;
          if (pointNameLower.includes('chw') || pointNameLower.includes('chill')) {
            enosPath = chplPrefix + 'flow_chws_header';
          } else if (pointNameLower.includes('cw') || pointNameLower.includes('cond')) {
            enosPath = chplPrefix + 'flow_cws_header';
          }
        } else if (pointNameLower.includes('pressure')) {
          pointCategory = 'pressure';
          confidence = 0.91;
          if (pointNameLower.includes('delta') || pointNameLower.includes('diff')) {
            if (pointNameLower.includes('sp') || pointNameLower.includes('set')) {
              enosPath = chplPrefix + 'sp_delta_pressure_header';
            } else {
              enosPath = chplPrefix + 'delta_pressure_header';
            }
          } else if (pointNameLower.includes('chws') || (pointNameLower.includes('chill') && pointNameLower.includes('supply'))) {
            enosPath = chplPrefix + 'chws_pressure';
          } else if (pointNameLower.includes('chwr') || (pointNameLower.includes('chill') && pointNameLower.includes('return'))) {
            enosPath = chplPrefix + 'chwr_pressure';
          }
        } else if (pointNameLower.includes('load') && pointNameLower.includes('building')) {
          pointCategory = 'load';
          confidence = 0.92;
          enosPath = chplPrefix + 'load_building';
        }
        break;
    }

    // Set default enosPath if not already set, based on device type
    if (!enosPath) {
      // Map to standard format for each device type
      if (deviceType === 'FCU') {
        enosPath = `FCU_raw_${pointCategory}`;
      } else if (deviceType === 'AHU') {
        enosPath = `AHU_raw_${pointCategory}`;
      } else if (deviceType === 'CH' || deviceType === 'CHILLER') {
        enosPath = `CH_raw_${pointCategory}`;
      } else if (deviceType === 'PUMP' || deviceType === 'PU') {
        enosPath = `PUMP_raw_${pointCategory}`;
      } else if (deviceType === 'CT' || deviceType === 'COOLING TOWER') {
        enosPath = `CT_raw_${pointCategory}`;
      } else if (deviceType === 'CHPL' || deviceType === 'CHILLER PLANT') {
        enosPath = `CHPL_raw_${pointCategory}`;
      } else {
        // For unknown device types, use a standard format
        enosPath = `${deviceType}_raw_${pointCategory}`;
      }
      
    }

    // Return the mapped point with properly typed status
    return {
      pointId: point.id,
      pointName: point.pointName,
      pointType: point.pointType,
      deviceType: deviceType,
      deviceId: deviceId,
      pointCategory: pointCategory,
      enosPath: enosPath,
      unit: point.unit,
      // Keep confidence for internal calculations but it won't be in the final types
      status: 'mapped' as 'mapped',  // Type assertion to satisfy TypeScript
      mappingSource: 'client-side'   // Add source information
    };
  });

  // Update mappedPoints to include the required enosPoint field
  const formattedMappings = mappedPoints.map(point => ({
    ...point,
    enosPoint: point.pointCategory || 'unknown' // Add enosPoint from pointCategory for compatibility
  }));

  // Calculate average confidence for debugging only

  // Create a success response
  const response: MapPointsToEnOSResponse = {
    success: true,
    mappings: formattedMappings,
    stats: {
      total: points.length,
      mapped: formattedMappings.length,
      errors: 0,
      deviceCount: Array.from(new Set(formattedMappings.map(p => p.deviceId))).length,
      deviceTypes: Array.from(new Set(formattedMappings.map(p => p.deviceType))).length
    }
  };

  // Return the response wrapped in a Promise
  return Promise.resolve(response);
}

/**
 * Analyze mapping quality to identify mappings that need improvement
 * @param mappings The mapping results to analyze
 * @returns Quality assessment results with suggestions for improvement
 */
export function analyzeMappingQuality(
  mappings: MapPointsToEnOSResponse
): MappingQualityResult {
  // Initialize quality counters
  const qualitySummary = {
    excellent: 0,
    good: 0,
    fair: 0,
    poor: 0,
    unacceptable: 0
  };
  
  // Array to hold points with poor quality mappings
  const pointsWithPoorQuality: Array<{
    pointId: string;
    pointName: string;
    mappingQuality: string;
    issues: string[];
  }> = [];
  
  // Unique ID for this mapping analysis
  const mappingId = `mapping_${Date.now()}`;
  
  // Helper function to check if enosPoint is valid according to the schema
  const isValidEnosPoint = (deviceType: string, enosPoint: string): boolean => {
    // Define valid point prefixes for each device type
    const validPrefixes: Record<string, string[]> = {
      'CH': ['CH_raw_', 'CH_write_'],
      'CHILLER': ['CH_raw_', 'CH_write_'],
      'AHU': ['AHU_raw_', 'AHU_write_'],
      'FCU': ['FCU_raw_', 'FCU_write_'],
      'PUMP': ['PUMP_raw_', 'PUMP_write_'],
      'PU': ['PUMP_raw_', 'PUMP_write_'],
      'CT': ['CT_raw_', 'CT_write_'],
      'COOLING TOWER': ['CT_raw_', 'CT_write_'],
      'CHPL': ['CHPL_raw_', 'CHPL_write_'],
      'CHILLER PLANT': ['CHPL_raw_', 'CHPL_write_']
    };

    // Points that should not contain 'generic' regardless of their prefix
    // This is our validation list - any point ending with these is considered valid
    const validPointSuffixes: Record<string, string[]> = {
      'CH': ['status', 'trip', 'temp_chws', 'temp_chwr', 'temp_evap', 'temp_cws', 'temp_cwr', 
             'power_active_total', 'energy_active_total', 'sp_temp_chws', 'chilled_valve_status',
             'cooling_valve_status', 'chilled_water_flow', 'cooling_water_flow', 'cooling_heating_mode', 'fla'],
      'PUMP': ['status', 'trip', 'power_active_total', 'energy_active_total', 'flow', 'pressure', 'speed'],
      'CT': ['status', 'trip', 'on_off_command', 'temp_cwe', 'temp_cwl', 'valve_status_cwe',
             'valve_status_cwl', 'power_active_total', 'energy_active_total'],
      'CHPL': ['load_building', 'temp_chws_header', 'temp_chwr_header', 'flow_chws_header',
               'chws_pressure', 'chwr_pressure', 'flow_chwr_header', 'power_active_total',
               'energy_active_total', 'sp_temp_chws', 'sp_delta_pressure_header', 'delta_pressure_header'],
      'AHU': ['status', 'trip', 'cooling_heating_mode_command', 'energy_active_total',
              'ra_damper_position', 'return_air_co2', 'on_off_command', 'return_air_humidity',
              'sp_ra_damper_position', 'supply_air_temp', 'return_air_temp', 'outside_air_temp',
              'static_pressure', 'oa_damper_position', 'supply_air_fan_speed', 'air_flow'],
      'FCU': ['chw_valve_status', 'cooling_heating_mode', 'hw_valve_status', 'local_mode',
              'local_mode_command', 'on_off_command', 'status', 'trip', 'zone_air_temp',
              'zone_occupancy', 'sp_supply_air_co2', 'fan_speed_command', 'fan_speed',
              'sp_zone_air_temp', 'sp_zone_air_temp_command', 'supply_air_temp']
    };
    
    // First check if it's a valid device type
    if (!validPrefixes[deviceType]) {
      return false; // Unknown device type
    }
    
    // Normalize deviceType for lookup
    const normalizedDeviceType = deviceType === 'CHILLER' ? 'CH' : 
                                deviceType === 'PU' ? 'PUMP' : 
                                deviceType === 'COOLING TOWER' ? 'CT' : 
                                deviceType === 'CHILLER PLANT' ? 'CHPL' : 
                                deviceType;
    
    // Check if it has a valid prefix
    const hasValidPrefix = validPrefixes[deviceType].some(prefix => 
      enosPoint.startsWith(prefix)
    );
    
    if (!hasValidPrefix) {
      return false; // Invalid prefix
    }
    
    // It has a valid prefix, now check if it contains 'generic'
    if (enosPoint.toLowerCase().includes('generic')) {
      return false; // Contains 'generic', so it's not a specific point type
    }
    
    // Check if it has a valid suffix
    const validSuffixes = validPointSuffixes[normalizedDeviceType] || [];
    return validSuffixes.some(suffix => 
      enosPoint.endsWith(suffix)
    );
  };

  // Process each mapping to assess quality
  if (mappings.mappings) {
    mappings.mappings.forEach(mapping => {
      const issues: string[] = [];
      
      // Original and mapping structure support
      const mappingData = mapping.original && mapping.mapping 
        ? { 
            pointId: mapping.mapping.pointId,
            pointName: mapping.original.pointName,
            deviceType: mapping.original.deviceType,
            enosPoint: mapping.mapping.enosPoint
          }
        : mapping;
      
      // Check for missing or unknown point type
      if (!mappingData.enosPoint || mappingData.enosPoint === 'unknown' || mappingData.enosPoint === null) {
        issues.push('Unknown point type');
      }
      
      // Check for missing or unknown device type
      if (!mappingData.deviceType || mappingData.deviceType === 'UNKNOWN') {
        issues.push('Unknown device type');
      }
      
      // Check for generic mapping
      if (mappingData.enosPoint && 
          (typeof mappingData.enosPoint === 'string') && 
          mappingData.enosPoint.toLowerCase().includes('generic')) {
        issues.push('Generic mapping used');
        
        // Try to suggest a better mapping
        if (mappingData.pointName && mappingData.deviceType) {
          const pointName = mappingData.pointName.toLowerCase();
          const deviceType = mappingData.deviceType;
          
          // Suggest better mappings for common patterns
          if (pointName.includes('trip') || pointName.includes('fault') || pointName.includes('alarm')) {
            issues.push(`Suggestion: Map to ${deviceType}_raw_trip instead of generic point`);
          } else if (pointName.includes('status') || pointName.includes('state') || pointName.includes('run')) {
            issues.push(`Suggestion: Map to ${deviceType}_raw_status instead of generic point`);
          }
        }
      }
      
      // Check if the enos point is valid according to the schema
      if (mappingData.enosPoint && mappingData.deviceType && 
          typeof mappingData.enosPoint === 'string' && 
          !mappingData.enosPoint.toLowerCase().includes('generic')) {
        
        if (!isValidEnosPoint(mappingData.deviceType, mappingData.enosPoint)) {
          issues.push(`Invalid enosPoint: ${mappingData.enosPoint} is not a valid point for ${mappingData.deviceType}`);
        }
      }
      
      // Assess mapping quality based on issues count
      let mappingQuality = 'fair';
      
      if (issues.length === 0) {
        mappingQuality = 'excellent';
        qualitySummary.excellent++;
      } else if (issues.length === 1 && !issues.includes('Unknown point type')) {
        mappingQuality = 'good';
        qualitySummary.good++;
      } else if (issues.length <= 2) {
        mappingQuality = 'fair';
        qualitySummary.fair++;
      } else if (issues.length <= 3) {
        mappingQuality = 'poor';
        qualitySummary.poor++;
        
        // Add to points needing improvement
        pointsWithPoorQuality.push({
          pointId: (mapping.mapping?.pointId || mapping.pointId || ''),
          pointName: (mapping.original?.pointName || mapping.pointName || ''),
          mappingQuality,
          issues
        });
      } else {
        mappingQuality = 'unacceptable';
        qualitySummary.unacceptable++;
        
        // Add to points needing improvement
        pointsWithPoorQuality.push({
          pointId: (mapping.mapping?.pointId || mapping.pointId || ''),
          pointName: (mapping.original?.pointName || mapping.pointName || ''),
          mappingQuality,
          issues
        });
      }
    });
  }
  
  return {
    mappingId,
    qualitySummary,
    pointsWithPoorQuality
  };
}