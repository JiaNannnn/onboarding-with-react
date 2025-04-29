import React from 'react';
import {
  DataGrid,
  DataGridProps,
  GridColDef,
  GridRowsProp,
  GridToolbar,
  GridToolbarContainer,
  GridToolbarColumnsButton,
  GridToolbarDensitySelector,
  GridToolbarExport,
  GridToolbarFilterButton,
} from '@mui/x-data-grid';
import { Box, Paper, Typography, CircularProgress } from '@mui/material';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import { EmptyState } from './EmptyState';

export interface DataTableProps extends Omit<DataGridProps, 'rows' | 'columns'> {
  columns: GridColDef[];
  rows: GridRowsProp;
  title?: string;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  pageSize?: number;
  height?: string | number;
  disableRowSelectionOnClick?: boolean;
  disableDensitySelector?: boolean;
  disableColumnMenu?: boolean;
  disableColumnFilter?: boolean;
  disableColumnSelector?: boolean;
  disableExport?: boolean;
  checkboxSelection?: boolean;
  autoHeight?: boolean;
  emptyMessage?: string;
}

/**
 * Custom toolbar component for DataGrid
 */
const CustomToolbar: React.FC<{
  disableExport?: boolean;
  disableFilters?: boolean;
}> = ({ disableExport, disableFilters }) => {
  return (
    <GridToolbarContainer>
      {!disableFilters && <GridToolbarFilterButton />}
      {!disableExport && <GridToolbarExport />}
    </GridToolbarContainer>
  );
};

/**
 * Reusable data table component built on MUI DataGrid
 */
export const DataTable: React.FC<DataTableProps> = ({
  columns,
  rows,
  title,
  loading = false,
  error = null,
  onRetry,
  pageSize = 25,
  height = 400,
  disableRowSelectionOnClick = true,
  disableDensitySelector = false,
  disableColumnMenu = false,
  disableColumnFilter = false,
  disableColumnSelector = false,
  disableExport = false,
  checkboxSelection = false,
  autoHeight = false,
  emptyMessage = 'No data available',
  ...rest
}) => {
  // Handle empty state
  const NoRowsOverlay = () => (
    <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <EmptyState 
        title="No Data" 
        description={emptyMessage} 
      />
    </Box>
  );

  // Handle loading state
  const LoadingOverlay = () => (
    <Box sx={{ 
      position: 'absolute', 
      top: 0, 
      left: 0, 
      right: 0, 
      bottom: 0, 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      backgroundColor: 'rgba(255, 255, 255, 0.7)'
    }}>
      <CircularProgress />
    </Box>
  );

  return (
    <Paper elevation={2} sx={{ p: 2, height: '100%' }}>
      {title && (
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
      )}

      {error ? (
        <Alert
          severity="error"
          action={
            onRetry && (
              <Button color="inherit" size="small" onClick={onRetry}>
                Retry
              </Button>
            )
          }
        >
          {error}
        </Alert>
      ) : (
        <Box sx={{ height: autoHeight ? 'auto' : height, width: '100%', position: 'relative' }}>
          {loading ? (
            <LoadingOverlay />
          ) : (
            <DataGrid
              rows={rows}
              columns={columns}
              loading={loading}
              disableRowSelectionOnClick={disableRowSelectionOnClick}
              disableDensitySelector={disableDensitySelector}
              disableColumnMenu={disableColumnMenu}
              disableColumnFilter={disableColumnFilter}
              disableColumnSelector={disableColumnSelector}
              autoHeight={autoHeight}
              initialState={{
                pagination: {
                  paginationModel: { pageSize, page: 0 },
                },
              }}
              pageSizeOptions={[5, 10, 25, 50, 100]}
              checkboxSelection={checkboxSelection}
              components={{
                Toolbar: CustomToolbar,
                NoRowsOverlay,
              }}
              componentsProps={{
                toolbar: {
                  disableExport,
                  disableFilters: disableColumnFilter,
                },
              }}
              sx={{
                '& .MuiDataGrid-cell:focus': {
                  outline: 'none',
                },
              }}
              {...rest}
            />
          )}
        </Box>
      )}
    </Paper>
  );
};

export default DataTable;
