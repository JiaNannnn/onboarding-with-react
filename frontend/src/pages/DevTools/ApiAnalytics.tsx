import React, { useState, useEffect } from 'react';
import { PageLayout, Card, Button } from '../../components';
import { getLogs, clearLogs } from '../../utils/logger';
import { LogEntry } from '../../types/commonTypes';
import './DevTools.css';

/**
 * API Analytics component for tracking and visualizing deprecated API usage
 */
const ApiAnalytics: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'timeline' | 'details' | 'checklist'>('overview');
  const [selectedService, setSelectedService] = useState<string | null>(null);

  // Fetch deprecation logs when the component mounts
  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = () => {
    // Get all logs that contain DEPRECATED_USAGE
    const deprecationLogs = getLogs().filter((log: LogEntry) => 
      log.message.includes('DEPRECATED_USAGE')
    );
    setLogs(deprecationLogs);
  };

  // Group logs by function name
  const groupedLogs = React.useMemo(() => {
    const groups: Record<string, {
      service: string;
      count: number;
      lastUsed: Date;
      details: Array<{timestamp: Date; data?: Record<string, unknown>}>
    }> = {};

    logs.forEach(log => {
      // Extract the function name from the message
      const parts = log.message.split(':');
      if (parts.length !== 2) return;
      
      const functionName = parts[1].trim();
      const service = log.data?.service as string || 'unknown';
      
      if (!groups[functionName]) {
        groups[functionName] = {
          service,
          count: 0,
          lastUsed: new Date(0),
          details: []
        };
      }
      
      groups[functionName].count++;
      const timestamp = log.timestamp;
      if (timestamp > groups[functionName].lastUsed) {
        groups[functionName].lastUsed = timestamp;
      }
      
      groups[functionName].details.push({
        timestamp,
        data: log.data
      });
    });
    
    return groups;
  }, [logs]);

  // Sort functions by usage count (descending)
  const sortedFunctions = React.useMemo(() => {
    return Object.entries(groupedLogs)
      .sort(([, a], [, b]) => b.count - a.count)
      .map(([name, data]) => ({
        name,
        ...data
      }));
  }, [groupedLogs]);

  // Get services from logs
  const services = React.useMemo(() => {
    const uniqueServices = new Set<string>();
    sortedFunctions.forEach(func => {
      uniqueServices.add(func.service);
    });
    return Array.from(uniqueServices);
  }, [sortedFunctions]);
  
  // Migration checklist data
  const migrationTasks = [
    { 
      id: 'task-1', 
      title: 'Replace bmsService.fetchPoints with useBMSClient().fetchPoints',
      description: 'Update components using the deprecated fetchPoints function to use the new hook-based approach',
      status: sortedFunctions.some(f => f.name === 'fetchPoints') ? 'in-progress' : 'completed',
      priority: 'high',
      files: ['src/pages/FetchPoints/FetchPoints.tsx']
    },
    { 
      id: 'task-2', 
      title: 'Replace bmsService.fetchDevices with useBMSClient().fetchDevices',
      description: 'Update components using the deprecated fetchDevices function to use the new hook-based approach',
      status: sortedFunctions.some(f => f.name === 'fetchDevices') ? 'in-progress' : 'completed',
      priority: 'high',
      files: ['src/pages/FetchPoints/FetchPoints.tsx']
    },
    { 
      id: 'task-3', 
      title: 'Replace bmsService.getNetworkConfig with useBMSClient().getNetworkConfig',
      description: 'Update components using the deprecated getNetworkConfig function to use the new hook-based approach',
      status: sortedFunctions.some(f => f.name === 'getNetworkConfig') ? 'in-progress' : 'completed',
      priority: 'medium',
      files: ['src/pages/FetchPoints/FetchPoints.tsx']
    },
    { 
      id: 'task-4', 
      title: 'Replace bmsService.discoverDevices with useBMSClient().discoverDevices',
      description: 'Update components using the deprecated discoverDevices function to use the new hook-based approach',
      status: sortedFunctions.some(f => f.name === 'discoverDevices') ? 'in-progress' : 'completed',
      priority: 'medium', 
      files: ['src/pages/FetchPoints/FetchPoints.tsx']
    },
    { 
      id: 'task-5', 
      title: 'Replace bmsService.groupPointsWithAI with useBMSClient().groupPointsWithAI',
      description: 'Update components using the deprecated groupPointsWithAI function to use the new hook-based approach',
      status: sortedFunctions.some(f => f.name === 'groupPointsWithAI') ? 'in-progress' : 'completed',
      priority: 'high',
      files: ['src/hooks/groupPoints/useAIGrouping.ts']
    },
    { 
      id: 'task-6', 
      title: 'Replace bmsService.mapPointsToEnOS with useBMSClient().mapPointsToEnOS',
      description: 'Update components using the deprecated mapPointsToEnOS function to use the new hook-based approach',
      status: sortedFunctions.some(f => f.name === 'mapPointsToEnOS') ? 'in-progress' : 'completed',
      priority: 'high',
      files: ['src/pages/MapPoints/MapPoints.tsx']
    },
    { 
      id: 'task-7', 
      title: 'Replace bmsService.saveMappingToCSV with useBMSClient().saveMappingToCSV',
      description: 'Update components using the deprecated saveMappingToCSV function to use the new hook-based approach',
      status: sortedFunctions.some(f => f.name === 'saveMappingToCSV') ? 'in-progress' : 'completed',
      priority: 'medium',
      files: ['src/pages/SavedMappings/SavedMappings.tsx']
    },
    { 
      id: 'task-8', 
      title: 'Replace bmsService.listSavedMappingFiles with useBMSClient().listSavedMappingFiles',
      description: 'Update components using the deprecated listSavedMappingFiles function to use the new hook-based approach',
      status: sortedFunctions.some(f => f.name === 'listSavedMappingFiles') ? 'in-progress' : 'completed',
      priority: 'medium',
      files: ['src/pages/SavedMappings/SavedMappings.tsx']
    },
    { 
      id: 'task-9', 
      title: 'Replace bmsService.loadMappingFromCSV with useBMSClient().loadMappingFromCSV',
      description: 'Update components using the deprecated loadMappingFromCSV function to use the new hook-based approach',
      status: sortedFunctions.some(f => f.name === 'loadMappingFromCSV') ? 'in-progress' : 'completed',
      priority: 'medium',
      files: ['src/pages/SavedMappings/SavedMappings.tsx']
    },
    { 
      id: 'task-10', 
      title: 'Replace bmsService.getFileDownloadURL with useBMSClient().getFileDownloadURL',
      description: 'Update components using the deprecated getFileDownloadURL function to use the new hook-based approach',
      status: sortedFunctions.some(f => f.name === 'getFileDownloadURL') ? 'in-progress' : 'completed',
      priority: 'low',
      files: ['src/pages/SavedMappings/SavedMappings.tsx']
    },
    { 
      id: 'task-11', 
      title: 'Replace bmsService.exportMappingToEnOS with useBMSClient().exportMappingToEnOS',
      description: 'Update components using the deprecated exportMappingToEnOS function to use the new hook-based approach',
      status: sortedFunctions.some(f => f.name === 'exportMappingToEnOS') ? 'in-progress' : 'completed',
      priority: 'medium',
      files: ['src/pages/SavedMappings/SavedMappings.tsx']
    },
    { 
      id: 'task-12', 
      title: 'Replace BMSDiscoveryService with useBMSClient()',
      description: 'Replace any usage of the deprecated BMSDiscoveryService class with the new hook-based approach',
      status: sortedFunctions.some(f => f.service === 'bmsDiscoveryService') ? 'in-progress' : 'completed',
      priority: 'high',
      files: ['src/hooks/useBMSDiscovery.ts']
    }
  ];

  // Filter functions by selected service
  const filteredFunctions = React.useMemo(() => {
    if (!selectedService) return sortedFunctions;
    return sortedFunctions.filter(func => func.service === selectedService);
  }, [sortedFunctions, selectedService]);

  // Clear logs 
  const handleClearLogs = () => {
    clearLogs();
    setLogs([]);
  };

  // Refresh logs
  const handleRefreshLogs = () => {
    loadLogs();
  };

  // Calculate stats
  const stats = React.useMemo(() => {
    const totalCalls = sortedFunctions.reduce((sum, func) => sum + func.count, 0);
    const totalFunctions = sortedFunctions.length;
    const serviceStats = services.map(service => ({
      name: service,
      count: sortedFunctions.filter(f => f.service === service).length,
      calls: sortedFunctions
        .filter(f => f.service === service)
        .reduce((sum, func) => sum + func.count, 0)
    }));
    
    return {
      totalCalls,
      totalFunctions,
      serviceStats
    };
  }, [sortedFunctions, services]);

  // Render the overview tab
  const renderOverview = () => (
    <div className="devtools-overview">
      <div className="devtools-stats-grid">
        <Card className="devtools-stat-card">
          <div className="devtools-stat-content">
            <h3>Total Deprecated Calls</h3>
            <div className="devtools-stat-value">{stats.totalCalls}</div>
          </div>
        </Card>
        
        <Card className="devtools-stat-card">
          <div className="devtools-stat-content">
            <h3>Unique Deprecated Functions</h3>
            <div className="devtools-stat-value">{stats.totalFunctions}</div>
          </div>
        </Card>
        
        <Card className="devtools-stat-card">
          <div className="devtools-stat-content">
            <h3>Services With Deprecated Calls</h3>
            <div className="devtools-stat-value">{services.length}</div>
          </div>
        </Card>
      </div>

      <Card className="devtools-card">
        <div className="devtools-card-header">
          <h3>Services Breakdown</h3>
        </div>
        
        <div className="devtools-card-body">
          <table className="devtools-table">
            <thead>
              <tr>
                <th>Service</th>
                <th>Deprecated Functions</th>
                <th>Total Calls</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {stats.serviceStats.map(service => (
                <tr key={service.name}>
                  <td>{service.name}</td>
                  <td>{service.count}</td>
                  <td>{service.calls}</td>
                  <td>
                    <Button 
                      variant="outline" 
                      size="small"
                      onClick={() => {
                        setSelectedService(service.name);
                        setActiveTab('details');
                      }}
                    >
                      View Details
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      
      <Card className="devtools-card">
        <div className="devtools-card-header">
          <h3>Top Deprecated Functions</h3>
        </div>
        
        <div className="devtools-card-body">
          <table className="devtools-table">
            <thead>
              <tr>
                <th>Function</th>
                <th>Service</th>
                <th>Calls</th>
                <th>Last Used</th>
              </tr>
            </thead>
            <tbody>
              {sortedFunctions.slice(0, 5).map(func => (
                <tr key={func.name}>
                  <td>{func.name}</td>
                  <td>{func.service}</td>
                  <td>{func.count}</td>
                  <td>{func.lastUsed.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );

  // Render the details tab
  const renderDetails = () => (
    <div className="devtools-details">
      <Card className="devtools-card">
        <div className="devtools-card-header">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>
              {selectedService 
                ? `Deprecated Functions in ${selectedService}` 
                : 'All Deprecated Functions'}
            </h3>
            
            <div>
              <select 
                value={selectedService || ''} 
                onChange={(e) => setSelectedService(e.target.value || null)}
                className="devtools-select"
              >
                <option value="">All Services</option>
                {services.map(service => (
                  <option key={service} value={service}>{service}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
        
        <div className="devtools-card-body">
          <table className="devtools-table">
            <thead>
              <tr>
                <th>Function</th>
                <th>Service</th>
                <th>Calls</th>
                <th>Last Used</th>
              </tr>
            </thead>
            <tbody>
              {filteredFunctions.map(func => (
                <tr key={func.name}>
                  <td>{func.name}</td>
                  <td>{func.service}</td>
                  <td>{func.count}</td>
                  <td>{func.lastUsed.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );

  // Render the timeline tab
  const renderTimeline = () => {
    // Sort all log entries by timestamp
    const timelineLogs = [...logs].sort((a, b) => 
      a.timestamp.getTime() - b.timestamp.getTime()
    );

    return (
      <div className="devtools-timeline">
        <Card className="devtools-card">
          <div className="devtools-card-header">
            <h3>API Call Timeline</h3>
          </div>
          
          <div className="devtools-card-body">
            <div className="devtools-timeline-entries">
              {timelineLogs.length === 0 ? (
                <div className="devtools-no-data">No deprecated API calls recorded</div>
              ) : (
                timelineLogs.map((log, index) => {
                  const parts = log.message.split(':');
                  const functionName = parts.length === 2 ? parts[1].trim() : 'unknown';
                  const service = log.data?.service as string || 'unknown';
                  
                  return (
                    <div key={index} className="devtools-timeline-entry">
                      <div className="devtools-timeline-time">
                        {log.timestamp.toLocaleTimeString()}
                      </div>
                      <div className="devtools-timeline-indicator" />
                      <div className="devtools-timeline-content">
                        <div className="devtools-timeline-title">
                          <strong>{functionName}</strong> from <em>{service}</em>
                        </div>
                        <div className="devtools-timeline-details">
                          {log.data && Object.entries(log.data)
                            .filter(([key]) => key !== 'service' && key !== 'timestamp')
                            .map(([key, value]) => (
                              <div key={key} className="devtools-timeline-detail">
                                <span className="devtools-timeline-key">{key}:</span> 
                                <span className="devtools-timeline-value">
                                  {typeof value === 'object' 
                                    ? JSON.stringify(value) 
                                    : String(value)
                                  }
                                </span>
                              </div>
                            ))
                          }
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </Card>
      </div>
    );
  };
  
  // Render the migration checklist tab
  const renderMigrationChecklist = () => {
    // Calculate progress
    const totalTasks = migrationTasks.length;
    const completedTasks = migrationTasks.filter(task => task.status === 'completed').length;
    const progressPercentage = Math.round((completedTasks / totalTasks) * 100);
    
    // Group tasks by priority
    const highPriorityTasks = migrationTasks.filter(task => task.priority === 'high');
    const mediumPriorityTasks = migrationTasks.filter(task => task.priority === 'medium');
    const lowPriorityTasks = migrationTasks.filter(task => task.priority === 'low');
    
    return (
      <div className="devtools-migration-checklist">
        <Card className="devtools-card">
          <div className="devtools-card-header">
            <h3>Migration Progress</h3>
          </div>
          
          <div className="devtools-card-body">
            <div className="devtools-progress-container">
              <div className="devtools-progress-stats">
                <div className="devtools-progress-percentage">{progressPercentage}%</div>
                <div className="devtools-progress-count">{completedTasks} of {totalTasks} tasks completed</div>
              </div>
              
              <div className="devtools-progress-bar-container">
                <div 
                  className="devtools-progress-bar" 
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
            </div>
            
            <div className="devtools-progress-summary">
              <p>
                Migration to the new API client architecture is <strong>{progressPercentage}% complete</strong>. 
                The remaining tasks involve replacing deprecated functions with their new equivalents from the
                BMSClient class or useBMSClient hook.
              </p>
              <p>
                <strong>Next steps:</strong> Focus on high-priority tasks first, such as replacing
                core functionality in frequently used components.
              </p>
            </div>
          </div>
        </Card>
        
        <Card className="devtools-card">
          <div className="devtools-card-header">
            <h3>High Priority Tasks</h3>
          </div>
          
          <div className="devtools-card-body">
            <div className="devtools-tasks-list">
              {highPriorityTasks.map(task => (
                <div key={task.id} className={`devtools-task-item devtools-task-${task.status}`}>
                  <div className="devtools-task-header">
                    <div className="devtools-task-status">
                      {task.status === 'completed' ? '✅' : '⏳'}
                    </div>
                    <div className="devtools-task-title">{task.title}</div>
                  </div>
                  <div className="devtools-task-description">{task.description}</div>
                  <div className="devtools-task-files">
                    <strong>Files to update:</strong>
                    <ul>
                      {task.files.map((file, index) => (
                        <li key={index}>{file}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
        
        <Card className="devtools-card">
          <div className="devtools-card-header">
            <h3>Medium Priority Tasks</h3>
          </div>
          
          <div className="devtools-card-body">
            <div className="devtools-tasks-list">
              {mediumPriorityTasks.map(task => (
                <div key={task.id} className={`devtools-task-item devtools-task-${task.status}`}>
                  <div className="devtools-task-header">
                    <div className="devtools-task-status">
                      {task.status === 'completed' ? '✅' : '⏳'}
                    </div>
                    <div className="devtools-task-title">{task.title}</div>
                  </div>
                  <div className="devtools-task-description">{task.description}</div>
                  <div className="devtools-task-files">
                    <strong>Files to update:</strong>
                    <ul>
                      {task.files.map((file, index) => (
                        <li key={index}>{file}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
        
        <Card className="devtools-card">
          <div className="devtools-card-header">
            <h3>Low Priority Tasks</h3>
          </div>
          
          <div className="devtools-card-body">
            <div className="devtools-tasks-list">
              {lowPriorityTasks.map(task => (
                <div key={task.id} className={`devtools-task-item devtools-task-${task.status}`}>
                  <div className="devtools-task-header">
                    <div className="devtools-task-status">
                      {task.status === 'completed' ? '✅' : '⏳'}
                    </div>
                    <div className="devtools-task-title">{task.title}</div>
                  </div>
                  <div className="devtools-task-description">{task.description}</div>
                  <div className="devtools-task-files">
                    <strong>Files to update:</strong>
                    <ul>
                      {task.files.map((file, index) => (
                        <li key={index}>{file}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
        
        <Card className="devtools-card">
          <div className="devtools-card-header">
            <h3>Migration Resources</h3>
          </div>
          
          <div className="devtools-card-body">
            <p>
              To help with the migration process, refer to the following resources:
            </p>
            <ul className="devtools-resources-list">
              <li>
                <strong>Migration Guide</strong> - Comprehensive documentation on how to migrate from deprecated services
                to the new API client architecture. 
                <a href="/docs/MIGRATION_GUIDE.md" target="_blank" rel="noopener noreferrer">View Guide</a>
              </li>
              <li>
                <strong>BMSClient Documentation</strong> - API reference for the BMSClient class and useBMSClient hook.
                <a href="/docs/API_CLIENT.md" target="_blank" rel="noopener noreferrer">View Documentation</a>
              </li>
              <li>
                <strong>Example Components</strong> - Reference implementations using the new API client architecture.
                <a href="/docs/EXAMPLES.md" target="_blank" rel="noopener noreferrer">View Examples</a>
              </li>
            </ul>
          </div>
        </Card>
      </div>
    );
  };

  return (
    <PageLayout>
      <div className="devtools-container">
        <header className="devtools-header">
          <h1>API Migration Analytics</h1>
          <p className="devtools-subtitle">
            Monitor and track deprecated API usage to help with migration planning
          </p>
        </header>

        <div className="devtools-actions">
          <Button variant="primary" onClick={handleRefreshLogs}>
            Refresh Data
          </Button>
          <Button variant="outline" onClick={handleClearLogs}>
            Clear Logs
          </Button>
        </div>

        <div className="devtools-tabs">
          <button 
            className={`devtools-tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button 
            className={`devtools-tab ${activeTab === 'details' ? 'active' : ''}`}
            onClick={() => setActiveTab('details')}
          >
            Details
          </button>
          <button 
            className={`devtools-tab ${activeTab === 'timeline' ? 'active' : ''}`}
            onClick={() => setActiveTab('timeline')}
          >
            Timeline
          </button>
          <button 
            className={`devtools-tab ${activeTab === 'checklist' ? 'active' : ''}`}
            onClick={() => setActiveTab('checklist')}
          >
            Migration Checklist
          </button>
        </div>

        <div className="devtools-content">
          {activeTab === 'overview' && renderOverview()}
          {activeTab === 'details' && renderDetails()}
          {activeTab === 'timeline' && renderTimeline()}
          {activeTab === 'checklist' && renderMigrationChecklist()}
        </div>

        {logs.length === 0 && (
          <Card className="devtools-notice-card">
            <div className="devtools-notice-content">
              <h3>No Deprecated API Calls Detected</h3>
              <p>
                This dashboard tracks usage of deprecated functions in real-time. 
                To see data here, your application needs to use functions from <code>bmsService</code> or <code>bmsDiscoveryService</code>.
              </p>
              <p>
                Try navigating to pages that fetch BMS data, like Fetch Points or Map Points,
                to see deprecated API usage appear in this dashboard.
              </p>
              <div className="devtools-migration-notice">
                <h4>Migration Guide Available</h4>
                <p>
                  We've created a comprehensive migration guide to help you update your code
                  to use the new API client architecture. This will make your code more maintainable,
                  type-safe, and future-proof.
                </p>
                <Button 
                  variant="outline" 
                  onClick={() => window.open('/docs/MIGRATION_GUIDE.md', '_blank')}
                >
                  View Migration Guide
                </Button>
              </div>
            </div>
          </Card>
        )}
      </div>
    </PageLayout>
  );
};

export default ApiAnalytics;