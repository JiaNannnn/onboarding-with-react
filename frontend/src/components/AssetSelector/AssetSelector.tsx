import React, { useState, useEffect } from 'react';
import './AssetSelector.css';

export interface Asset {
  id: string;
  name: string;
  type: string;
  deviceCount?: number;
  description?: string;
  location?: string;
  status?: 'active' | 'inactive' | 'maintenance';
  lastUpdated?: string;
}

export interface AssetSelectorProps {
  assets: Asset[];
  selectedAssetId: string | null;
  onAssetSelect: (assetId: string) => void;
  isLoading?: boolean;
  error?: string;
  allowSearch?: boolean;
  allowTypeFilter?: boolean;
  pageSize?: number;
}

const AssetSelector: React.FC<AssetSelectorProps> = ({
  assets,
  selectedAssetId,
  onAssetSelect,
  isLoading = false,
  error = '',
  allowSearch = true,
  allowTypeFilter = true,
  pageSize = 5
}) => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [filteredAssets, setFilteredAssets] = useState<Asset[]>(assets);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [showDetail, setShowDetail] = useState<boolean>(false);
  const [uniqueTypes, setUniqueTypes] = useState<string[]>([]);

  // Get unique asset types for the filter
  useEffect(() => {
    const types = Array.from(new Set(assets.map(asset => asset.type)));
    setUniqueTypes(types);
  }, [assets]);

  // Filter assets based on search term and selected types
  useEffect(() => {
    let filtered = [...assets];
    
    // Filter by search term
    if (searchTerm.trim() !== '') {
      filtered = filtered.filter(asset => 
        asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        asset.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (asset.description && asset.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (asset.location && asset.location.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }
    
    // Filter by selected types
    if (selectedTypes.length > 0) {
      filtered = filtered.filter(asset => selectedTypes.includes(asset.type));
    }
    
    setFilteredAssets(filtered);
    setCurrentPage(1); // Reset to first page when filters change
  }, [assets, searchTerm, selectedTypes]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleTypeToggle = (type: string) => {
    setSelectedTypes(prev => {
      if (prev.includes(type)) {
        return prev.filter(t => t !== type);
      } else {
        return [...prev, type];
      }
    });
  };

  const handleAssetSelect = (assetId: string) => {
    onAssetSelect(assetId);
    setShowDetail(true);
  };

  const clearFilters = () => {
    setSearchTerm('');
    setSelectedTypes([]);
  };

  // Calculate pagination
  const totalPages = Math.ceil(filteredAssets.length / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedAssets = filteredAssets.slice(startIndex, endIndex);

  // Find selected asset details
  const selectedAsset = assets.find(asset => asset.id === selectedAssetId);

  return (
    <div className="asset-selector">
      <div className="asset-selector__header">
        <h3 className="asset-selector__title">Select an Asset</h3>
        {allowSearch && (
          <div className="asset-selector__search">
            <input
              type="text"
              placeholder="Search assets..."
              value={searchTerm}
              onChange={handleSearchChange}
              disabled={isLoading}
              className="asset-selector__search-input"
            />
          </div>
        )}
      </div>

      {error && (
        <div className="asset-selector__error">
          {error}
        </div>
      )}

      {allowTypeFilter && uniqueTypes.length > 0 && (
        <div className="asset-selector__filters">
          <div className="asset-selector__filter-header">
            <span className="asset-selector__filter-title">Filter by Type</span>
            {selectedTypes.length > 0 && (
              <button 
                className="asset-selector__clear-filters"
                onClick={clearFilters}
              >
                Clear Filters
              </button>
            )}
          </div>
          <div className="asset-selector__type-filters">
            {uniqueTypes.map(type => (
              <label key={type} className="asset-selector__type-filter">
                <input
                  type="checkbox"
                  checked={selectedTypes.includes(type)}
                  onChange={() => handleTypeToggle(type)}
                />
                <span>{type}</span>
                <span className="asset-selector__type-count">
                  ({assets.filter(asset => asset.type === type).length})
                </span>
              </label>
            ))}
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="asset-selector__loading">
          Loading assets...
        </div>
      ) : (
        <div className="asset-selector__content">
          <div className={`asset-selector__list ${showDetail && selectedAssetId ? 'asset-selector__list--with-detail' : ''}`}>
            {paginatedAssets.length === 0 ? (
              <div className="asset-selector__empty">
                No assets found
              </div>
            ) : (
              paginatedAssets.map(asset => (
                <div
                  key={asset.id}
                  className={`asset-selector__item ${selectedAssetId === asset.id ? 'asset-selector__item--selected' : ''}`}
                  onClick={() => handleAssetSelect(asset.id)}
                >
                  <div className="asset-selector__item-header">
                    <h4 className="asset-selector__item-name">{asset.name}</h4>
                    <span className="asset-selector__item-type">{asset.type}</span>
                  </div>
                  {asset.deviceCount !== undefined && (
                    <div className="asset-selector__item-devices">
                      {asset.deviceCount} device{asset.deviceCount !== 1 ? 's' : ''}
                    </div>
                  )}
                  {asset.description && (
                    <div className="asset-selector__item-description">
                      {asset.description}
                    </div>
                  )}
                  {asset.location && (
                    <div className="asset-selector__item-location">
                      Location: {asset.location}
                    </div>
                  )}
                  {asset.status && (
                    <div className={`asset-selector__item-status asset-selector__item-status--${asset.status}`}>
                      Status: {asset.status}
                    </div>
                  )}
                </div>
              ))
            )}
            
            {totalPages > 1 && (
              <div className="asset-selector__pagination">
                <button 
                  className="asset-selector__pagination-button"
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                >
                  &laquo; Prev
                </button>
                <span className="asset-selector__pagination-info">
                  Page {currentPage} of {totalPages}
                </span>
                <button 
                  className="asset-selector__pagination-button"
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                >
                  Next &raquo;
                </button>
              </div>
            )}
          </div>
          
          {showDetail && selectedAsset && (
            <div className="asset-selector__detail">
              <div className="asset-selector__detail-header">
                <h3 className="asset-selector__detail-title">{selectedAsset.name}</h3>
                <button 
                  className="asset-selector__detail-close"
                  onClick={() => setShowDetail(false)}
                >
                  &times;
                </button>
              </div>
              <div className="asset-selector__detail-content">
                <div className="asset-selector__detail-group">
                  <span className="asset-selector__detail-label">Asset ID:</span>
                  <span className="asset-selector__detail-value">{selectedAsset.id}</span>
                </div>
                <div className="asset-selector__detail-group">
                  <span className="asset-selector__detail-label">Type:</span>
                  <span className="asset-selector__detail-value">{selectedAsset.type}</span>
                </div>
                {selectedAsset.deviceCount !== undefined && (
                  <div className="asset-selector__detail-group">
                    <span className="asset-selector__detail-label">Device Count:</span>
                    <span className="asset-selector__detail-value">{selectedAsset.deviceCount}</span>
                  </div>
                )}
                {selectedAsset.description && (
                  <div className="asset-selector__detail-group">
                    <span className="asset-selector__detail-label">Description:</span>
                    <span className="asset-selector__detail-value">{selectedAsset.description}</span>
                  </div>
                )}
                {selectedAsset.location && (
                  <div className="asset-selector__detail-group">
                    <span className="asset-selector__detail-label">Location:</span>
                    <span className="asset-selector__detail-value">{selectedAsset.location}</span>
                  </div>
                )}
                {selectedAsset.status && (
                  <div className="asset-selector__detail-group">
                    <span className="asset-selector__detail-label">Status:</span>
                    <span className={`asset-selector__detail-value asset-selector__detail-status--${selectedAsset.status}`}>
                      {selectedAsset.status}
                    </span>
                  </div>
                )}
                {selectedAsset.lastUpdated && (
                  <div className="asset-selector__detail-group">
                    <span className="asset-selector__detail-label">Last Updated:</span>
                    <span className="asset-selector__detail-value">
                      {new Date(selectedAsset.lastUpdated).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AssetSelector; 