import React, { useState } from 'react';
import { Button, Card, Collapse, Divider, Space, Table, Tag, Typography, Modal, Select, Form } from 'antd';
import { CaretRightOutlined, InfoCircleOutlined } from '@ant-design/icons';
import './GroupVerification.css';

const { Panel } = Collapse;
const { Title, Text } = Typography;
const { Option } = Select;

interface Point {
  pointId: string;
  pointName: string;
  unit?: string;
  description?: string;
  grouping_reasoning?: string[];
  verification_reasoning?: string[];
}

interface GroupData {
  points: Point[];
  reasoning?: string[];
  confidence?: number;
  confidence_details?: {
    naming_pattern: number;
    point_types: number;
    units: number;
    coherence: number;
  };
}

interface GroupVerificationProps {
  groups: Record<string, GroupData>;
  onVerify: (verifiedGroups: Record<string, GroupData>) => void;
  isLoading?: boolean;
}

const GroupVerification: React.FC<GroupVerificationProps> = ({ 
  groups, 
  onVerify,
  isLoading = false
}) => {
  const [verifiedGroups, setVerifiedGroups] = useState<Record<string, GroupData>>(groups);
  const [expandedGroups, setExpandedGroups] = useState<string[]>([]);
  const [moveModalVisible, setMoveModalVisible] = useState(false);
  const [pointToMove, setPointToMove] = useState<Point | null>(null);
  const [targetGroup, setTargetGroup] = useState<string>('');
  
  // Columns for point details
  const columns = [
    {
      title: 'Point ID',
      dataIndex: 'pointId',
      key: 'pointId',
      width: '15%',
    },
    {
      title: 'Point Name',
      dataIndex: 'pointName',
      key: 'pointName',
      width: '30%',
    },
    {
      title: 'Unit',
      dataIndex: 'unit',
      key: 'unit',
      width: '10%',
      render: (text: string) => text || '-',
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      width: '25%',
      render: (text: string) => text || '-',
    },
    {
      title: 'Reasoning',
      key: 'reasoning',
      width: '10%',
      render: (_: any, record: Point) => (
        record.verification_reasoning ? (
          <Collapse ghost>
            <Panel header="View Reasoning" key="verification">
              <ul className="reasoning-list">
                {record.verification_reasoning.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ul>
            </Panel>
          </Collapse>
        ) : null
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: '10%',
      render: (_: any, record: Point) => (
        <Button 
          size="small" 
          onClick={() => handleMovePointClick(record)}
          disabled={isLoading}
        >
          Move
        </Button>
      ),
    },
  ];
  
  // Handle clicking the move point button
  const handleMovePointClick = (point: Point) => {
    setPointToMove(point);
    setTargetGroup('');
    setMoveModalVisible(true);
  };
  
  // Handle moving a point to a different group
  const handleMovePoint = () => {
    if (!pointToMove || !targetGroup) return;
    
    // Find source group
    const sourceGroup = Object.entries(verifiedGroups).find(([_, groupData]) => 
      groupData.points.some(p => p.pointId === pointToMove.pointId)
    );
    
    if (!sourceGroup) {
      setMoveModalVisible(false);
      return;
    }
    
    const [sourceGroupName, sourceGroupData] = sourceGroup;
    
    // Remove point from source group
    const updatedSourcePoints = sourceGroupData.points.filter(
      p => p.pointId !== pointToMove.pointId
    );
    
    // Add point to target group
    const updatedGroups = { ...verifiedGroups };
    
    // Update source group
    updatedGroups[sourceGroupName] = {
      ...sourceGroupData,
      points: updatedSourcePoints
    };
    
    // If source group is now empty, remove it
    if (updatedSourcePoints.length === 0) {
      delete updatedGroups[sourceGroupName];
    }
    
    // Update target group
    if (!updatedGroups[targetGroup]) {
      updatedGroups[targetGroup] = { points: [] };
    }
    
    // Add reasoning about manual move
    const pointWithReasoning = {
      ...pointToMove,
      verification_reasoning: [
        ...(pointToMove.verification_reasoning || []),
        `Manually moved from ${sourceGroupName} to ${targetGroup} by user.`
      ]
    };
    
    updatedGroups[targetGroup].points = [
      ...updatedGroups[targetGroup].points,
      pointWithReasoning
    ];
    
    setVerifiedGroups(updatedGroups);
    setMoveModalVisible(false);
  };
  
  // Toggle expanded groups
  const handleGroupExpand = (deviceType: string) => {
    if (expandedGroups.includes(deviceType)) {
      setExpandedGroups(expandedGroups.filter(g => g !== deviceType));
    } else {
      setExpandedGroups([...expandedGroups, deviceType]);
    }
  };
  
  // Handle verifying all groups
  const handleVerify = () => {
    onVerify(verifiedGroups);
  };
  
  // Render confidence score indicator
  const renderConfidenceIndicator = (confidence?: number) => {
    if (confidence === undefined) return null;
    
    let color = 'red';
    if (confidence >= 0.8) color = 'green';
    else if (confidence >= 0.6) color = 'gold';
    else if (confidence >= 0.4) color = 'orange';
    
    return (
      <Tag color={color}>
        Confidence: {Math.round(confidence * 100)}%
      </Tag>
    );
  };
  
  return (
    <div className="group-verification">
      <Space direction="vertical" style={{ width: '100%' }}>
        <div className="group-verification-header">
          <Title level={4}>Verify Device Type Groups</Title>
          <Text type="secondary">
            Review the groups below and make any necessary adjustments before proceeding.
          </Text>
        </div>
        
        {Object.entries(verifiedGroups).map(([deviceType, data]) => (
          <Card
            key={deviceType}
            title={
              <div className="group-card-title">
                <span>{deviceType}</span>
                <span className="group-point-count">({data.points.length} points)</span>
                {renderConfidenceIndicator(data.confidence)}
              </div>
            }
            extra={
              <Button 
                type="text" 
                icon={<CaretRightOutlined rotate={expandedGroups.includes(deviceType) ? 90 : 0} />}
                onClick={() => handleGroupExpand(deviceType)}
                disabled={isLoading}
              />
            }
            className="group-card"
          >
            {data.reasoning && data.reasoning.length > 0 && (
              <Collapse ghost>
                <Panel 
                  header={
                    <span>
                      <InfoCircleOutlined /> View Grouping Reasoning
                    </span>
                  } 
                  key="reasoning"
                >
                  <ul className="reasoning-list">
                    {data.reasoning.map((step, index) => (
                      <li key={index}>{step}</li>
                    ))}
                  </ul>
                </Panel>
              </Collapse>
            )}
            
            {data.confidence_details && (
              <Collapse ghost>
                <Panel 
                  header={
                    <span>
                      <InfoCircleOutlined /> View Confidence Details
                    </span>
                  } 
                  key="confidence"
                >
                  <ul className="confidence-details">
                    <li>Naming Pattern: {Math.round(data.confidence_details.naming_pattern * 100)}%</li>
                    <li>Point Types: {Math.round(data.confidence_details.point_types * 100)}%</li>
                    <li>Units: {Math.round(data.confidence_details.units * 100)}%</li>
                    <li>Coherence: {Math.round(data.confidence_details.coherence * 100)}%</li>
                  </ul>
                </Panel>
              </Collapse>
            )}
            
            {expandedGroups.includes(deviceType) && (
              <Table
                dataSource={data.points}
                columns={columns}
                size="small"
                rowKey="pointId"
                pagination={{ pageSize: 5 }}
                loading={isLoading}
              />
            )}
          </Card>
        ))}
        
        <Divider />
        
        <Button 
          type="primary" 
          onClick={handleVerify}
          disabled={isLoading}
          loading={isLoading}
        >
          Confirm Groups & Proceed
        </Button>
      </Space>
      
      {/* Modal for moving points */}
      <Modal
        title="Move Point to Different Group"
        open={moveModalVisible}
        onOk={handleMovePoint}
        onCancel={() => setMoveModalVisible(false)}
        okButtonProps={{ disabled: !targetGroup }}
      >
        <Form layout="vertical">
          <Form.Item label="Point">
            <Text strong>{pointToMove?.pointName}</Text>
          </Form.Item>
          
          <Form.Item 
            label="Target Group" 
            required
            help="Select an existing group or enter a new group name"
          >
            <Select
              showSearch
              value={targetGroup}
              onChange={setTargetGroup}
              style={{ width: '100%' }}
              placeholder="Select target group"
              allowClear
              optionFilterProp="children"
            >
              {Object.keys(verifiedGroups).map(group => (
                <Option key={group} value={group}>{group}</Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default GroupVerification; 