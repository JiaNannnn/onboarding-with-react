/**
 * BMS API client module
 *
 * This module provides functions for interacting with the BMS onboarding API.
 */
import axios from 'axios';

// Get API base URL from environment or use default
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

/**
 * Process BMS points through the onboarding pipeline
 *
 * @param {Array} points - Array of BMS point objects
 * @param {Object} options - Optional parameters
 * @param {number} options.batchSize - Batch size for processing points
 * @param {string} options.ontologyVersion - Specific ontology version to use
 * @param {number} options.memoryLimitPct - Memory limit percentage
 * @returns {Promise} - Promise resolving to the mapping results
 */
export const processBmsPoints = async (points, options = {}) => {
  const { batchSize = 200, ontologyVersion, memoryLimitPct = 75 } = options;

  try {
    const response = await axios.post(`${API_BASE_URL}/bms/onboard`, {
      points,
      batch_size: batchSize,
      ontology_version: ontologyVersion,
      memory_limit_pct: memoryLimitPct,
    });

    return response.data;
  } catch (error) {
    console.error('Error processing BMS points:', error);
    throw error;
  }
};

/**
 * Export mapping configuration from mapping results
 *
 * @param {Object} result - Mapping result from processBmsPoints
 * @returns {Promise} - Promise resolving to the mapping configuration
 */
export const exportMappingConfig = async (result) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/bms/export-mapping`, {
      result,
    });

    return response.data;
  } catch (error) {
    console.error('Error exporting mapping config:', error);
    throw error;
  }
};

/**
 * Format a BMS point for display in the UI
 *
 * @param {Object} bmsPoint - BMS point from mapping results
 * @returns {Object} - Formatted BMS point for UI display
 */
export const formatBmsPointForDisplay = (bmsPoint) => {
  // Extract tags into a more usable format
  const tags = {};
  if (bmsPoint.tags) {
    bmsPoint.tags.forEach((tag) => {
      const [key, value] = tag.split(':');
      if (key && value) {
        tags[key] = value;
      }
    });
  }

  return {
    id: bmsPoint.point_id,
    name: bmsPoint.point_name,
    type: bmsPoint.point_type,
    description: bmsPoint.description,
    unit: bmsPoint.unit,
    component: bmsPoint.component,
    subcomponent: bmsPoint.subcomponent,
    function: bmsPoint.function,
    resource: bmsPoint.resource,
    subResource: bmsPoint.sub_resource,
    category: bmsPoint.category,
    phenomenon: bmsPoint.phenomenon,
    aspect: bmsPoint.aspect,
    quantity: bmsPoint.quantity,
    tags,
  };
};

/**
 * Format mapping results for display in the UI
 *
 * @param {Object} result - Mapping result from processBmsPoints
 * @returns {Array} - Formatted mappings for UI display
 */
export const formatMappingsForDisplay = (result) => {
  const formattedMappings = [];

  for (const equipmentType in result) {
    for (const instanceId in result[equipmentType]) {
      const mappings = result[equipmentType][instanceId];

      mappings.forEach((mapping) => {
        formattedMappings.push({
          equipmentType,
          instanceId,
          bmsPoint: formatBmsPointForDisplay(mapping.bms_point),
          enosPoint: mapping.enos_point,
          confidence: mapping.confidence,
          mappingType: mapping.mapping_type,
          transformation: mapping.transformation,
          reason: mapping.reason,
        });
      });
    }
  }

  return formattedMappings;
};
