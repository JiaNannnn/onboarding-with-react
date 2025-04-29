# Phase 5: Frontend Integration

## Overview
This phase focuses on integrating the reasoning and reflection capabilities into the frontend UI, allowing users to visualize and interact with the reasoning chains and reflection data generated during the mapping process.

## PointsTable Component Updates

### Enhanced Table Cell Renderer

```tsx
// frontend/src/components/PointsTable/ReasoningCell.tsx

import React, { useState } from 'react';
import { Button, Popover, Tag, Typography } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import './ReasoningCell.css';

const { Text } = Typography;

interface ReasoningCellProps {
  reasoningData: any;
  mapping: any;
}

const ReasoningCell: React.FC<ReasoningCellProps> = ({ reasoningData, mapping }) => {
  const [visible, setVisible] = useState(false);
  
  // No reasoning data
  if (!reasoningData) {
    return <Text type="secondary">No reasoning available</Text>;
  }
  
  // Get confidence color
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.5) return 'warning';
    return 'error';
  };
  
  // Render confidence tag
  const confidenceTag = (
    <Tag color={getConfidenceColor(mapping.confidence)}>
      {(mapping.confidence * 100).toFixed(0)}%
    </Tag>
  );
  
  // Prepare reasoning content
  const renderReasoningContent = () => {
    return (
      <div className="reasoning-popover">
        <h4>Mapping Decision</h4>
        {mapping.enosPoint === 'unknown' ? (
          <Text type="danger">Unable to determine mapping</Text>
        ) : (
          <Text strong>{mapping.enosPoint}</Text>
        )}
        
        <h4>Decision Path</h4>
        <ol className="decision-path">
          {reasoningData.decision_path.map((step: string, index: number) => (
            <li key={index}>{step}</li>
          ))}
        </ol>
        
        <h4>Confidence Factors</h4>
        <ul className="confidence-factors">
          {Object.entries(reasoningData.confidence_factors).map(([factor, value]: [string, any]) => (
            <li key={factor}>
              <span className="factor-name">{factor}:</span> 
              <Tag color={getConfidenceColor(value as number)}>
                {((value as number) * 100).toFixed(0)}%
              </Tag>
            </li>
          ))}
        </ul>
        
        {reasoningData.chain && (
          <>
            <h4>Reasoning Chain</h4>
            <Button 
              size="small" 
              onClick={() => window.postMessage({ type: 'SHOW_REASONING_CHAIN', data: reasoningData.chain }, '*')}
            >
              View Full Chain
            </Button>
          </>
        )}
      </div>
    );
  };
  
  return (
    <div className="reasoning-cell">
      <span>{mapping.enosPoint}</span>
      {confidenceTag}
      <Popover
        content={renderReasoningContent()}
        title="Mapping Reasoning"
        trigger="click"
        visible={visible}
        onVisibleChange={setVisible}
        placement="right"
        overlayClassName="reasoning-popover-overlay"
      >
        <Button 
          type="text" 
          icon={<InfoCircleOutlined />} 
          size="small"
          className="reasoning-button"
        />
      </Popover>
    </div>
  );
};

export default ReasoningCell;
```

### CSS for Reasoning Cell

```css
/* frontend/src/components/PointsTable/ReasoningCell.css */

.reasoning-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.reasoning-button {
  opacity: 0.6;
  transition: opacity 0.2s;
}

.reasoning-cell:hover .reasoning-button {
  opacity: 1;
}

.reasoning-popover {
  max-width: 400px;
}

.reasoning-popover h4 {
  margin-bottom: 8px;
  margin-top: 16px;
}

.reasoning-popover h4:first-child {
  margin-top: 0;
}

.decision-path {
  margin-left: 16px;
  padding-left: 0;
}

.decision-path li {
  margin-bottom: 8px;
  font-size: 13px;
}

.confidence-factors {
  list-style: none;
  padding-left: 0;
}

.confidence-factors li {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.factor-name {
  width: 150px;
  text-transform: capitalize;
  font-size: 13px;
}

.reasoning-popover-overlay {
  max-width: 500px;
}
```

## Reasoning Chain Visualization

### ReasoningChainViewer Component

