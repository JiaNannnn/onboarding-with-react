import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import GroupPoints from './GroupPoints';

// Mock the Card and Table components
jest.mock('../../components', () => ({
  Card: ({ children, className }: { children: React.ReactNode, className?: string }) => (
    <div data-testid="card" className={className}>{children}</div>
  ),
  Table: ({ columns, data, pagination, onPageChange }: any) => (
    <div data-testid="table">
      <div data-testid="table-columns">{JSON.stringify(columns)}</div>
      <div data-testid="table-data">{JSON.stringify(data)}</div>
      <div data-testid="table-pagination">{JSON.stringify(pagination)}</div>
      <button onClick={() => onPageChange(2)} data-testid="next-page">Next Page</button>
    </div>
  ),
}));

describe('GroupPoints Component', () => {
  test('renders upload card', () => {
    render(<GroupPoints />);
    
    expect(screen.getByText('Group Points')).toBeInTheDocument();
    expect(screen.getByText('Upload Points File')).toBeInTheDocument();
    expect(screen.getByText('Choose CSV or JSON file')).toBeInTheDocument();
  });

  test('shows error for unsupported file type', async () => {
    render(<GroupPoints />);
    
    const file = new File(['dummy content'], 'test.txt', { type: 'text/plain' });
    const fileInput = screen.getByLabelText('Choose CSV or JSON file');
    
    // Mock the file change event
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByText('Unsupported file format. Please upload CSV or JSON files only.')).toBeInTheDocument();
    });
  });

  test('parses CSV file and displays table', async () => {
    render(<GroupPoints />);
    
    // Create a sample CSV file with BACnet points data
    const csvContent = `objectType,otDeviceInst,objectInst,objectIdentifier,objectName,description,presentValue,covIncrement,unit,timestamp,assetId,deviceInstance,deviceAddress,pointName,pointType,source,pointId
analog-input,10102,0,"(analog-input,0)",FCU_01_25.RoomTemp,,27.9,1.0,degrees-Celsius,20250312_173540,5xkIipSH,10102,192.168.10.102:47808,FCU_01_25.RoomTemp,analog-input,bacnet,10102:0
binary-input,10102,1,"(binary-input,1)",DriverCH-SYS-1.CH.RunStatus,,active,,,20250312_173540,5xkIipSH,10102,192.168.10.102:47808,DriverCH-SYS-1.CH.RunStatus,binary-input,bacnet,10102:1`;
    
    const file = new File([csvContent], 'points.csv', { type: 'text/csv' });
    const fileInput = screen.getByLabelText('Choose CSV or JSON file');
    
    // Mock the file change event
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    await waitFor(() => {
      // Check that the table is displayed with the correct data
      expect(screen.getByTestId('table')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Points Data')).toBeInTheDocument();
    expect(screen.getByText('CSV')).toBeInTheDocument();
    expect(screen.getByText('2 points')).toBeInTheDocument();
  });

  test('parses JSON file and displays table', async () => {
    render(<GroupPoints />);
    
    // Create a sample JSON file with BACnet points data
    const jsonData = [
      {
        "id": "10102:0",
        "pointId": "10102:0",
        "objectType": "analog-input",
        "otDeviceInst": "10102",
        "objectInst": "0",
        "objectIdentifier": "(analog-input,0)",
        "objectName": "FCU_01_25.RoomTemp",
        "description": "",
        "presentValue": "27.9",
        "covIncrement": "1.0",
        "unit": "degrees-Celsius",
        "timestamp": "20250312_173540",
        "assetId": "5xkIipSH",
        "deviceInstance": "10102",
        "deviceAddress": "192.168.10.102:47808",
        "pointName": "FCU_01_25.RoomTemp",
        "pointType": "analog-input",
        "source": "bacnet"
      }
    ];
    
    const file = new File([JSON.stringify(jsonData)], 'points.json', { type: 'application/json' });
    const fileInput = screen.getByLabelText('Choose CSV or JSON file');
    
    // Mock the file change event
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    await waitFor(() => {
      // Check that the table is displayed with the correct data
      expect(screen.getByTestId('table')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Points Data')).toBeInTheDocument();
    expect(screen.getByText('JSON')).toBeInTheDocument();
    expect(screen.getByText('1 points')).toBeInTheDocument();
  });

  test('handles pagination correctly', async () => {
    render(<GroupPoints />);
    
    // Create sample data with more than 10 items to test pagination
    const points = Array.from({ length: 25 }, (_, i) => ({
      id: `point-${i}`,
      pointId: `${i}`,
      objectType: "analog-input",
      otDeviceInst: "10102",
      objectInst: `${i}`,
      objectIdentifier: `(analog-input,${i})`,
      objectName: `Point ${i}`,
      description: `Description ${i}`,
      presentValue: i,
      covIncrement: "1.0",
      unit: "degrees-Celsius",
      timestamp: "20250312_173540",
      assetId: "5xkIipSH",
      deviceInstance: "10102",
      deviceAddress: "192.168.10.102:47808",
      pointName: `Point ${i}`,
      pointType: "analog-input",
      source: "bacnet"
    }));

    const file = new File([JSON.stringify(points)], 'points.json', { type: 'application/json' });
    const fileInput = screen.getByLabelText('Choose CSV or JSON file');
    
    // Upload file
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    // Check initial pagination state
    await waitFor(() => {
      const paginationInfo = JSON.parse(screen.getByTestId('table-pagination').textContent || '{}');
      expect(paginationInfo.pageSize).toBe(10);
    });
    
    const paginationInfo = JSON.parse(screen.getByTestId('table-pagination').textContent || '{}');
    expect(paginationInfo.totalItems).toBe(25);
    expect(paginationInfo.page).toBe(1);

    // Test page size change
    const pageSizeSelect = screen.getByLabelText('Items per page:');
    fireEvent.change(pageSizeSelect, { target: { value: '20' } });

    await waitFor(() => {
      const paginationInfo = JSON.parse(screen.getByTestId('table-pagination').textContent || '{}');
      expect(paginationInfo.pageSize).toBe(20);
    });
    
    const newPaginationInfo = JSON.parse(screen.getByTestId('table-pagination').textContent || '{}');
    expect(newPaginationInfo.page).toBe(1); // Should reset to page 1

    // Test page change
    fireEvent.click(screen.getByTestId('next-page'));
    
    await waitFor(() => {
      const paginationInfo = JSON.parse(screen.getByTestId('table-pagination').textContent || '{}');
      expect(paginationInfo.page).toBe(2);
    });
  });
}); 