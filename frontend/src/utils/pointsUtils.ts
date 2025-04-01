import { BMSPoint, BMSPointRaw, FetchPointsResponse } from '../types/apiTypes';

/**
 * Map a raw point from the API to the standard format
 */
export function mapRawPoint(rawPoint: BMSPointRaw): BMSPoint {
  return {
    id: rawPoint.id || rawPoint.pointId || `point-${Math.random().toString(36).substring(2, 9)}`,
    pointName: rawPoint.pointName || '',
    pointType: rawPoint.pointType || 'Unknown',
    unit: rawPoint.unit || '',
    description: rawPoint.description || '',
    value: rawPoint.value,
    timestamp: rawPoint.timestamp,
    status: rawPoint.status
  };
}

/**
 * Convert a response from the API to a standardized points array
 */
export function convertPointsFromResponse(response: FetchPointsResponse): BMSPoint[] {
  if (response?.record && Array.isArray(response.record)) {
    return response.record.map(mapRawPoint);
  }
  return [];
}

/**
 * Find a point in an array by ID
 */
export function findPointById(points: BMSPoint[], id: string): BMSPoint | undefined {
  return points.find(point => point.id === id);
}

/**
 * Filter an array of points by search term and/or point types
 */
export function filterPoints(
  points: BMSPoint[], 
  searchTerm: string = '', 
  selectedTypes: string[] = []
): BMSPoint[] {
  // If no filters active, return all points
  if (!searchTerm && selectedTypes.length === 0) {
    return points;
  }
  
  const lowercaseSearch = searchTerm.toLowerCase();
  
  return points.filter(point => {
    // Apply type filter if selected types exist
    const matchesType = selectedTypes.length === 0 || 
      selectedTypes.includes(point.pointType);
    
    // Apply search filter if search term exists
    const matchesSearch = !searchTerm || 
      point.pointName.toLowerCase().includes(lowercaseSearch) ||
      point.description.toLowerCase().includes(lowercaseSearch);
    
    return matchesType && matchesSearch;
  });
} 