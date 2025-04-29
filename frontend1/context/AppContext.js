import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

// Create context
const AppContext = createContext();

// Custom hook to use the context
export const useAppContext = () => useContext(AppContext);

export const AppProvider = ({ children }) => {
  // State for raw points data
  const [rawPoints, setRawPoints] = useState([]);
  
  // State for grouped points
  const [groupedPoints, setGroupedPoints] = useState({});
  
  // State for EnOS mapping
  const [enosMapping, setEnosMapping] = useState([]);
  
  // State for saved mappings
  const [savedMappings, setSavedMappings] = useState([]);
  
  // State for loading status
  const [loading, setLoading] = useState(false);
  
  // State for error messages
  const [error, setError] = useState(null);
  
  // Fetch raw points data from API
  const fetchRawPoints = async (assetId, deviceInstance, deviceAddress = 'unknown-ip') => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/bms/fetch-points', {
        assetId,
        deviceInstance,
        deviceAddress
      });
      
      if (response.data.success) {
        // Ensure all required fields are available for each point
        const processedPoints = response.data.data.map(point => {
          // Convert objectIdentifier if it's a string to ensure its value is accessible
          let objectId = point.objectIdentifier;
          if (typeof objectId === 'string' && objectId.includes(',')) {
            try {
              // Handle format like "(binary-input,0)"
              objectId = objectId.replace(/[()]/g, '');
            } catch (e) {
              console.error('Error parsing objectIdentifier:', e);
            }
          }
          
          return {
            ...point,
            objectIdentifier: objectId,
            // Ensure these fields are present for display in the table
            pointName: point.pointName || point.objectName || 'Unknown',
            pointType: point.pointType || point.objectType || 'Unknown',
            pointId: point.pointId || `${point.otDeviceInst}:${point.objectInst}` || 'Unknown',
            otDeviceInst: point.otDeviceInst || 'Unknown',
            objectInst: point.objectInst || 'Unknown',
            PresentValue: point.presentValue || point.PresentValue || 'N/A'
          };
        });
        
        setRawPoints(processedPoints);
        console.log('Fetched and processed points:', processedPoints);
        return processedPoints;
      } else {
        setError(response.data.error || 'Failed to fetch points data');
        return [];
      }
    } catch (err) {
      setError(err.message || 'An error occurred while fetching points data');
      return [];
    } finally {
      setLoading(false);
    }
  };
  
  // Group points by a specific property
  const groupPointsByProperty = useCallback((points, property) => {
    if (!points || !points.length) return {};
    
    const groups = {};
    
    points.forEach(point => {
      const value = point[property] || 'Unknown';
      if (!groups[value]) {
        groups[value] = [];
      }
      groups[value].push(point);
    });
    
    setGroupedPoints(groups);
    return groups;
  }, []);
  
  // Save mapping to CSV
  const saveMappingToCsv = async (mapping, filename = '') => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/bms/save-mapping', {
        mapping,
        filename
      });
      
      if (response.data.success) {
        // Refresh the list of saved mappings
        await listSavedMappings();
        return response.data.filepath;
      } else {
        setError(response.data.error || 'Failed to save mapping');
        return null;
      }
    } catch (err) {
      setError(err.message || 'An error occurred while saving mapping');
      return null;
    } finally {
      setLoading(false);
    }
  };
  
  // List saved mapping files
  const listSavedMappings = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get('/api/bms/list-saved-files');
      
      if (response.data.success) {
        setSavedMappings(response.data.files);
        return response.data.files;
      } else {
        setError(response.data.error || 'Failed to list saved files');
        return [];
      }
    } catch (err) {
      setError(err.message || 'An error occurred while listing saved files');
      return [];
    } finally {
      setLoading(false);
    }
  };
  
  // Load a saved mapping file
  const loadSavedMapping = async (filepath) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/bms/load-csv', {
        filepath
      });
      
      if (response.data.success) {
        setEnosMapping(response.data.data);
        return response.data.data;
      } else {
        setError(response.data.error || 'Failed to load mapping');
        return null;
      }
    } catch (err) {
      setError(err.message || 'An error occurred while loading mapping');
      return null;
    } finally {
      setLoading(false);
    }
  };
  
  // Load saved mappings on component mount
  useEffect(() => {
    listSavedMappings();
  }, []);
  
  // Group points using AI with hierarchical structure support
  const groupPointsWithAI = async (points, groupingStrategy = 'default', equipmentType = null) => {
    if (!points || points.length === 0) {
      console.error('No points provided for grouping');
      return {};
    }
    
    setLoading(true);
    try {
      console.log(`Grouping ${points.length} points with strategy: ${groupingStrategy}`);
      
      // Prepare request data
      const requestData = {
        points: points,
        strategy: groupingStrategy,
        equipment_type: equipmentType
      };
      
      // Make API request
      const response = await axios.post('/api/bms/group-points', requestData);
      
      // Check for successful response
      if (!response.data || !response.data.success) {
        console.error('Failed to group points:', response.data?.error || 'Unknown error');
        setError(response.data?.error || 'Failed to group points');
        return {};
      }
      
      // Parse and normalize the response data
      const parsedGroups = parseGroupingResponse(response.data, points);
      console.log('Parsed groups structure:', parsedGroups);
      
      setGroupedPoints(parsedGroups);
      return parsedGroups;
    } catch (error) {
      console.error('Error grouping points:', error);
      setError(error.message || 'Failed to group points');
      return {};
    } finally {
      setLoading(false);
    }
  };
  
  /**
   * Parses and normalizes group response data from different formats
   * @param {Object} responseData - The API response data
   * @param {Array} originalPoints - Original points array for reference
   * @returns {Object} Normalized groups object
   */
  const parseGroupingResponse = (responseData, originalPoints) => {
    console.log('Parsing group response:', responseData);
    
    // Create points lookup for reference
    const pointsLookup = createPointsLookup(originalPoints);
    
    // Initialize result object
    const result = {};
    
    try {
      // Case 1: We have grouped_points object in the response (preferred format)
      if (responseData.grouped_points && typeof responseData.grouped_points === 'object') {
        return parseGroupedPointsStructure(responseData.grouped_points, pointsLookup);
      }
      
      // Case 2: We have a groups array in the response (legacy format)
      if (Array.isArray(responseData.groups)) {
        return parseGroupsArrayStructure(responseData.groups, pointsLookup);
      }
      
      // Case 3: Direct object with group names as keys (simplest format)
      if (responseData.groups && typeof responseData.groups === 'object' && !Array.isArray(responseData.groups)) {
        return parseDirectGroupsStructure(responseData.groups, pointsLookup);
      }
      
      // Nothing valid found, return empty result
      console.error('No recognizable group format found in response', responseData);
      return {};
    } catch (error) {
      console.error('Error parsing group response:', error);
      return {};
    }
  };
  
  /**
   * Creates a lookup object for points by various identifiers
   * @param {Array} points - Array of points
   * @returns {Object} Lookup dictionary
   */
  const createPointsLookup = (points) => {
    const lookup = {};
    
    if (!Array.isArray(points)) return lookup;
    
    points.forEach(point => {
      // Add multiple lookup keys
      if (point.pointId) lookup[point.pointId] = point;
      if (point.pointName) lookup[point.pointName] = point;
      if (point.objectName) lookup[point.objectName] = point;
      if (point.id) lookup[point.id] = point;
      
      // Add combined key for BACnet references
      if (point.otDeviceInst && point.objectInst) {
        lookup[`${point.otDeviceInst}:${point.objectInst}`] = point;
      }
    });
    
    return lookup;
  };
  
  /**
   * Parses the hierarchical grouped_points structure
   * @param {Object} groupedPoints - The grouped_points object
   * @param {Object} pointsLookup - Lookup for resolving point references
   * @returns {Object} Normalized groups object
   */
  const parseGroupedPointsStructure = (groupedPoints, pointsLookup) => {
    const result = {};
    
    // Validate input
    if (!groupedPoints || typeof groupedPoints !== 'object') {
      console.error('Invalid grouped_points structure:', groupedPoints);
      return result;
    }
    
    Object.entries(groupedPoints).forEach(([groupName, groupData]) => {
      // Skip empty or invalid groups
      if (!groupName || !groupData) return;
      
      // Initialize group structure
      result[groupName] = {
        points: [],
        subgroups: {}
      };
      
      // Case 1: Group is a direct array of points
      if (Array.isArray(groupData)) {
        result[groupName].points = resolvePointReferences(groupData, pointsLookup);
        return;
      }
      
      // Case 2: Group has a points array
      if (groupData.points && Array.isArray(groupData.points)) {
        result[groupName].points = resolvePointReferences(groupData.points, pointsLookup);
      }
      
      // Case 3: Group has subgroups
      if (groupData.subgroups && typeof groupData.subgroups === 'object') {
        Object.entries(groupData.subgroups).forEach(([subgroupName, subgroupData]) => {
          // Skip if subgroup name is invalid
          if (!subgroupName) return;
          
          // Case 3.1: Subgroup is a direct array of points
          if (Array.isArray(subgroupData)) {
            result[groupName].subgroups[subgroupName] = resolvePointReferences(subgroupData, pointsLookup);
            return;
          }
          
          // Case 3.2: Subgroup has a points array
          if (subgroupData && subgroupData.points && Array.isArray(subgroupData.points)) {
            result[groupName].subgroups[subgroupName] = resolvePointReferences(subgroupData.points, pointsLookup);
            return;
          }
          
          // Case 3.3: Unexpected format, treat as empty
          console.warn(`Unexpected subgroup format for ${groupName} > ${subgroupName}:`, subgroupData);
          result[groupName].subgroups[subgroupName] = [];
        });
      }
    });
    
    return result;
  };
  
  /**
   * Parses the legacy groups array structure
   * @param {Array} groups - The groups array
   * @param {Object} pointsLookup - Lookup for resolving point references
   * @returns {Object} Normalized groups object
   */
  const parseGroupsArrayStructure = (groups, pointsLookup) => {
    const result = {};
    
    // Validate input
    if (!Array.isArray(groups)) {
      console.error('Invalid groups array structure:', groups);
      return result;
    }
    
    groups.forEach(group => {
      // Skip invalid groups
      if (!group || !group.name) return;
      
      const groupName = group.name;
      
      // Initialize group structure
      result[groupName] = {
        points: [],
        subgroups: {}
      };
      
      // Parse points
      if (group.points && Array.isArray(group.points)) {
        result[groupName].points = resolvePointReferences(group.points, pointsLookup);
      }
      
      // Parse subgroups if they exist
      if (group.subgroups && typeof group.subgroups === 'object') {
        Object.entries(group.subgroups).forEach(([subgroupName, subgroupData]) => {
          // Skip invalid subgroups
          if (!subgroupName) return;
          
          // Resolve points depending on format
          if (Array.isArray(subgroupData)) {
            result[groupName].subgroups[subgroupName] = resolvePointReferences(subgroupData, pointsLookup);
          } else if (subgroupData && Array.isArray(subgroupData.points)) {
            result[groupName].subgroups[subgroupName] = resolvePointReferences(subgroupData.points, pointsLookup);
          } else {
            console.warn(`Invalid subgroup data for ${groupName} > ${subgroupName}:`, subgroupData);
            result[groupName].subgroups[subgroupName] = [];
          }
        });
      }
    });
    
    return result;
  };
  
  /**
   * Parses the simple direct groups structure
   * @param {Object} groups - The groups object
   * @param {Object} pointsLookup - Lookup for resolving point references
   * @returns {Object} Normalized groups object
   */
  const parseDirectGroupsStructure = (groups, pointsLookup) => {
    const result = {};
    
    // Validate input
    if (!groups || typeof groups !== 'object') {
      console.error('Invalid direct groups structure:', groups);
      return result;
    }
    
    Object.entries(groups).forEach(([groupName, groupPoints]) => {
      // Skip invalid groups
      if (!groupName) return;
      
      // Initialize group structure
      result[groupName] = {
        points: [],
        subgroups: {}
      };
      
      // Parse points based on format
      if (Array.isArray(groupPoints)) {
        result[groupName].points = resolvePointReferences(groupPoints, pointsLookup);
      } else if (groupPoints && Array.isArray(groupPoints.points)) {
        result[groupName].points = resolvePointReferences(groupPoints.points, pointsLookup);
        
        // Check for subgroups
        if (groupPoints.subgroups && typeof groupPoints.subgroups === 'object') {
          Object.entries(groupPoints.subgroups).forEach(([subgroupName, subgroupPoints]) => {
            if (!subgroupName) return;
            
            // Resolve subgroup points
            if (Array.isArray(subgroupPoints)) {
              result[groupName].subgroups[subgroupName] = resolvePointReferences(subgroupPoints, pointsLookup);
            } else {
              console.warn(`Invalid subgroup data for ${groupName} > ${subgroupName}:`, subgroupPoints);
              result[groupName].subgroups[subgroupName] = [];
            }
          });
        }
      } else {
        console.warn(`Invalid group data for ${groupName}:`, groupPoints);
        result[groupName].points = [];
      }
    });
    
    return result;
  };
  
  /**
   * Resolves point references to full point objects
   * @param {Array} pointRefs - Array of point references (can be IDs or objects)
   * @param {Object} pointsLookup - Lookup for resolving point references
   * @returns {Array} Array of full point objects
   */
  const resolvePointReferences = (pointRefs, pointsLookup) => {
    if (!Array.isArray(pointRefs)) return [];
    
    return pointRefs.map(pointRef => {
      // Case 1: Already a full point object with a pointName
      if (pointRef && typeof pointRef === 'object' && pointRef.pointName) {
        return pointRef;
      }
      
      // Case 2: Point reference is a string ID
      if (typeof pointRef === 'string') {
        return pointsLookup[pointRef] || {
          pointName: pointRef,
          pointType: 'unknown',
          pointId: pointRef,
          PresentValue: 'N/A'
        };
      }
      
      // Case 3: Partial point object with an ID
      if (pointRef && typeof pointRef === 'object') {
        const pointId = pointRef.id || pointRef.pointId;
        if (pointId && pointsLookup[pointId]) {
          return pointsLookup[pointId];
        }
        
        // Create a basic point from the partial data
        return {
          pointName: pointRef.name || pointRef.pointName || 'Unknown Point',
          pointType: pointRef.type || pointRef.pointType || 'unknown',
          pointId: pointId || 'unknown-id',
          PresentValue: pointRef.PresentValue || pointRef.presentValue || 'N/A',
          ...pointRef
        };
      }
      
      // Case 4: Completely invalid point reference
      console.warn('Invalid point reference:', pointRef);
      return {
        pointName: 'Invalid Point',
        pointType: 'unknown',
        pointId: 'invalid-id',
        PresentValue: 'N/A'
      };
    });
  };
  
  // Generate tags using AI
  const generateTagsWithAI = async (points, equipmentType = null) => {
    if (!points || points.length === 0) {
      console.error('No points provided for tagging');
      return;
    }
    
    setLoading(true);
    try {
      console.log(`Generating tags for ${points.length} points`);
      
      // Prepare request data
      const requestData = {
        points: points,
        equipment_type: equipmentType
      };
      
      // Make API request
      const response = await axios.post('/api/bms/generate-tags', requestData);
      
      // Update state with tagged points
      if (response.data && response.data.success) {
        return response.data.tagged_points;
      } else {
        console.error('Failed to generate tags:', response.data);
        return null;
      }
    } catch (error) {
      console.error('Error generating tags:', error);
      setError(error.message || 'Failed to generate tags');
      return null;
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <AppContext.Provider value={{
      rawPoints,
      setRawPoints,
      groupedPoints,
      setGroupedPoints,
      enosMapping,
      setEnosMapping,
      savedMappings,
      setSavedMappings,
      loading,
      setLoading,
      error,
      setError,
      fetchRawPoints,
      groupPointsByProperty,
      saveMappingToCsv,
      listSavedMappings,
      loadSavedMapping,
      groupPointsWithAI,
      generateTagsWithAI
    }}>
      {children}
    </AppContext.Provider>
  );
}; 