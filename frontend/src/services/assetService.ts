import { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import { Asset } from '../components/AssetSelector/AssetSelector';

interface FetchAssetsOptions {
  mock?: boolean;
  orgId?: string;
  filterByStatus?: 'active' | 'inactive' | 'maintenance' | 'all';
  filterByType?: string;
  search?: string;
}

interface FetchAssetDetailsOptions {
  mock?: boolean;
  assetId: string;
}

interface FetchDevicesOptions {
  mock?: boolean;
  assetId: string;
}

interface Device {
  id: string;
  name: string;
  type: string;
  instance: string;
  address?: string;
  pointsCount?: number;
  status?: 'online' | 'offline' | 'warning';
}

// Mock assets for development with expanded data
const MOCK_ASSETS: Asset[] = [
  {
    id: 'asset1',
    name: 'Building 1',
    type: 'Office Building',
    deviceCount: 42,
    description: 'Main office building with 5 floors',
    location: 'New York, NY',
    status: 'active',
    lastUpdated: '2023-05-15T10:00:00Z'
  },
  {
    id: 'asset2',
    name: 'Building 2',
    type: 'Warehouse',
    deviceCount: 28,
    description: 'Storage and distribution center',
    location: 'Chicago, IL',
    status: 'active',
    lastUpdated: '2023-06-20T14:30:00Z'
  },
  {
    id: 'asset3',
    name: 'Building 3',
    type: 'Manufacturing',
    deviceCount: 64,
    description: 'Production facility',
    location: 'Detroit, MI',
    status: 'maintenance',
    lastUpdated: '2023-07-05T09:15:00Z'
  },
  {
    id: 'asset4',
    name: 'Building 4',
    type: 'Data Center',
    deviceCount: 35,
    description: 'Server and network infrastructure',
    location: 'San Jose, CA',
    status: 'active',
    lastUpdated: '2023-04-30T16:45:00Z'
  },
  {
    id: 'asset5',
    name: 'Building 5',
    type: 'Office Building',
    deviceCount: 23,
    description: 'Regional headquarters',
    location: 'Boston, MA',
    status: 'inactive',
    lastUpdated: '2023-02-10T11:20:00Z'
  },
  {
    id: 'asset6',
    name: 'Building 6',
    type: 'Retail',
    deviceCount: 15,
    description: 'Flagship retail store',
    location: 'Los Angeles, CA',
    status: 'active',
    lastUpdated: '2023-08-01T08:00:00Z'
  },
  {
    id: 'asset7',
    name: 'Building 7',
    type: 'Healthcare',
    deviceCount: 52,
    description: 'Medical center with advanced HVAC',
    location: 'Houston, TX',
    status: 'active',
    lastUpdated: '2023-07-15T13:10:00Z'
  }
];

// Mock devices for development
const MOCK_DEVICES: Record<string, Device[]> = {
  'asset1': [
    { id: 'dev1-1', name: 'AHU-1', type: 'Air Handler', instance: '3001', address: '192.168.1.101', pointsCount: 24, status: 'online' },
    { id: 'dev1-2', name: 'AHU-2', type: 'Air Handler', instance: '3002', address: '192.168.1.102', pointsCount: 24, status: 'online' },
    { id: 'dev1-3', name: 'VAV-1', type: 'Variable Air Volume', instance: '4001', address: '192.168.1.201', pointsCount: 12, status: 'online' },
    { id: 'dev1-4', name: 'VAV-2', type: 'Variable Air Volume', instance: '4002', address: '192.168.1.202', pointsCount: 12, status: 'warning' }
  ],
  'asset2': [
    { id: 'dev2-1', name: 'RTU-1', type: 'Rooftop Unit', instance: '5001', address: '192.168.2.101', pointsCount: 18, status: 'online' },
    { id: 'dev2-2', name: 'RTU-2', type: 'Rooftop Unit', instance: '5002', address: '192.168.2.102', pointsCount: 18, status: 'offline' }
  ],
  'asset3': [
    { id: 'dev3-1', name: 'Boiler-1', type: 'Boiler', instance: '6001', address: '192.168.3.101', pointsCount: 30, status: 'online' },
    { id: 'dev3-2', name: 'Chiller-1', type: 'Chiller', instance: '7001', address: '192.168.3.201', pointsCount: 36, status: 'online' }
  ]
};

/**
 * Apply filters to assets
 */
const applyFilters = (assets: Asset[], options: FetchAssetsOptions): Asset[] => {
  let filtered = [...assets];
  
  // Filter by status
  if (options.filterByStatus && options.filterByStatus !== 'all') {
    filtered = filtered.filter(asset => asset.status === options.filterByStatus);
  }
  
  // Filter by type
  if (options.filterByType) {
    filtered = filtered.filter(asset => asset.type === options.filterByType);
  }
  
  // Filter by search term
  if (options.search) {
    const search = options.search.toLowerCase();
    filtered = filtered.filter(asset => 
      asset.name.toLowerCase().includes(search) || 
      asset.description?.toLowerCase().includes(search) ||
      asset.location?.toLowerCase().includes(search)
    );
  }
  
  return filtered;
};

/**
 * Fetches assets from the API
 * @param options Options for fetching assets
 * @returns Promise with assets
 */
export const fetchAssets = async (options: FetchAssetsOptions = {}): Promise<Asset[]> => {
  const { mock = false, orgId } = options;

  if (mock) {
    return new Promise(resolve => {
      setTimeout(() => {
        const filtered = applyFilters(MOCK_ASSETS, options);
        resolve(filtered);
      }, 500);
    });
  }

  try {
    // In a real implementation, this would call the actual API endpoint
    // With the appropriate filters in the query parameters
    const apiUrl = `${process.env.REACT_APP_API_BASE_URL || ''}/api/assets`;
    
    const params: Record<string, string> = {};
    if (orgId) params.orgId = orgId;
    if (options.filterByStatus) params.status = options.filterByStatus;
    if (options.filterByType) params.type = options.filterByType;
    if (options.search) params.search = options.search;
    
    const response = await axios.get(apiUrl, { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching assets:', error);
    throw error;
  }
};

/**
 * Fetches detailed information about a specific asset
 * @param options Options for fetching asset details
 * @returns Promise with detailed asset information
 */
export const fetchAssetDetails = async (options: FetchAssetDetailsOptions): Promise<Asset | null> => {
  const { mock = false, assetId } = options;

  if (!assetId) {
    throw new Error('Asset ID is required');
  }

  if (mock) {
    return new Promise(resolve => {
      setTimeout(() => {
        const asset = MOCK_ASSETS.find(a => a.id === assetId) || null;
        resolve(asset);
      }, 300);
    });
  }

  try {
    const apiUrl = `${process.env.REACT_APP_API_BASE_URL || ''}/api/assets/${assetId}`;
    const response = await axios.get(apiUrl);
    return response.data;
  } catch (error) {
    console.error(`Error fetching details for asset ${assetId}:`, error);
    throw error;
  }
};

/**
 * Fetches devices for a specific asset
 * @param options Options for fetching devices
 * @returns Promise with devices
 */
export const fetchDevices = async (options: FetchDevicesOptions): Promise<Device[]> => {
  const { mock = false, assetId } = options;

  if (!assetId) {
    throw new Error('Asset ID is required');
  }

  if (mock) {
    return new Promise(resolve => {
      setTimeout(() => {
        const devices = MOCK_DEVICES[assetId] || [];
        resolve(devices);
      }, 500);
    });
  }

  try {
    const apiUrl = `${process.env.REACT_APP_API_BASE_URL || ''}/api/assets/${assetId}/devices`;
    const response = await axios.get(apiUrl);
    return response.data;
  } catch (error) {
    console.error(`Error fetching devices for asset ${assetId}:`, error);
    throw error;
  }
};

/**
 * Hook for fetching and managing assets
 * @param options Options for fetching assets
 * @returns Object with assets, loading state, error, and refetch function
 */
export const useAssets = (options: FetchAssetsOptions = {}) => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await fetchAssets(options);
      setAssets(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch assets');
      console.error('Error in useAssets hook:', err);
    } finally {
      setIsLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [options]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    assets,
    isLoading,
    error,
    refetch: fetchData
  };
};

/**
 * Hook for fetching and managing devices for an asset
 * @param options Options for fetching devices
 * @returns Object with devices, loading state, error, and refetch function
 */
export const useDevices = (options: FetchDevicesOptions) => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!options.assetId) {
      setDevices([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await fetchDevices(options);
      setDevices(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch devices');
      console.error('Error in useDevices hook:', err);
    } finally {
      setIsLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [options, options.assetId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    devices,
    isLoading,
    error,
    refetch: fetchData
  };
}; 