```tsx
// frontend/src/components/ReasoningChain/ReasoningChainViewer.tsx

import React, { useState, useEffect } from 'react';
import { Modal, Steps, Collapse, Tag, Typography, Divider } from 'antd';
import { InfoCircleOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import './ReasoningChainViewer.css';

const { Step } = Steps;
const { Panel } = Collapse;
const { Text, Title } = Typography;

interface ReasoningChainViewerProps {
  visible: boolean;
  onClose: () => void;
  chain: any[];
  pointName?: string;
}

const ReasoningChainViewer: React.FC<ReasoningChainViewerProps> = ({ 
  visible, 
  onClose, 
  chain,
  pointName
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  
  // Reset current step when chain changes
  useEffect(() => {
    setCurrentStep(0);
  }, [chain]);
  
  // Render step content
  const renderStepContent = (step: any) => {
    return (
      <div className="step-content">
        <div className="step-header">
          <div className="step-type">
            <Tag color={getStepTypeColor(step.type)}>{step.type}</Tag>
          </div>
          <div className="step-title">
            <Text strong>{step.description}</Text>
          </div>
        </div>
        
        <Divider className="step-divider" />
        
        <div className="step-detail">
          <Text>{step.detail}</Text>
        </div>
        
        {renderStepData(step)}
      </div>
    );
  };
  
  // Get color for step type
  const getStepTypeColor = (type: string) => {
    const colors: {[key: string]: string} = {
      'analysis': 'blue',
      'identification': 'purple',
      'matching': 'green',
      'generation': 'orange',
      'schema_analysis': 'cyan',
      'analogy': 'magenta'
    };
    
    return colors[type] || 'default';
  };
  
  // Render step-specific data
  const renderStepData = (step: any) => {
    switch (step.type) {
      case 'identification':
        return (
          <div className="step-components">
            <Collapse bordered={false} ghost>
              <Panel header="Identified Components" key="components">
                <ul className="component-list">
                  {Object.entries(step.components).map(([key, value]) => (
                    <li key={key}>
                      <span className="component-key">{key}:</span>
                      <Text code>{value as React.ReactNode || 'None'}</Text>
                    </li>
                  ))}
                </ul>
              </Panel>
            </Collapse>
          </div>
        );
        
      case 'matching':
        return (
          <div className="step-matches">
            <Collapse bordered={false} ghost>
              <Panel header={`Pattern Matches (${step.matches?.length || 0})`} key="matches">
                {step.matches?.length > 0 ? (
                  <ul className="match-list">
                    {step.matches.map((match: any, index: number) => (
                      <li key={index} className="match-item">
                        <div className="match-header">
                          <Text strong>{match.enosPoint}</Text>
                          <Tag color={match.confidence >= 0.7 ? 'success' : 'warning'}>
                            {(match.confidence * 100).toFixed(0)}%
                          </Tag>
                        </div>
                        <div className="match-pattern">
                          <Text code>{match.pattern}</Text>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <Text type="secondary">No matches found</Text>
                )}
              </Panel>
            </Collapse>
          </div>
        );
        
      case 'generation':
        return (
          <div className="step-alternatives">
            <Collapse bordered={false} ghost>
              <Panel header={`Generated Alternatives (${step.alternatives?.length || 0})`} key="alternatives">
                {step.alternatives?.length > 0 ? (
                  <ul className="alternative-list">
                    {step.alternatives.map((alt: any, index: number) => (
                      <li key={index} className="alternative-item">
                        <div className="alternative-header">
                          <Text strong>{alt.enosPoint}</Text>
                          <Tag color={alt.confidence >= 0.7 ? 'success' : 'warning'}>
                            {(alt.confidence * 100).toFixed(0)}%
                          </Tag>
                        </div>
                        <div className="alternative-rationale">
                          <Text>{alt.rationale}</Text>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <Text type="secondary">No alternatives generated</Text>
                )}
              </Panel>
            </Collapse>
          </div>
        );
        
      default:
        return null;
    }
  };
  
  return (
    <Modal
      title={<Title level={4}>Reasoning Chain {pointName ? `for ${pointName}` : ''}</Title>}
      visible={visible}
      onCancel={onClose}
      footer={null}
      width={800}
      className="reasoning-chain-modal"
    >
      <div className="reasoning-chain-container">
        <Steps 
          current={currentStep} 
          onChange={setCurrentStep}
          direction="vertical"
          className="reasoning-steps"
        >
          {chain.map((step, index) => (
            <Step 
              key={index} 
              title={`Step ${step.step}: ${step.description}`} 
              description={step.type} 
              icon={getStepIcon(step.type)}
            />
          ))}
        </Steps>
        
        <div className="reasoning-content">
          {chain.length > 0 ? (
            renderStepContent(chain[currentStep])
          ) : (
            <Text type="secondary">No reasoning steps available</Text>
          )}
        </div>
      </div>
    </Modal>
  );
};

// Get icon for step type
const getStepIcon = (type: string) => {
  switch (type) {
    case 'analysis':
      return <InfoCircleOutlined />;
    case 'matching':
      return <CheckCircleOutlined />;
    case 'generation':
      return <InfoCircleOutlined />;
    default:
      return null;
  }
};

export default ReasoningChainViewer;
```

