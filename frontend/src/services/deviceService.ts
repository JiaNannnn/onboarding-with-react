import { useEffect, useState, useCallback } from 'react';
import axios from 'axios';

export interface Device {
  id: string;
  name: string;
  type: string;
  instance: string;
  address?: string;
  pointsCount?: number;
  status?: 'online' | 'offline' | 'warning';
}

interface FetchDevicesOptions {
  mock?: boolean;
  assetId: string;
}

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
  ],
  'asset4': [
    { id: 'dev4-1', name: 'UPS-1', type: 'Power Supply', instance: '8001', address: '192.168.4.101', pointsCount: 15, status: 'online' },
    { id: 'dev4-2', name: 'UPS-2', type: 'Power Supply', instance: '8002', address: '192.168.4.102', pointsCount: 15, status: 'warning' },
    { id: 'dev4-3', name: 'Cooling-1', type: 'CRAC', instance: '9001', address: '192.168.4.201', pointsCount: 28, status: 'online' },
  ],
  'asset5': [
    { id: 'dev5-1', name: 'VAV-1', type: 'Variable Air Volume', instance: '10001', address: '192.168.5.101', pointsCount: 12, status: 'online' },
    { id: 'dev5-2', name: 'VAV-2', type: 'Variable Air Volume', instance: '10002', address: '192.168.5.102', pointsCount: 12, status: 'offline' }
  ],
  'asset6': [
    { id: 'dev6-1', name: 'RTU-1', type: 'Rooftop Unit', instance: '11001', address: '192.168.6.101', pointsCount: 16, status: 'online' }
  ],
  'asset7': [
    { id: 'dev7-1', name: 'AHU-1', type: 'Air Handler', instance: '12001', address: '192.168.7.101', pointsCount: 24, status: 'online' },
    { id: 'dev7-2', name: 'VAV-1', type: 'Variable Air Volume', instance: '13001', address: '192.168.7.201', pointsCount: 12, status: 'online' },
    { id: 'dev7-3', name: 'VAV-2', type: 'Variable Air Volume', instance: '13002', address: '192.168.7.202', pointsCount: 12, status: 'online' },
    { id: 'dev7-4', name: 'Cooling-1', type: 'Chiller', instance: '14001', address: '192.168.7.301', pointsCount: 36, status: 'online' }
  ]
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
  }, [options]);

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