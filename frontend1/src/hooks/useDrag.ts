import { useRef } from 'react';

// Define a type for the monitor object to avoid 'any'
export interface DragMonitor {
  isDragging: () => boolean;
  getItem: () => any;
  getItemType: () => string;
  [key: string]: any;
}

interface DragOptions<T, R> {
  type: string;
  item: T;
  collect: (monitor: DragMonitor) => R;
}

/**
 * Mock implementation of useDrag
 * In a real application, we would use the real react-dnd implementation
 */
export function useDrag<T, D = {}, R = { isDragging: boolean }>(options: DragOptions<T, R>) {
  const ref = useRef(null);
  
  // Create a mock drag state based on the collect function
  const dragState = options.collect({
    isDragging: () => false,
    getItem: () => options.item,
    getItemType: () => options.type,
    // Add other monitor methods as needed
  });
  
  return [dragState, ref] as [R, React.RefObject<any>];
} 