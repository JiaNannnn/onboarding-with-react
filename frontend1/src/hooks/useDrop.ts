import { useRef } from 'react';

// Define a type for the monitor object to avoid 'any'
export interface DropMonitor {
  isOver: () => boolean;
  canDrop: () => boolean;
  getItem: () => any;
  getItemType: () => string;
  [key: string]: any;
}

interface DropOptions<T, R> {
  accept: string | string[];
  drop?: (item: T, monitor: DropMonitor) => any;
  collect: (monitor: DropMonitor) => R;
  canDrop?: (item: T, monitor: DropMonitor) => boolean;
  hover?: (item: T, monitor: DropMonitor) => void;
}

/**
 * Mock implementation of useDrop
 * In a real application, we would use the real react-dnd implementation
 */
export function useDrop<T, D = {}, R = { isOver: boolean; canDrop: boolean }>(options: DropOptions<T, R>) {
  const ref = useRef(null);
  
  // Create a mock drop state based on the collect function
  const dropState = options.collect({
    isOver: () => false,
    canDrop: () => true,
    getItem: () => ({}),
    getItemType: () => typeof options.accept === 'string' ? options.accept : options.accept[0],
    // Add other monitor methods as needed
  });
  
  return [dropState, ref] as [R, React.RefObject<any>];
} 