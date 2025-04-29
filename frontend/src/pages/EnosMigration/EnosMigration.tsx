import React, { useState } from 'react';
import { 
  Card, 
  Steps, 
  Button, 
  Form, 
  Input, 
  Select, 
  Upload, 
  message, 
  Table, 
  Progress, 
  Typography, 
  Alert, 
  Collapse,
  Space,
  Tag,
  Tabs
} from 'antd';
import { 
  CloudUploadOutlined, 
  SettingOutlined, 
  CheckCircleOutlined, 
  SyncOutlined,
  UploadOutlined,
  DownloadOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import './EnosMigration.css';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;
const { Step } = Steps;
const { Panel } = Collapse;
const { TabPane } = Tabs;

interface MigrationPoint {
  id: string;
  name: string;
  bmsSource: string;
  enosModel: string;
  enosPointId: string;
  status: 'pending' | 'success' | 'failed' | 'warning';
  message?: string;
}

const EnosMigration: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [form] = Form.useForm();
  const [migrationPoints, setMigrationPoints] = useState<MigrationPoint[]>([]);
  const [migrationProgress, setMigrationProgress] = useState<number>(0);
  const [migrationStatus, setMigrationStatus] = useState<'idle' | 'running' | 'completed' | 'failed'>('idle');

  const columns: ColumnsType<MigrationPoint> = [
    {
      title: 'BMS Point ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'BMS Source',
      dataIndex: 'bmsSource',
      key: 'bmsSource',
    },
    {
      title: 'EnOS Model',
      dataIndex: 'enosModel',
      key: 'enosModel',
    },
    {
      title: 'EnOS Point ID',
      dataIndex: 'enosPointId',
      key: 'enosPointId',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: 'pending' | 'success' | 'failed' | 'warning', record) => {
        const statusMap = {
          pending: { icon: <SyncOutlined spin />, color: 'blue', text: 'Pending' },
          success: { icon: <CheckCircleOutlined />, color: 'green', text: 'Success' },
          failed: { icon: <InfoCircleOutlined />, color: 'red', text: 'Failed' },
          warning: { icon: <InfoCircleOutlined />, color: 'orange', text: 'Warning' }
        };
        
        return (
          <Space>
            <Tag color={statusMap[status].color} icon={statusMap[status].icon}>
              {statusMap[status].text}
            </Tag>
            {record.message && (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {record.message}
              </Text>
            )}
          </Space>
        );
      },
    },
  ];

  const steps = [
    {
      title: 'Configure',
      description: 'Set up migration settings',
      content: (
        <Card title="Migration Configuration" className="config-card">
          <Form
            form={form}
            layout="vertical"
            initialValues={{
              migrationType: 'full',
              enosEnvironment: 'production'
            }}
          >
            <Form.Item
              name="migrationType"
              label="Migration Type"
              rules={[{ required: true, message: 'Please select migration type' }]}
            >
              <Select>
                <Option value="full">Full Migration</Option>
                <Option value="incremental">Incremental Migration</Option>
                <Option value="test">Test Migration</Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="enosEnvironment"
              label="EnOS Environment"
              rules={[{ required: true, message: 'Please select EnOS environment' }]}
            >
              <Select>
                <Option value="development">Development</Option>
                <Option value="testing">Testing</Option>
                <Option value="production">Production</Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="orgId"
              label="Organization ID"
              rules={[{ required: true, message: 'Please enter organization ID' }]}
            >
              <Input placeholder="Enter EnOS organization ID" />
            </Form.Item>

            <Form.Item
              name="apiKey"
              label="API Key"
              rules={[{ required: true, message: 'Please enter API key' }]}
            >
              <Input.Password placeholder="Enter EnOS API key" />
            </Form.Item>

            <Form.Item
              name="apiSecret"
              label="API Secret"
              rules={[{ required: true, message: 'Please enter API secret' }]}
            >
              <Input.Password placeholder="Enter EnOS API secret" />
            </Form.Item>

            <Form.Item
              name="mappingFile"
              label="Mapping Configuration File (Optional)"
            >
              <Upload
                name="mappingFile"
                accept=".json,.csv"
                maxCount={1}
                beforeUpload={() => false}
              >
                <Button icon={<UploadOutlined />}>Upload Mapping File</Button>
              </Upload>
            </Form.Item>
          </Form>
        </Card>
      ),
    },
    {
      title: 'Map Points',
      description: 'Map BMS points to EnOS',
      content: (
        <div className="mapping-container">
          <Card title="Point Mapping Configuration">
            <Tabs defaultActiveKey="1">
              <TabPane tab="Automatic Mapping" key="1">
                <Alert
                  message="Automatic Mapping"
                  description="System will attempt to map BMS points to EnOS models based on naming conventions and metadata."
                  type="info"
                  showIcon
                  style={{ marginBottom: '16px' }}
                />
                <Form layout="vertical">
                  <Form.Item
                    label="Naming Pattern"
                    name="namingPattern"
                  >
                    <Input placeholder="e.g., {building}.{floor}.{system}.{point}" />
                  </Form.Item>
                  <Form.Item
                    label="Default EnOS Model"
                    name="defaultModel"
                  >
                    <Select placeholder="Select default model">
                      <Option value="HVAC">HVAC</Option>
                      <Option value="Lighting">Lighting</Option>
                      <Option value="Energy">Energy Meter</Option>
                    </Select>
                  </Form.Item>
                  <Button type="primary">Run Automatic Mapping</Button>
                </Form>
              </TabPane>
              <TabPane tab="Manual Mapping" key="2">
                <Alert
                  message="Manual Mapping"
                  description="Upload a CSV or Excel file with your custom mapping between BMS points and EnOS models."
                  type="info"
                  showIcon
                  style={{ marginBottom: '16px' }}
                />
                <Upload
                  name="mappingFile"
                  accept=".csv,.xlsx"
                  maxCount={1}
                  beforeUpload={() => false}
                >
                  <Button icon={<UploadOutlined />}>Upload Mapping File</Button>
                </Upload>
                <div style={{ marginTop: '16px' }}>
                  <Button type="link" icon={<DownloadOutlined />}>Download Template</Button>
                </div>
              </TabPane>
              <TabPane tab="Preview Mapping" key="3">
                <Table 
                  columns={columns} 
                  dataSource={migrationPoints.length ? migrationPoints : []} 
                  rowKey="id"
                  pagination={{ pageSize: 5 }}
                  locale={{ emptyText: 'No mapping data. Please configure mapping first.' }}
                />
              </TabPane>
            </Tabs>
          </Card>
        </div>
      ),
    },
    {
      title: 'Migrate',
      description: 'Start migration process',
      content: (
        <div className="migration-container">
          <Card title="Migration Process">
            <div className="migration-status">
              <Progress 
                percent={migrationProgress} 
                status={migrationStatus === 'failed' ? 'exception' : undefined}
                style={{ marginBottom: '20px' }}
              />
              
              {migrationStatus === 'idle' && (
                <Alert
                  message="Ready to Start Migration"
                  description="Review your configuration settings before starting the migration process."
                  type="info"
                  showIcon
                  style={{ marginBottom: '20px' }}
                />
              )}
              
              {migrationStatus === 'running' && (
                <Alert
                  message="Migration in Progress"
                  description="The system is currently migrating BMS points to EnOS. This may take several minutes."
                  type="warning"
                  showIcon
                  style={{ marginBottom: '20px' }}
                />
              )}
              
              {migrationStatus === 'completed' && (
                <Alert
                  message="Migration Completed"
                  description="All points have been successfully migrated to EnOS."
                  type="success"
                  showIcon
                  style={{ marginBottom: '20px' }}
                />
              )}
              
              {migrationStatus === 'failed' && (
                <Alert
                  message="Migration Failed"
                  description="There was an error during the migration process. See the details below."
                  type="error"
                  showIcon
                  style={{ marginBottom: '20px' }}
                />
              )}
              
              <Collapse>
                <Panel header="Migration Details" key="1">
                  <Table 
                    columns={columns} 
                    dataSource={migrationPoints} 
                    rowKey="id"
                    pagination={{ pageSize: 10 }}
                  />
                </Panel>
                <Panel header="Migration Log" key="2">
                  <pre className="migration-log">
                    {migrationStatus !== 'idle' 
                      ? "2023-04-25 14:30:15 INFO Starting migration process\n2023-04-25 14:30:16 INFO Connecting to EnOS environment\n2023-04-25 14:30:17 INFO Authentication successful\n2023-04-25 14:30:20 INFO Processing 48 points for migration\n2023-04-25 14:31:05 INFO Completed migration of 48/48 points\n2023-04-25 14:31:06 INFO Migration completed successfully"
                      : "Migration log will appear here once started."}
                  </pre>
                </Panel>
              </Collapse>
            </div>
          </Card>
        </div>
      ),
    },
  ];

  const nextStep = () => {
    if (currentStep === 0) {
      form.validateFields()
        .then(() => {
          setCurrentStep(currentStep + 1);
          if (migrationPoints.length === 0) {
            // Generate mock data for the migration points on first entry to step 1
            generateMockMigrationPoints();
          }
        })
        .catch((info: any) => {
          message.error('Please complete all required fields');
        });
    } else if (currentStep === 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    setCurrentStep(currentStep - 1);
  };

  const generateMockMigrationPoints = () => {
    const mockData: MigrationPoint[] = Array(20).fill(null).map((_, index) => ({
      id: `BMS-${1000 + index}`,
      name: `Point ${index + 1}`,
      bmsSource: ['BACnet', 'Modbus', 'KNX'][Math.floor(Math.random() * 3)],
      enosModel: ['HVAC', 'Lighting', 'Energy'][Math.floor(Math.random() * 3)],
      enosPointId: `ENOS-${2000 + index}`,
      status: 'pending',
    }));
    
    setMigrationPoints(mockData);
  };

  const startMigration = () => {
    if (migrationStatus === 'running') {
      message.warning('Migration is already in progress');
      return;
    }
    
    setLoading(true);
    setMigrationStatus('running');
    setMigrationProgress(0);
    
    // Mock the migration process
    const interval = setInterval(() => {
      setMigrationProgress(prev => {
        // Update status of random points
        const updatedPoints = [...migrationPoints];
        const randomIndex = Math.floor(Math.random() * updatedPoints.length);
        
        if (updatedPoints[randomIndex].status === 'pending') {
          const randomStatus = Math.random();
          if (randomStatus > 0.9) {
            updatedPoints[randomIndex].status = 'failed';
            updatedPoints[randomIndex].message = 'Connection timeout';
          } else if (randomStatus > 0.8) {
            updatedPoints[randomIndex].status = 'warning';
            updatedPoints[randomIndex].message = 'Converted with data loss';
          } else {
            updatedPoints[randomIndex].status = 'success';
          }
        }
        
        setMigrationPoints(updatedPoints);
        
        // Calculate new progress
        const newProgress = prev + Math.floor(Math.random() * 10);
        
        if (newProgress >= 100) {
          clearInterval(interval);
          setLoading(false);
          setMigrationStatus(
            updatedPoints.some(p => p.status === 'failed') 
              ? 'failed' 
              : 'completed'
          );
          return 100;
        }
        
        return newProgress;
      });
    }, 800);
  };

  return (
    <div className="enos-migration-container">
      <Title level={2}>EnOS Migration</Title>
      <Paragraph>
        Migrate your BMS points to the EnOS IoT platform. Follow these steps to 
        configure and execute the migration process.
      </Paragraph>

      <Card className="steps-card">
        <Steps current={currentStep}>
          {steps.map(item => (
            <Step 
              key={item.title} 
              title={item.title} 
              description={item.description} 
            />
          ))}
        </Steps>
        
        <div className="steps-content">
          {steps[currentStep].content}
        </div>
        
        <div className="steps-action">
          {currentStep > 0 && (
            <Button style={{ margin: '0 8px' }} onClick={prevStep}>
              Previous
            </Button>
          )}
          
          {currentStep < steps.length - 1 && (
            <Button type="primary" onClick={nextStep}>
              Next
            </Button>
          )}
          
          {currentStep === steps.length - 1 && (
            <Button 
              type="primary" 
              onClick={startMigration} 
              loading={loading}
              icon={<CloudUploadOutlined />}
            >
              Start Migration
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
};

export default EnosMigration; 