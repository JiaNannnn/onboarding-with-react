import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} AppContextType
 * @property {Array} rawPoints - Array of raw points
 * @property {Object} groupedPoints - Points grouped by property
 * @property {Object} hierarchicalGroups - Points grouped hierarchically
 * @property {Object} groupTags - Tags for each group
 * @property {Array} savedFiles - List of saved files
 * @property {boolean} loading - Loading state
 * @property {Object|null} error - Error state
 * @property {Object} pointTags - Tags for individual points
 * @property {function(Array): void} setRawPoints - Set raw points
 * @property {function(Object): void} setHierarchicalGroups - Set hierarchical groups
 * @property {function(Array, string, boolean=): Object} groupPointsByProperty - Group points by property with optional hierarchical flag
 * @property {function(string, string): boolean} addGroupTag - Add a tag to a group
 * @property {function(string, number): boolean} removeGroupTag - Remove a tag from a group
 * @property {function(string, number, string): boolean} updateGroupTag - Update a tag in a group
 * @property {function(string, string=): boolean} tagPointsInGroup - Tag all points in a group
 * @property {function(Object): void} setGroupTags - Set group tags
 * @property {function(): Promise<Array>} listSavedFiles - List saved files
 * @property {function(string): Promise<Object|null>} loadSavedFile - Load a saved file
 * @property {function(Array, string): Array} filterPointsByTag - Filter points by tag
 */

/** @type {AppContextType} */
const defaultContext = {
  rawPoints: [],
  groupedPoints: {},
  savedFiles: [],
  loading: false,
  error: null,
  hierarchicalGroups: {},
  groupTags: {},
  pointTags: {},
  setHierarchicalGroups: () => {},
  setRawPoints: () => {},
  listSavedFiles: () => Promise.resolve([]),
  loadSavedFile: (filepath) => Promise.resolve(null),
  filterPointsByTag: (points, tag) => [],
  setGroupTags: () => {},
  groupPointsByProperty: () => ({}),
  addGroupTag: () => false,
  removeGroupTag: () => false,
  updateGroupTag: () => false,
  tagPointsInGroup: () => false,
};

export const AppContext = createContext(defaultContext);

// Custom hook to use the context
export const useAppContext = () => useContext(AppContext);

