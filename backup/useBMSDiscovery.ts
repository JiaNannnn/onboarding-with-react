/**
 * A custom hook for BMS discovery operations
 * 
 * This hook provides functions for:
 * - Loading network configurations
 * - Discovering devices on selected networks
 * - Searching for points across devices
 * - Managing the discovery state
 */

import { useState, useCallback } from 'react';
import { createBMSClient, NetworkInterface, DeviceDiscoveryStatusResponse } from '../api/bmsClient';

/**
 * BMS Service configuration interface
 */
export interface BMSDiscoveryConfig {
  apiGateway?: string;
  accessKey: string;
  secretKey: string;
  orgId?: string;
  assetId?: string;
}

/**
 * Discovery state interface
 */
export interface DiscoveryState {
  networks: NetworkInterface[];
  selectedNetworks: string[];
  devices: Array<{
    instanceNumber: number;
    name: string;
    address: string;
    model?: string;
    vendor?: string;
  }>;
  discoveryStatus: 'idle' | 'loading-networks' | 'network-ready' | 'discovering' | 'discovered' | 'error';
  error: string | null;
}

/**
 * Default configuration
 */
const defaultConfig: BMSDiscoveryConfig = {
  apiGateway: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  accessKey: '',
  secretKey: '',
};

/**
 * Custom hook for BMS discovery operations
 */
export function useBMSDiscovery(config: BMSDiscoveryConfig = defaultConfig) {
  // State for the discovery process
  const [state, setState] = useState<DiscoveryState>({
    networks: [],
    selectedNetworks: [],
    devices: [],
    discoveryStatus: 'idle',
    error: null,
  });

  // Create BMS client
  const bmsClient = useCallback(() => {
    return createBMSClient(config);
  }, [config]);

  /**
   * Load available networks
   */
  const loadNetworks = useCallback(async () => {
    try {
      setState(prevState => ({
        ...prevState,
        discoveryStatus: 'loading-networks',
        error: null,
      }));

      const client = bmsClient();
      const networks = await client.getNetworkConfig();

      setState(prevState => ({
        ...prevState,
        networks,
        discoveryStatus: 'network-ready',
      }));

      return networks;
    } catch (error) {
      console.error('Error loading networks:', error);
      setState(prevState => ({
        ...prevState,
        discoveryStatus: 'error',
        error: error instanceof Error ? error.message : 'Failed to load networks',
      }));
      throw error;
    }
  }, [bmsClient]);

  /**
   * Toggle a network selection
   */
  const selectNetwork = useCallback((networkName: string, selected: boolean) => {
    setState(prevState => {
      const selectedNetworks = selected
        ? [...prevState.selectedNetworks, networkName]
        : prevState.selectedNetworks.filter(name => name !== networkName);

      return {
        ...prevState,
        selectedNetworks,
      };
    });
  }, []);

  /**
   * Start device discovery on selected networks
   */
  const startDiscovery = useCallback(async () => {
    try {
      setState(prevState => ({
        ...prevState,
        discoveryStatus: 'discovering',
        error: null,
      }));

      const client = bmsClient();
      
      // Don't proceed if no networks are selected
      if (state.selectedNetworks.length === 0) {
        throw new Error('No networks selected for discovery');
      }

      // Start device discovery
      const deviceDiscoveryResponse = await client.discoverDevices(
        state.selectedNetworks,
        'bacnet'
      );

      // Get task ID from response
      const deviceTaskId = deviceDiscoveryResponse.task_id || deviceDiscoveryResponse.taskId;
      if (!deviceTaskId) {
        throw new Error('No task ID returned from discovery request');
      }

      // Poll until discovery is complete
      const deviceDiscoveryResult = await client.pollUntilComplete<DeviceDiscoveryStatusResponse>(
        () => client.checkDeviceDiscoveryStatus(deviceTaskId),
        response => response.status === 'completed',
        5000
      );

      // Extract devices from result
      const devices = 
        deviceDiscoveryResult.result?.devices || 
        (deviceDiscoveryResult.result?.all_devices || []).map(d => ({
          instanceNumber: d.otDeviceInst,
          name: d.deviceName,
          address: d.address
        }));

      setState(prevState => ({
        ...prevState,
        devices,
        discoveryStatus: 'discovered',
      }));

      return devices;
    } catch (error) {
      console.error('Error discovering devices:', error);
      setState(prevState => ({
        ...prevState,
        discoveryStatus: 'error',
        error: error instanceof Error ? error.message : 'Failed to discover devices',
      }));
      throw error;
    }
  }, [bmsClient, state.selectedNetworks]);

  /**
   * Search for points across discovered devices
   */
  const searchPoints = useCallback(async () => {
    try {
      const client = bmsClient();
      
      // Don't proceed if no devices were discovered
      if (state.devices.length === 0) {
        throw new Error('No devices discovered');
      }

      // Get device instance numbers
      const deviceInstances = state.devices.map(d => d.instanceNumber);

      // Start points search
      const pointsSearchResponse = await client.initiatePointsSearch(
        deviceInstances,
        'bacnet'
      );

      // Get task ID from response
      const pointsTaskId = pointsSearchResponse.task_id || pointsSearchResponse.taskId;
      if (!pointsTaskId) {
        throw new Error('No task ID returned from points search request');
      }

      // Poll until search is complete
      const pointsSearchResult = await client.pollUntilComplete(
        () => client.checkPointsSearchStatus(pointsTaskId),
        response => response.status === 'completed',
        5000
      );

      return pointsSearchResult;
    } catch (error) {
      console.error('Error searching for points:', error);
      throw error;
    }
  }, [bmsClient, state.devices]);

  /**
   * Reset discovery state
   */
  const reset = useCallback(() => {
    setState({
      networks: [],
      selectedNetworks: [],
      devices: [],
      discoveryStatus: 'idle',
      error: null,
    });
  }, []);

  return {
    state,
    loadNetworks,
    selectNetwork,
    startDiscovery,
    searchPoints,
    reset,
  };
}

export default useBMSDiscovery;