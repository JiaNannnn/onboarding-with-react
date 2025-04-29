import React, { useState } from 'react';
import { PageLayout, Card, Button } from '../../components';
import './DevTools.css';

interface MigrationPattern {
  id: string;
  name: string;
  description: string;
  importPattern: string;
  usagePattern: string;
  importReplacement: string;
  usageReplacement: string;
  examples: {
    before: string;
    after: string;
  }[];
}

/**
 * Migration Assistant component for helping with API client migration
 */
const MigrationAssistant: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [fileContent, setFileContent] = useState<string>('');
  const [refactoredContent, setRefactoredContent] = useState<string>('');
  const [changes, setChanges] = useState<{line: number; original: string; new: string}[]>([]);
  const [activePattern, setActivePattern] = useState<string | null>(null);
  
  // Migration patterns for different API functions
  const migrationPatterns: MigrationPattern[] = [
    {
      id: 'fetchPoints',
      name: 'Replace fetchPoints',
      description: 'Replace bmsService.fetchPoints with useBMSClient().fetchPoints',
      importPattern: `import { fetchPoints } from '../api/bmsService';`,
      usagePattern: `fetchPoints(assetId, deviceInstance, deviceAddress, config)`,
      importReplacement: `import { useBMSClient } from '../hooks/useBMSClient';`,
      usageReplacement: `useBMSClient(config).fetchPoints(deviceInstance, deviceAddress)`,
      examples: [
        {
          before: `
import React, { useState, useEffect } from 'react';
import { fetchPoints } from '../api/bmsService';

function MyComponent() {
  const [points, setPoints] = useState([]);
  
  useEffect(() => {
    const loadPoints = async () => {
      const result = await fetchPoints('asset123', 'device456', '192.168.1.100', {
        apiGateway: 'http://localhost:5000'
      });
      setPoints(result);
    };
    
    loadPoints();
  }, []);
  
  return (
    <div>
      {points.map(point => (
        <div key={point.id}>{point.pointName}</div>
      ))}
    </div>
  );
}`,
          after: `
import React, { useState, useEffect } from 'react';
import { useBMSClient } from '../hooks/useBMSClient';

function MyComponent() {
  const [points, setPoints] = useState([]);
  const bmsClient = useBMSClient({
    apiGateway: 'http://localhost:5000',
    assetId: 'asset123'
  });
  
  useEffect(() => {
    const loadPoints = async () => {
      const result = await bmsClient.fetchPoints('device456', '192.168.1.100');
      setPoints(result);
    };
    
    loadPoints();
  }, [bmsClient]);
  
  return (
    <div>
      {points.map(point => (
        <div key={point.id}>{point.pointName}</div>
      ))}
    </div>
  );
}`
        }
      ]
    },
    {
      id: 'groupPointsWithAI',
      name: 'Replace groupPointsWithAI',
      description: 'Replace bmsService.groupPointsWithAI with useBMSClient().groupPointsWithAI',
      importPattern: `import { groupPointsWithAI } from '../api/bmsService';`,
      usagePattern: `groupPointsWithAI(points, config)`,
      importReplacement: `import { useBMSClient } from '../hooks/useBMSClient';`,
      usageReplacement: `useBMSClient(config).groupPointsWithAI(points)`,
      examples: [
        {
          before: `
import { useState } from 'react';
import { groupPointsWithAI } from '../../api/bmsService';

export function useAIGrouping() {
  const handleAIGrouping = async (points) => {
    try {
      const response = await groupPointsWithAI(points, {
        apiGateway: 'http://localhost:5000',
        accessKey: '',
        secretKey: ''
      });
      
      return response.grouped_points;
    } catch (err) {
      console.error('Error in AI grouping:', err);
      throw err;
    }
  };

  return { handleAIGrouping };
}`,
          after: `
import { useState } from 'react';
import { useBMSClient } from '../hooks/useBMSClient';

export function useAIGrouping() {
  const bmsClient = useBMSClient({
    apiGateway: 'http://localhost:5000',
    accessKey: '',
    secretKey: ''
  });
  
  const handleAIGrouping = async (points) => {
    try {
      const response = await bmsClient.groupPointsWithAI(points);
      
      return response.grouped_points;
    } catch (err) {
      console.error('Error in AI grouping:', err);
      throw err;
    }
  };

  return { handleAIGrouping };
}`
        }
      ]
    }
  ];
  
  // Handle file selection
  const handleFileSelect = (file: string) => {
    setSelectedFile(file);
    
    // In a real implementation, this would load the file content from the filesystem
    // For this demo, we'll simulate loading the content
    if (file === 'src/hooks/groupPoints/useAIGrouping.ts') {
      setFileContent(`import { useState } from 'react';
import { BMSPoint, PointGroup } from '../../types/apiTypes';
import { groupPointsWithAI } from '../../api/bmsService';

type AIStrategy = 'default' | 'ai' | 'ontology';

interface UseAIGroupingOptions {
  onStartGrouping?: () => void;
  onGroupingSuccess?: (groups: Record<string, PointGroup>) => void;
  onGroupingError?: (error: string) => void;
  onGroupingComplete?: () => void;
}

/**
 * Hook for handling AI-assisted grouping of points
 */
export function useAIGrouping(options: UseAIGroupingOptions = {}) {
  const [aiStrategy, setAiStrategy] = useState<AIStrategy>('default');
  const [isProcessingAI, setIsProcessingAI] = useState<boolean>(false);
  const [aiGroupingError, setAiGroupingError] = useState<string | null>(null);
  const [aiGroupingMethod, setAiGroupingMethod] = useState<string | null>(null);

  // Handle AI-assisted grouping
  const handleAIGrouping = async (points: BMSPoint[]) => {
    // Check if there are points available
    if (points.length === 0) {
      const errorMessage = 'No points available for AI grouping. Please upload points first.';
      setAiGroupingError(errorMessage);
      if (options.onGroupingError) options.onGroupingError(errorMessage);
      return;
    }
    
    // Set processing state
    setIsProcessingAI(true);
    setAiGroupingError(null);
    setAiGroupingMethod(null);
    
    // Notify start of grouping
    if (options.onStartGrouping) options.onStartGrouping();
    
    try {
      console.log(\`Starting AI grouping with \${points.length} points...\`);
      
      // Call API to group points
      const response = await groupPointsWithAI(points, {
        apiGateway: process.env.REACT_APP_API_URL || process.env.REACT_APP_BMS_API_URL || 'http://localhost:5000',
        accessKey: '',
        secretKey: '',
        orgId: '',
        assetId: ''
      });
      
      console.log('AI grouping response:', response);
      
      if (response.success && response.grouped_points) {
        // Transform the AI grouped points to our format
        const newGroups: Record<string, PointGroup> = {};
        
        Object.entries(response.grouped_points).forEach(([key, value]) => {
          const groupId = \`group-\${Date.now()}-\${key}\`;
          newGroups[groupId] = {
            id: groupId,
            name: value.name,
            description: value.description,
            points: value.points,
            subgroups: {} // Initialize empty subgroups
          };
        });
        
        // Log created groups
        console.log(\`Created \${Object.keys(newGroups).length} groups from AI grouping\`);
        
        // Check if the API used a fallback method
        if (response.method && response.method !== aiStrategy) {
          setAiGroupingError(\`AI grouping used fallback \${response.method} method instead.\`);
          console.log(\`API used fallback method: \${response.method}\`);
        }
        
        // Store the method used for display
        if (response.method) {
          setAiGroupingMethod(response.method);
        }
        
        // Call success callback with the new groups
        if (options.onGroupingSuccess) {
          options.onGroupingSuccess(newGroups);
        }
      } else {
        // Handle failed response
        const errorMsg = response.error || 'Failed to group points with AI';
        console.error('AI grouping failed:', errorMsg);
        setAiGroupingError(errorMsg);
        if (options.onGroupingError) options.onGroupingError(errorMsg);
      }
    } catch (err) {
      // Handle exceptions
      const errorMessage = err instanceof Error ? err.message : 'Unknown error during AI grouping';
      console.error('Error in AI grouping:', errorMessage, err);
      const fullErrorMessage = \`AI grouping failed: \${errorMessage}. Check that the backend server is running.\`;
      setAiGroupingError(fullErrorMessage);
      if (options.onGroupingError) options.onGroupingError(fullErrorMessage);
    } finally {
      setIsProcessingAI(false);
      if (options.onGroupingComplete) options.onGroupingComplete();
    }
  };

  return {
    aiStrategy,
    isProcessingAI,
    aiGroupingError,
    aiGroupingMethod,
    setAiStrategy,
    handleAIGrouping
  };
}`);
    } else if (file === 'src/pages/FetchPoints/FetchPoints.tsx') {
      setFileContent(`import React, { useState, useEffect } from 'react';
import { fetchPoints } from '../../api/bmsService';

export const FetchPoints: React.FC = () => {
  const [points, setPoints] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const loadPoints = async () => {
      setLoading(true);
      try {
        const result = await fetchPoints('asset123', 'device456', '192.168.1.100', {
          apiGateway: 'http://localhost:5000'
        });
        setPoints(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    loadPoints();
  }, []);
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div>
      <h1>Fetched Points</h1>
      <ul>
        {points.map(point => (
          <li key={point.id}>{point.pointName}</li>
        ))}
      </ul>
    </div>
  );
}`);
    } else {
      setFileContent('');
    }
    
    setRefactoredContent('');
    setChanges([]);
  };
  
  // Handle pattern selection
  const handlePatternSelect = (patternId: string) => {
    setActivePattern(patternId);
    
    // In a real implementation, this would analyze the file and suggest changes
    const pattern = migrationPatterns.find(p => p.id === patternId);
    if (!pattern || !fileContent) return;
    
    // Very basic pattern matching for demo purposes
    // A real implementation would use AST parsing for accurate code transformation
    let content = fileContent;
    const contentLines = content.split('\n');
    const newChanges: {line: number; original: string; new: string}[] = [];
    
    // Look for import patterns
    for (let i = 0; i < contentLines.length; i++) {
      const line = contentLines[i];
      if (line.includes(pattern.id) && line.includes('import') && line.includes('bmsService')) {
        newChanges.push({
          line: i + 1,
          original: line,
          new: line.replace(/import.*from.*bmsService.*/, pattern.importReplacement)
        });
      }
    }
    
    // Look for usage patterns
    for (let i = 0; i < contentLines.length; i++) {
      const line = contentLines[i];
      if (line.includes(pattern.id) && line.includes('(') && !line.includes('import')) {
        // This is a very simplistic approach - a real implementation would be more sophisticated
        const newLine = line.replace(
          new RegExp(`${pattern.id}\\s*\\(.*\\)`, 'g'), 
          line.includes('await') ? `await ${pattern.usageReplacement}` : pattern.usageReplacement
        );
        newChanges.push({
          line: i + 1,
          original: line,
          new: newLine
        });
      }
    }
    
    setChanges(newChanges);
    
    // Apply changes to create refactored content
    const refactored = [...contentLines];
    newChanges.forEach(change => {
      refactored[change.line - 1] = change.new;
    });
    setRefactoredContent(refactored.join('\n'));
  };
  
  // Handle applying changes
  const handleApplyChanges = () => {
    // In a real implementation, this would save the changes to the file
    alert('Changes applied successfully! In a real implementation, this would save the file.');
    
    // Update the file content to show the changes have been applied
    setFileContent(refactoredContent);
    setRefactoredContent('');
    setChanges([]);
    setActivePattern(null);
  };
  
  return (
    <PageLayout>
      <div className="devtools-container">
        <header className="devtools-header">
          <h1>Migration Assistant</h1>
          <p className="devtools-subtitle">
            Automate the process of migrating from deprecated API services to the new BMSClient architecture
          </p>
        </header>
        
        <div className="migration-assistant-layout">
          <Card className="migration-files-card">
            <div className="devtools-card-header">
              <h3>Select File to Refactor</h3>
            </div>
            <div className="devtools-card-body">
              <div className="migration-file-list">
                <div 
                  className={`migration-file-item ${selectedFile === 'src/hooks/groupPoints/useAIGrouping.ts' ? 'active' : ''}`}
                  onClick={() => handleFileSelect('src/hooks/groupPoints/useAIGrouping.ts')}
                >
                  <div className="migration-file-icon">📄</div>
                  <div className="migration-file-name">useAIGrouping.ts</div>
                </div>
                <div 
                  className={`migration-file-item ${selectedFile === 'src/pages/FetchPoints/FetchPoints.tsx' ? 'active' : ''}`}
                  onClick={() => handleFileSelect('src/pages/FetchPoints/FetchPoints.tsx')}
                >
                  <div className="migration-file-icon">📄</div>
                  <div className="migration-file-name">FetchPoints.tsx</div>
                </div>
              </div>
            </div>
          </Card>
          
          {selectedFile && (
            <>
              <Card className="migration-patterns-card">
                <div className="devtools-card-header">
                  <h3>Select Migration Pattern</h3>
                </div>
                <div className="devtools-card-body">
                  <div className="migration-pattern-list">
                    {migrationPatterns.map(pattern => (
                      <div 
                        key={pattern.id}
                        className={`migration-pattern-item ${activePattern === pattern.id ? 'active' : ''}`}
                        onClick={() => handlePatternSelect(pattern.id)}
                      >
                        <div className="migration-pattern-name">{pattern.name}</div>
                        <div className="migration-pattern-description">{pattern.description}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
              
              <div className="migration-editor-container">
                <Card className="migration-editor-card">
                  <div className="devtools-card-header">
                    <h3>File Content</h3>
                  </div>
                  <div className="devtools-card-body">
                    <pre className="migration-code">{fileContent}</pre>
                  </div>
                </Card>
                
                {refactoredContent && (
                  <Card className="migration-editor-card">
                    <div className="devtools-card-header">
                      <h3>Refactored Content</h3>
                      <Button 
                        variant="primary" 
                        size="small"
                        onClick={handleApplyChanges}
                      >
                        Apply Changes
                      </Button>
                    </div>
                    <div className="devtools-card-body">
                      <pre className="migration-code">{refactoredContent}</pre>
                    </div>
                  </Card>
                )}
                
                {changes.length > 0 && (
                  <Card className="migration-changes-card">
                    <div className="devtools-card-header">
                      <h3>Suggested Changes</h3>
                    </div>
                    <div className="devtools-card-body">
                      <div className="migration-changes-list">
                        {changes.map((change, index) => (
                          <div key={index} className="migration-change-item">
                            <div className="migration-change-line">Line {change.line}</div>
                            <div className="migration-change-content">
                              <div className="migration-change-original">
                                <div className="migration-change-label">Original</div>
                                <pre>{change.original}</pre>
                              </div>
                              <div className="migration-change-arrow">→</div>
                              <div className="migration-change-new">
                                <div className="migration-change-label">New</div>
                                <pre>{change.new}</pre>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </Card>
                )}
              </div>
              
              {activePattern && (
                <Card className="migration-example-card">
                  <div className="devtools-card-header">
                    <h3>Example Migration</h3>
                  </div>
                  <div className="devtools-card-body">
                    <div className="migration-example">
                      {migrationPatterns.find(p => p.id === activePattern)?.examples.map((example, index) => (
                        <div key={index} className="migration-example-item">
                          <div className="migration-example-column">
                            <h4>Before</h4>
                            <pre className="migration-code">{example.before}</pre>
                          </div>
                          <div className="migration-example-arrow">→</div>
                          <div className="migration-example-column">
                            <h4>After</h4>
                            <pre className="migration-code">{example.after}</pre>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </PageLayout>
  );
};

export default MigrationAssistant;