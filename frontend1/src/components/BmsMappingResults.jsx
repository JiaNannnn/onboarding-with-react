import React, { useState, useMemo } from 'react';
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Typography,
  Button,
  TextField,
  CircularProgress,
  TablePagination,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  FilterList as FilterIcon,
  Info as InfoIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { formatMappingsForDisplay, exportMappingConfig } from '../api/bms';

/**
 * BMS Mapping Results Component
 *
 * @param {Object} props - Component props
 * @param {Object} props.mappingResults - The mapping results from the API
 * @param {boolean} props.loading - Whether the results are loading
 * @param {function} props.onExport - Function to call when exporting results
 */
const BmsMappingResults = ({ mappingResults, loading, onExport }) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [filter, setFilter] = useState('');
  const [sortBy, setSortBy] = useState('confidence');
  const [sortDirection, setSortDirection] = useState('desc');
  const [selectedMapping, setSelectedMapping] = useState(null);

  // Format the mappings for display
  const formattedMappings = useMemo(() => {
    if (!mappingResults || !mappingResults.result) return [];
    return formatMappingsForDisplay(mappingResults.result);
  }, [mappingResults]);

  // Apply filtering and sorting
  const filteredMappings = useMemo(() => {
    if (!formattedMappings) return [];

    // Apply filter
    let filtered = formattedMappings;
    if (filter) {
      const lowerFilter = filter.toLowerCase();
      filtered = formattedMappings.filter(
        (mapping) =>
          mapping.bmsPoint.name.toLowerCase().includes(lowerFilter) ||
          mapping.equipmentType.toLowerCase().includes(lowerFilter) ||
          mapping.instanceId.toLowerCase().includes(lowerFilter) ||
          (mapping.enosPoint && mapping.enosPoint.point_name.toLowerCase().includes(lowerFilter))
      );
    }

    // Apply sorting
    return [...filtered].sort((a, b) => {
      let aValue, bValue;

      // Determine values to compare based on sortBy
      switch (sortBy) {
        case 'confidence':
          aValue = a.confidence || 0;
          bValue = b.confidence || 0;
          break;
        case 'equipmentType':
          aValue = a.equipmentType || '';
          bValue = b.equipmentType || '';
          break;
        case 'instanceId':
          aValue = a.instanceId || '';
          bValue = b.instanceId || '';
          break;
        case 'bmsPointName':
          aValue = a.bmsPoint.name || '';
          bValue = b.bmsPoint.name || '';
          break;
        case 'enosPointName':
          aValue = a.enosPoint ? a.enosPoint.point_name : '';
          bValue = b.enosPoint ? b.enosPoint.point_name : '';
          break;
        case 'mappingType':
          aValue = a.mappingType || '';
          bValue = b.mappingType || '';
          break;
        default:
          aValue = a.confidence || 0;
          bValue = b.confidence || 0;
      }

      // Compare values according to direction
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      } else {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
      }
    });
  }, [formattedMappings, filter, sortBy, sortDirection]);

  // Handle pagination changes
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Handle sorting
  const handleSort = (column) => {
    if (sortBy === column) {
      // Toggle direction if same column
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // Set new column and default direction
      setSortBy(column);
      setSortDirection('desc');
    }
  };

  // Handle viewing details
  const handleViewDetails = (mapping) => {
    setSelectedMapping(mapping);
  };

  // Handle closing the details dialog
  const handleCloseDetails = () => {
    setSelectedMapping(null);
  };

  // Handle exporting results
  const handleExport = async () => {
    if (onExport) {
      onExport(formattedMappings);
    } else {
      try {
        const config = await exportMappingConfig(mappingResults.result);
        // Download as JSON file
        const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'bms-mapping-config.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      } catch (error) {
        console.error('Error exporting mapping config:', error);
      }
    }
  };

  // Get confidence chip color
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.5) return 'info';
    if (confidence >= 0.3) return 'warning';
    return 'error';
  };

  // Get mapping type chip color
  const getMappingTypeColor = (type) => {
    switch (type) {
      case 'auto':
        return 'success';
      case 'suggested':
        return 'info';
      case 'manual':
        return 'primary';
      case 'unmapped':
        return 'error';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!mappingResults || !formattedMappings.length) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="body1">No mapping results available.</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, p: 2 }}>
        <Typography variant="h6">
          BMS Mapping Results
          {mappingResults.summary && (
            <Chip
              label={`${mappingResults.summary.mapped_points} points`}
              size="small"
              color="primary"
              sx={{ ml: 1 }}
            />
          )}
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            label="Filter"
            size="small"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            InputProps={{
              startAdornment: <FilterIcon fontSize="small" sx={{ mr: 1 }} />,
            }}
          />
          <Button variant="contained" startIcon={<DownloadIcon />} onClick={handleExport}>
            Export
          </Button>
        </Box>
      </Box>

      <TableContainer component={Paper}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell onClick={() => handleSort('equipmentType')} sx={{ cursor: 'pointer' }}>
                Equipment Type
                {sortBy === 'equipmentType' && (sortDirection === 'asc' ? ' ↑' : ' ↓')}
              </TableCell>
              <TableCell onClick={() => handleSort('instanceId')} sx={{ cursor: 'pointer' }}>
                Instance
                {sortBy === 'instanceId' && (sortDirection === 'asc' ? ' ↑' : ' ↓')}
              </TableCell>
              <TableCell onClick={() => handleSort('bmsPointName')} sx={{ cursor: 'pointer' }}>
                BMS Point
                {sortBy === 'bmsPointName' && (sortDirection === 'asc' ? ' ↑' : ' ↓')}
              </TableCell>
              <TableCell onClick={() => handleSort('enosPointName')} sx={{ cursor: 'pointer' }}>
                EnOS Point
                {sortBy === 'enosPointName' && (sortDirection === 'asc' ? ' ↑' : ' ↓')}
              </TableCell>
              <TableCell
                onClick={() => handleSort('confidence')}
                sx={{ cursor: 'pointer', width: 100 }}
              >
                Confidence
                {sortBy === 'confidence' && (sortDirection === 'asc' ? ' ↑' : ' ↓')}
              </TableCell>
              <TableCell
                onClick={() => handleSort('mappingType')}
                sx={{ cursor: 'pointer', width: 120 }}
              >
                Type
                {sortBy === 'mappingType' && (sortDirection === 'asc' ? ' ↑' : ' ↓')}
              </TableCell>
              <TableCell sx={{ width: 50 }}></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredMappings
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((mapping, index) => (
                <TableRow key={index} hover>
                  <TableCell>{mapping.equipmentType}</TableCell>
                  <TableCell>{mapping.instanceId}</TableCell>
                  <TableCell>
                    <Typography variant="body2">{mapping.bmsPoint.name}</Typography>
                    {mapping.bmsPoint.component && (
                      <Typography variant="caption" color="textSecondary" display="block">
                        {mapping.bmsPoint.component}
                        {mapping.bmsPoint.subcomponent && ` > ${mapping.bmsPoint.subcomponent}`}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {mapping.enosPoint ? (
                      <>
                        <Typography variant="body2">{mapping.enosPoint.point_name}</Typography>
                        <Typography variant="caption" color="textSecondary" display="block">
                          {mapping.enosPoint.model_id}
                        </Typography>
                      </>
                    ) : (
                      <Typography variant="body2" color="error">
                        Unmapped
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={
                        mapping.confidence ? `${Math.round(mapping.confidence * 100)}%` : 'N/A'
                      }
                      size="small"
                      color={getConfidenceColor(mapping.confidence || 0)}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={mapping.mappingType}
                      size="small"
                      color={getMappingTypeColor(mapping.mappingType)}
                    />
                  </TableCell>
                  <TableCell>
                    <Tooltip title="View Details">
                      <IconButton size="small" onClick={() => handleViewDetails(mapping)}>
                        <InfoIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        rowsPerPageOptions={[10, 25, 50, 100]}
        component="div"
        count={filteredMappings.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />

      {/* Details Dialog */}
      {selectedMapping && (
        <Dialog
          open={Boolean(selectedMapping)}
          onClose={handleCloseDetails}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            Mapping Details
            <IconButton
              aria-label="close"
              onClick={handleCloseDetails}
              sx={{ position: 'absolute', right: 8, top: 8 }}
            >
              <CloseIcon />
            </IconButton>
          </DialogTitle>
          <DialogContent dividers>
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                BMS Point
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell component="th" sx={{ width: '30%', fontWeight: 'bold' }}>
                        ID
                      </TableCell>
                      <TableCell>{selectedMapping.bmsPoint.id}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                        Name
                      </TableCell>
                      <TableCell>{selectedMapping.bmsPoint.name}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                        Type
                      </TableCell>
                      <TableCell>{selectedMapping.bmsPoint.type}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                        Description
                      </TableCell>
                      <TableCell>{selectedMapping.bmsPoint.description}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                        Component
                      </TableCell>
                      <TableCell>{selectedMapping.bmsPoint.component || 'N/A'}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                        Subcomponent
                      </TableCell>
                      <TableCell>{selectedMapping.bmsPoint.subcomponent || 'N/A'}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                        Function
                      </TableCell>
                      <TableCell>{selectedMapping.bmsPoint.function || 'N/A'}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                        Resource
                      </TableCell>
                      <TableCell>{selectedMapping.bmsPoint.resource || 'N/A'}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                        Sub-resource
                      </TableCell>
                      <TableCell>{selectedMapping.bmsPoint.subResource || 'N/A'}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                        Phenomenon
                      </TableCell>
                      <TableCell>{selectedMapping.bmsPoint.phenomenon || 'N/A'}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                        Aspect
                      </TableCell>
                      <TableCell>{selectedMapping.bmsPoint.aspect || 'N/A'}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                        Quantity
                      </TableCell>
                      <TableCell>{selectedMapping.bmsPoint.quantity || 'N/A'}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                        Unit
                      </TableCell>
                      <TableCell>{selectedMapping.bmsPoint.unit || 'N/A'}</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>

            {selectedMapping.enosPoint ? (
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  EnOS Point
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell component="th" sx={{ width: '30%', fontWeight: 'bold' }}>
                          ID
                        </TableCell>
                        <TableCell>{selectedMapping.enosPoint.point_id}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                          Name
                        </TableCell>
                        <TableCell>{selectedMapping.enosPoint.point_name}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                          Model
                        </TableCell>
                        <TableCell>{selectedMapping.enosPoint.model_id}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                          Type
                        </TableCell>
                        <TableCell>{selectedMapping.enosPoint.point_type}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                          Description
                        </TableCell>
                        <TableCell>{selectedMapping.enosPoint.description}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                          Unit
                        </TableCell>
                        <TableCell>{selectedMapping.enosPoint.unit}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                          Data Type
                        </TableCell>
                        <TableCell>{selectedMapping.enosPoint.data_type}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            ) : (
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  EnOS Point
                </Typography>
                <Typography color="error">Unmapped - {selectedMapping.reason}</Typography>
              </Box>
            )}

            <Box>
              <Typography variant="h6" gutterBottom>
                Mapping Info
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell component="th" sx={{ width: '30%', fontWeight: 'bold' }}>
                        Confidence
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={
                            selectedMapping.confidence
                              ? `${Math.round(selectedMapping.confidence * 100)}%`
                              : 'N/A'
                          }
                          size="small"
                          color={getConfidenceColor(selectedMapping.confidence || 0)}
                        />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                        Mapping Type
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={selectedMapping.mappingType}
                          size="small"
                          color={getMappingTypeColor(selectedMapping.mappingType)}
                        />
                      </TableCell>
                    </TableRow>
                    {selectedMapping.transformation &&
                      Object.keys(selectedMapping.transformation).length > 0 && (
                        <TableRow>
                          <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                            Transformation
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {selectedMapping.transformation.description ||
                                'Data transformation required'}
                            </Typography>
                            {selectedMapping.transformation.formula && (
                              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                                Formula: <code>{selectedMapping.transformation.formula}</code>
                              </Typography>
                            )}
                          </TableCell>
                        </TableRow>
                      )}
                    {selectedMapping.reason && (
                      <TableRow>
                        <TableCell component="th" sx={{ fontWeight: 'bold' }}>
                          Reason
                        </TableCell>
                        <TableCell>{selectedMapping.reason}</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDetails}>Close</Button>
          </DialogActions>
        </Dialog>
      )}
    </Box>
  );
};

export default BmsMappingResults;