### CSS for Reasoning Chain Viewer

```css
/* frontend/src/components/ReasoningChain/ReasoningChainViewer.css */

.reasoning-chain-modal .ant-modal-body {
  padding: 0;
  overflow: hidden;
}

.reasoning-chain-container {
  display: flex;
  height: 500px;
}

.reasoning-steps {
  width: 250px;
  padding: 16px;
  border-right: 1px solid #f0f0f0;
  overflow-y: auto;
}

.reasoning-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.step-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.step-header {
  margin-bottom: 16px;
}

.step-type {
  margin-bottom: 8px;
}

.step-title {
  font-size: 16px;
}

.step-divider {
  margin: 12px 0;
}

.step-detail {
  margin-bottom: 24px;
}

.component-list, .match-list, .alternative-list {
  list-style: none;
  padding-left: 0;
}

.component-list li, .match-item, .alternative-item {
  margin-bottom: 12px;
}

.component-key {
  display: inline-block;
  width: 120px;
  text-transform: capitalize;
}

.match-header, .alternative-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.match-pattern, .alternative-rationale {
  margin-top: 4px;
  font-size: 13px;
}
```

## Reflection Visualization

### ReflectionPanel Component

```tsx
// frontend/src/components/Reflection/ReflectionPanel.tsx

import React from 'react';
import { Card, Tag, Typography, Collapse, Button, Divider } from 'antd';
import { 
  InfoCircleOutlined, 
  WarningOutlined, 
  CheckCircleOutlined,
  SyncOutlined
} from '@ant-design/icons';
import './ReflectionPanel.css';

const { Text, Title, Paragraph } = Typography;
const { Panel } = Collapse;

interface ReflectionPanelProps {
  reflection: any;
  onReapply?: () => void;
}

const ReflectionPanel: React.FC<ReflectionPanelProps> = ({ reflection, onReapply }) => {
  if (!reflection) {
    return null;
  }
  
  // Get icon for reflection type
  const getReflectionIcon = () => {
    switch (reflection.type) {
      case 'format_correction':
        return <WarningOutlined />;
      case 'low_confidence':
        return <InfoCircleOutlined />;
      case 'unknown_mapping':
        return <WarningOutlined />;
      default:
        return <InfoCircleOutlined />;
    }
  };
  
  // Get title for reflection type
  const getReflectionTitle = () => {
    switch (reflection.type) {
      case 'format_correction':
        return 'Format Correction';
      case 'low_confidence':
        return 'Low Confidence Analysis';
      case 'unknown_mapping':
        return 'Unknown Mapping Analysis';
      default:
        return 'Reflection';
    }
  };
  
  // Get color for reflection type
  const getReflectionColor = () => {
    switch (reflection.type) {
      case 'format_correction':
        return reflection.success ? '#52c41a' : '#faad14';
      case 'low_confidence':
        return '#1890ff';
      case 'unknown_mapping':
        return '#faad14';
      default:
        return '#d9d9d9';
    }
  };
  
  return (
    <Card 
      className="reflection-card"
      title={
        <div className="reflection-header">
          {getReflectionIcon()}
          <span>{getReflectionTitle()}</span>
          <Tag color={reflection.success ? 'success' : 'warning'}>
            {reflection.success ? 'Resolved' : 'Unresolved'}
          </Tag>
        </div>
      }
      style={{ borderLeft: `2px solid ${getReflectionColor()}` }}
    >
      <div className="reflection-content">
        <div className="reflection-analysis">
          <Title level={5}>Analysis</Title>
          <ul className="analysis-list">
            {reflection.analysis?.map((item: string, index: number) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </div>
        
        {reflection.suggestions && (
          <div className="reflection-suggestions">
            <Title level={5}>Suggestions</Title>
            <ul className="suggestion-list">
              {reflection.suggestions.map((item: string, index: number) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>
        )}
        
        {reflection.type === 'low_confidence' && (
          <div className="confidence-improvement">
            <Divider />
            <Title level={5}>Confidence Improvement</Title>
            <div className="confidence-comparison">
              <div className="confidence-original">
                <Text>Original:</Text>
                <Tag color={getConfidenceColor(reflection.original_decision.confidence)}>
                  {(reflection.original_decision.confidence * 100).toFixed(0)}%
                </Tag>
              </div>
              <div className="confidence-potential">
                <Text>Potential:</Text>
                <Tag color={getConfidenceColor(reflection.potential_confidence)}>
                  {(reflection.potential_confidence * 100).toFixed(0)}%
                </Tag>
              </div>
              <div className="confidence-improvement">
                <Text>Improvement:</Text>
                <Tag color="blue">+{(reflection.confidence_improvement * 100).toFixed(0)}%</Tag>
              </div>
            </div>
            
            <Collapse bordered={false} ghost>
              <Panel header="Factor Details" key="factors">
                <ul className="factor-improvements">
                  {Object.entries(reflection.confidence_improvements).map(([factor, improvement]: [string, any]) => (
                    <li key={factor}>
                      <span className="factor-name">{factor}:</span>
                      <Tag color="blue">
                        {((improvement as number) * 100).toFixed(0)}%
                      </Tag>
                    </li>
                  ))}
                </ul>
              </Panel>
            </Collapse>
          </div>
        )}
        
        {reflection.decomposition && (
          <div className="point-decomposition">
            <Divider />
            <Collapse bordered={false} ghost>
              <Panel header="Point Name Decomposition" key="decomposition">
                <ul className="decomposition-list">
                  <li>
                    <span className="decomp-key">Segments:</span>
                    <Text code>{reflection.decomposition.segments.join(', ')}</Text>
                  </li>
                  <li>
                    <span className="decomp-key">Measurement Type:</span>
                    <Text code>{reflection.decomposition.measurement_type || 'None'}</Text>
                  </li>
                  <li>
                    <span className="decomp-key">Device:</span>
                    <Text code>{reflection.decomposition.device || 'None'}</Text>
                  </li>
                  <li>
                    <span className="decomp-key">Property:</span>
                    <Text code>{reflection.decomposition.property || 'None'}</Text>
                  </li>
                </ul>
              </Panel>
            </Collapse>
          </div>
        )}
        
        {!reflection.success && onReapply && (
          <div className="reflection-actions">
            <Divider />
            <Button 
              type="primary" 
              icon={<SyncOutlined />}
              onClick={onReapply}
            >
              Apply Reflection & Remap
            </Button>
          </div>
        )}
      </div>
    </Card>
  );
};

// Helper function to get confidence color
const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return 'success';
  if (confidence >= 0.5) return 'warning';
  return 'error';
};

export default ReflectionPanel;
```