export const AppProvider = ({ children }) => {
  // State for raw points data
  const [rawPoints, setRawPoints] = useState([]);

  // State for grouped points
  const [groupedPoints, setGroupedPoints] = useState({});

  // State for saved files
  const [savedFiles, setSavedFiles] = useState([]);

  // State for loading status
  const [loading, setLoading] = useState(false);

  // State for error messages
  const [error, setError] = useState(null);

  // State for AI-grouped points - hierarchical structure by model and device
  const [hierarchicalGroups, setHierarchicalGroups] = useState({});

  // State for group tags - organized by group name
  const [groupTags, setGroupTags] = useState({});

  // State for point tags - maps pointName to an array of tags
  const [pointTags /* setPointTags */] = useState({});

  // Wrapped setter function with validation
  const safeSetHierarchicalGroups = (groups) => {
    try {
      // Validate that groups is an object
      if (!groups || typeof groups !== 'object' || Array.isArray(groups)) {
        console.error('Invalid hierarchical groups format:', groups);
        console.error('Expected an object but got:', typeof groups);
        // Set to empty object as fallback
        setHierarchicalGroups({});
        return;
      }

      // Validate each group has the required structure
      const validatedGroups = {};

      Object.entries(groups).forEach(([groupName, group]) => {
        // Ensure group is an object
        if (!group || typeof group !== 'object') {
          console.warn(`Group ${groupName} is not an object, skipping`);
          return;
        }

        // Ensure points is an array
        const points = Array.isArray(group.points) ? group.points : [];

        // Ensure subgroups is an object
        let subgroups = {};
        if (
          group.subgroups &&
          typeof group.subgroups === 'object' &&
          !Array.isArray(group.subgroups)
        ) {
          // Validate each subgroup
          Object.entries(group.subgroups).forEach(([subgroupName, subgroupPoints]) => {
            subgroups[subgroupName] = Array.isArray(subgroupPoints) ? subgroupPoints : [];
          });
        }

        // Add validated group
        validatedGroups[groupName] = {
          ...group,
          points: points,
          subgroups: subgroups,
        };
      });

      // Set the validated groups
      setHierarchicalGroups(validatedGroups);
    } catch (error) {
      console.error('Error setting hierarchical groups:', error);
      // Set to empty object as fallback
      setHierarchicalGroups({});
    }
  };

  // Helper function to extract equipment type from point name
  const extractEquipmentTypeFromName = (pointName) => {
    if (!pointName) return 'Unknown';

    // Common equipment prefixes and patterns to recognize
    // eslint-disable-next-line no-useless-escape
    const equipmentPatterns = [
      { type: 'AHU', patterns: [/^AHU/i, /\.AHU\./i, /AHU[_\-\.]/i] },
      { type: 'VAV', patterns: [/^VAV/i, /\.VAV\./i, /VAV[_\-\.]/i] },
      { type: 'FCU', patterns: [/^FCU/i, /\.FCU\./i, /FCU[_\-\.]/i] },
      {
        type: 'CH',
        patterns: [/^CH/i, /^CHL/i, /[_\-.]CH[_\-.]/i, /[_\-.]CHL[_\-.]/i, /CHILLER/i, /\bCH\b/i],
      },
      { type: 'CT', patterns: [/^CT/i, /\.CT\./i, /CT[_\-\.]/i, /COOLING.?TOWER/i] },
      {
        type: 'PUMP',
        patterns: [/^PUMP/i, /\.PUMP\./i, /PUMP[_\-\.]/i, /\b[CP]WP\b/i, /\bCHWP\b/i],
      },
      { type: 'FAN', patterns: [/^FAN/i, /\.FAN\./i, /FAN[_\-\.]/i] },
      { type: 'BOILER', patterns: [/^BOILER/i, /\.BOILER\./i, /BOILER[_\-\.]/i] },
      { type: 'HW', patterns: [/^HW[_\-\.]/i, /\.HW\./i, /\bHW\b/i] },
    ];

    // Check each pattern against the pointName
    for (const { type, patterns } of equipmentPatterns) {
      for (const pattern of patterns) {
        if (pattern.test(pointName)) {
          console.log(
            `Point "${pointName}" matched equipment type "${type}" using pattern ${pattern}`
          );
          return type;
        }
      }
    }

    // Extract any leading alphabetic characters as fallback
    const match = pointName.match(/^([A-Za-z]+)/);
    console.log(`Point "${pointName}" using fallback detection: ${match ? match[1] : 'Unknown'}`);
    return match ? match[1] : 'Unknown';
  };

  // Group points by property
  const groupPointsByProperty = (points, property) => {
    if (!points || !Array.isArray(points) || points.length === 0 || !property) {
      console.log('Invalid input to groupPointsByProperty:', { points, property });
      return {};
    }

    console.log('groupPointsByProperty called');

    // Preprocess points to add equipmentType if needed
    let processedPoints = points;
    if (property === 'equipmentType') {
      console.log('Preprocessing points to extract equipment types');
      processedPoints = points.map((point) => {
        if (!point.equipmentType) {
          // Extract equipment type from objectName (since it has same value as pointName)
          const equipmentType = extractEquipmentTypeFromName(point.objectName);
          return { ...point, equipmentType };
        }
        return point;
      });
    }

    // For backward compatibility or local grouping
    const localGroups = processedPoints.reduce((acc, point) => {
      if (!point) return acc;

      const value = point[property] || 'Unknown';
      if (!acc[value]) {
        acc[value] = [];
      }
      acc[value].push(point);
      return acc;
    }, {});

    // Create model groups with subgroups
    const modelGroups = {};

    Object.entries(localGroups).forEach(([groupName, groupPoints]) => {
      if (!groupName || !Array.isArray(groupPoints)) return;

      modelGroups[groupName] = {
        points: groupPoints || [],
        subgroups: {},
      };

      // If we're grouping by equipment type, create subgroups by instance number
      if (property === 'equipmentType' && groupName !== 'Unknown') {
        console.log(`Creating instance subgroups for ${groupName}`);
        const instanceGroups = groupPointsByEquipmentInstance(groupPoints, groupName);
        modelGroups[groupName].subgroups = instanceGroups;
      }
    });

    console.log('Created model groups:', Object.keys(modelGroups));
    safeSetHierarchicalGroups(modelGroups);

    // For non-hierarchical grouping, just use local grouping
    console.log('Setting groupedPoints:', localGroups);
    setGroupedPoints(localGroups);
    return localGroups;
  };

  // Helper function to group points by equipment instance
  const groupPointsByEquipmentInstance = (points, equipmentType) => {
    const instanceGroups = {};

    points.forEach((point) => {
      const objectName = point.objectName || '';

      // Extract the instance number or identifier (e.g., "1" from "AHU-1.SupplyTemp")
      const regex = new RegExp(`^${equipmentType}[-._\\s]?(\\w+)`);
      const match = objectName.match(regex);

      let instanceId = 'Other';
      if (match && match[1]) {
        instanceId = match[1];
      }

      const instanceName = `${equipmentType}-${instanceId}`;

      if (!instanceGroups[instanceName]) {
        instanceGroups[instanceName] = [];
      }

      instanceGroups[instanceName].push(point);
    });

    return instanceGroups;
  };

  // Add a tag to a group
  const addGroupTag = (group, tag) => {
    if (!group || !tag) {
      return false;
    }

    // Initialize group tags if they don't exist yet
    const updatedTags = {
      ...groupTags,
      [group]: [...(groupTags[group] || []), tag],
    };

    setGroupTags(updatedTags);
    return true;
  };

  // Remove a tag from a group
  const removeGroupTag = (group, index) => {
    if (!group || !groupTags[group] || index < 0 || index >= groupTags[group].length) {
      return false;
    }

    const updatedTags = {
      ...groupTags,
      [group]: groupTags[group].filter((_, i) => i !== index),
    };
    setGroupTags(updatedTags);
    return true;
  };

  // Update a tag value
  const updateGroupTag = (group, index, newTag) => {
    if (!group || !groupTags[group] || !newTag || index < 0 || index >= groupTags[group].length) {
      return false;
    }

    const updatedTags = {
      ...groupTags,
      [group]: groupTags[group].map((tag, i) => (i === index ? newTag : tag)),
    };
    setGroupTags(updatedTags);
    return true;
  };

  // Apply group tags to all points in a group
  const tagPointsInGroup = (group, subgroup = null) => {
    if (!group) {
      console.log('No group specified for tagging');
      return false;
    }

    if (!groupTags[group] || groupTags[group].length === 0) {
      console.log('No tags available for group:', group);
      return false;
    }

    let points;

    if (subgroup) {
      points = hierarchicalGroups?.[group]?.subgroups?.[subgroup];
    } else {
      points = hierarchicalGroups?.[group]?.points || groupedPoints?.[group];
    }

    if (!points || !Array.isArray(points) || points.length === 0) {
      console.log('No points found in group/subgroup:', { group, subgroup });
      return false;
    }

    console.log('Tagging points:', {
      group,
      subgroup,
      pointCount: points.length,
      tags: groupTags[group],
    });

    const updatedPoints = points.map((point) => ({
      ...point,
      tags: [...(point.tags || []), ...groupTags[group]],
    }));

    if (subgroup) {
      safeSetHierarchicalGroups((prev) => {
        if (!prev?.[group]?.subgroups) {
          console.warn('Cannot update subgroups - structure not initialized properly');
          return prev;
        }

        return {
          ...prev,
          [group]: {
            ...prev[group],
            subgroups: {
              ...prev[group].subgroups,
              [subgroup]: updatedPoints,
            },
          },
        };
      });
    } else if (hierarchicalGroups?.[group]) {
      safeSetHierarchicalGroups((prev) => {
        if (!prev?.[group]) {
          console.warn('Cannot update hierarchical groups - structure not initialized properly');
          return prev;
        }

        return {
          ...prev,
          [group]: {
            ...prev[group],
            points: updatedPoints,
          },
        };
      });
    } else {
      setGroupedPoints((prev) => ({
        ...prev,
        [group]: updatedPoints,
      }));
    }

    return true;
  };

  // Filter points by tag
  const filterPointsByTag = (points, tag) => {
    if (!tag || !points || points.length === 0) return points;

    return points.filter((point) => {
      const tags = pointTags[point.pointName] || [];
      return tags.includes(tag);
    });
  };

  // List saved files
  const listSavedFiles = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get('/api/v1/files/list');

      if (response.data.success) {
        setSavedFiles(response.data.files);
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

  // Load a saved file
  const loadSavedFile = async (filename) => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(`/api/v1/files/download/${filename}`, {
        responseType: 'blob',
      });

      // Create a URL for the blob
      const url = window.URL.createObjectURL(new Blob([response.data]));

      // Create a temporary link and click it to download
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();

      // Clean up
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);

      return true;
    } catch (err) {
      setError(err.message || 'An error occurred while loading file');
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Group points using AI
  const aiGroupPoints = async (points) => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/v1/points/group', { points });

      if (response.data.success) {
        return response.data.groups;
      } else {
        setError(response.data.error || 'Failed to group points');
        return null;
      }
    } catch (err) {
      setError(err.message || 'An error occurred while grouping points');
      return null;
    } finally {
      setLoading(false);
    }
  };

  // Load saved files on component mount
  useEffect(() => {
    listSavedFiles();
  }, []);

  // Context value
  const contextValue = {
    rawPoints,
    groupedPoints,
    savedFiles,
    loading,
    error,
    hierarchicalGroups,
    setHierarchicalGroups: safeSetHierarchicalGroups,
    groupTags,
    pointTags,
    setRawPoints,
    listSavedFiles,
    loadSavedFile,
    filterPointsByTag,
    setGroupTags,
    groupPointsByProperty,
    addGroupTag,
    removeGroupTag,
    updateGroupTag,
    tagPointsInGroup,
    aiGroupPoints,
  };

  return <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>;
};