### CSS for Reflection Panel

```css
/* frontend/src/components/Reflection/ReflectionPanel.css */

.reflection-card {
  margin-bottom: 16px;
}

.reflection-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.reflection-header .anticon {
  font-size: 16px;
}

.reflection-header span {
  flex: 1;
}

.reflection-content {
  font-size: 14px;
}

.analysis-list, .suggestion-list, .decomposition-list, .factor-improvements {
  padding-left: 16px;
  margin-bottom: 16px;
}

.analysis-list li, .suggestion-list li {
  margin-bottom: 8px;
}

.confidence-comparison {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}

.confidence-original, .confidence-potential, .confidence-improvement {
  display: flex;
  align-items: center;
  gap: 8px;
}

.decomp-key, .factor-name {
  display: inline-block;
  width: 130px;
  font-weight: 500;
  text-transform: capitalize;
}

.reflection-actions {
  display: flex;
  justify-content: flex-end;
}
```

## Integration with MapPoints Page

### Update MapPoints Component

```tsx
// frontend/src/pages/MapPoints/MapPoints.tsx

// ... existing imports ...
import ReasoningCell from '../../components/PointsTable/ReasoningCell';
import ReasoningChainViewer from '../../components/ReasoningChain/ReasoningChainViewer';
import ReflectionPanel from '../../components/Reflection/ReflectionPanel';

function MapPoints() {
  // ... existing state ...
  
  // New state for reasoning UI
  const [reasoningChain, setReasoningChain] = useState<any[]>([]);
  const [isReasoningVisible, setIsReasoningVisible] = useState(false);
  const [selectedPoint, setSelectedPoint] = useState<any>(null);
  
  // Listen for reasoning chain view requests
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'SHOW_REASONING_CHAIN') {
        setReasoningChain(event.data.data);
        setIsReasoningVisible(true);
      }
    };
    
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);
  
  // Function to handle point selection for detail view
  const handlePointSelect = (point: any) => {
    setSelectedPoint(point);
  };
  
  // Function to reapply reflection
  const handleReapplyReflection = async () => {
    if (!selectedPoint) return;
    
    // API call to reapply reflection
    try {
      const response = await bmsClient.reflectAndRemap(
        selectedPoint.mapping.pointId,
        selectedPoint.original,
        selectedPoint
      );
      
      // Update points with new mapping
      const updatedPoints = points.map(p => 
        p.mapping.pointId === response.mapping.pointId ? response : p
      );
      
      setPoints(updatedPoints);
      setSelectedPoint(response);
      
      message.success('Reflection applied successfully');
    } catch (error) {
      message.error('Failed to apply reflection');
    }
  };
  
  // Updated hotSettings
  const hotSettings = {
    // ... existing settings ...
    
    columns: [
      // ... existing columns ...
      {
        data: 'mapping.enosPoint',
        type: 'text',
        readOnly: true,
        // Use custom renderer for reasoning
        renderer: function(instance, td, row, col, prop, value, cellProperties) {
          // Get full data for this row
          const rowData = instance.getSourceDataAtRow(row);
          
          // Render custom component to cell
          ReactDOM.render(
            <ReasoningCell 
              reasoningData={rowData.reasoning} 
              mapping={rowData.mapping}
            />,
            td
          );
          
          return td;
        }
      },
      // ... other columns ...
    ]
  };
  
  return (
    <div className="map-points-container">
      {/* Existing UI components */}
      
      {/* Point details panel with reflection */}
      {selectedPoint && (
        <Card title="Point Details" className="point-details-card">
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="Point ID">{selectedPoint.original.pointId}</Descriptions.Item>
            <Descriptions.Item label="Point Name">{selectedPoint.original.pointName}</Descriptions.Item>
            <Descriptions.Item label="Device Type">{selectedPoint.original.deviceType}</Descriptions.Item>
            <Descriptions.Item label="Unit">{selectedPoint.original.unit}</Descriptions.Item>
            <Descriptions.Item label="Description">{selectedPoint.original.description}</Descriptions.Item>
            <Descriptions.Item label="Mapping">
              <Tag color={selectedPoint.mapping.enosPoint === 'unknown' ? 'error' : 'success'}>
                {selectedPoint.mapping.enosPoint}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Confidence">
              <Tag color={getConfidenceColor(selectedPoint.mapping.confidence)}>
                {(selectedPoint.mapping.confidence * 100).toFixed(0)}%
              </Tag>
            </Descriptions.Item>
          </Descriptions>
          
          {/* Show reflection panel if available */}
          {selectedPoint.reflection && (
            <div className="point-reflection">
              <Title level={4}>Reflection Analysis</Title>
              <ReflectionPanel 
                reflection={selectedPoint.reflection}
                onReapply={handleReapplyReflection}
              />
            </div>
          )}
          
          {/* View reasoning chain button */}
          {selectedPoint.reasoning?.chain && (
            <div className="point-reasoning">
              <Button 
                type="primary" 
                ghost
                onClick={() => {
                  setReasoningChain(selectedPoint.reasoning.chain);
                  setIsReasoningVisible(true);
                }}
              >
                View Reasoning Chain
              </Button>
            </div>
          )}
        </Card>
      )}
      
      {/* Reasoning chain modal */}
      <ReasoningChainViewer
        visible={isReasoningVisible}
        onClose={() => setIsReasoningVisible(false)}
        chain={reasoningChain}
        pointName={selectedPoint?.original.pointName}
      />
    </div>
  );
}

export default MapPoints;
```

## API Client Updates

### BMS Client

```tsx
// frontend/src/api/bmsClient.ts

// ... existing code ...

/**
 * Map points with integrated reasoning
 */
export async function mapPointsWithReasoning(
  points: any[],
  reasoningLevel: number = 2
): Promise<any[]> {
  const response = await api.post('/bms/points/map-with-reasoning', {
    points_data: points,
    reasoning_level: reasoningLevel
  });
  return response.data;
}

/**
 * Reflect on and remap a specific point
 */
export async function reflectAndRemap(
  pointId: string,
  pointData: any,
  previousResult: any
): Promise<any> {
  const response = await api.post(`/bms/points/reflect-and-remap/${pointId}`, {
    point_data: pointData,
    previous_result: previousResult
  });
  return response.data;
}

/**
 * Verify consistency between grouping and mapping
 */
export async function verifyConsistency(
  groupedPoints: any,
  mappingResults: any[]
): Promise<any> {
  const response = await api.post('/bms/points/verify-consistency', {
    grouped_points: groupedPoints,
    mapping_results: mappingResults
  });
  return response.data;
}
``` 