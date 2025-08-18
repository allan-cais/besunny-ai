// Python Backend Integration Test Component
// Comprehensive testing of all Python backend services

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { usePythonBackend } from '@/hooks/use-python-backend';
import { pythonBackendAPI } from '@/lib/python-backend-api';
import { features } from '@/config';
import { 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Play, 
  Server, 
  Calendar,
  FileText,
  FolderOpen,
  HardDrive,
  Mail,
  Brain,
  Loader2
} from 'lucide-react';

interface TestResult {
  service: string;
  status: 'pending' | 'running' | 'success' | 'error';
  message: string;
  duration?: number;
  error?: string;
}

interface PythonBackendIntegrationTestProps {
  className?: string;
}

export function PythonBackendIntegrationTest({ className = '' }: PythonBackendIntegrationTestProps) {
  const { status, checkConnection } = usePythonBackend();
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const services = [
    { name: 'Health Check', icon: Server, test: () => pythonBackendAPI.healthCheck() },
    { name: 'Calendar API', icon: Calendar, test: () => pythonBackendAPI.getUserMeetings() },
    { name: 'Documents API', icon: FileText, test: () => pythonBackendAPI.getDocuments() },
    { name: 'Projects API', icon: FolderOpen, test: () => pythonBackendAPI.getProjects() },
    { name: 'Drive API', icon: HardDrive, test: () => pythonBackendAPI.syncDriveFiles() },
    { name: 'Emails API', icon: Mail, test: () => pythonBackendAPI.getEmailProcessingStatus('test') },
    { name: 'Classification API', icon: Brain, test: () => pythonBackendAPI.classifyContent('test content', 'text') },
  ];

  const runAllTests = async () => {
    if (!features.isPythonBackendEnabled()) {
      setTestResults([{
        service: 'Configuration',
        status: 'error',
        message: 'Python backend is disabled in configuration',
        error: 'Feature flag disabled'
      }]);
      return;
    }

    setIsRunning(true);
    const results: TestResult[] = [];

    // Initialize all tests as pending
    services.forEach(service => {
      results.push({
        service: service.name,
        status: 'pending',
        message: 'Waiting to start...'
      });
    });

    setTestResults(results);

    // Run tests sequentially
    for (let i = 0; i < services.length; i++) {
      const service = services[i];
      const startTime = Date.now();

      // Update status to running
      setTestResults(prev => prev.map((result, index) => 
        index === i ? { ...result, status: 'running', message: 'Testing...' } : result
      ));

      try {
        const response = await service.test();
        const duration = Date.now() - startTime;

        if (response.success) {
          results[i] = {
            service: service.name,
            status: 'success',
            message: 'Service is working correctly',
            duration
          };
        } else {
          results[i] = {
            service: service.name,
            status: 'error',
            message: 'Service returned an error',
            duration,
            error: response.error || 'Unknown error'
          };
        }
      } catch (error) {
        const duration = Date.now() - startTime;
        results[i] = {
          service: service.name,
          status: 'error',
          message: 'Service test failed',
          duration,
          error: error instanceof Error ? error.message : 'Unknown error'
        };
      }

      // Update results
      setTestResults([...results]);

      // Small delay between tests
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    setIsRunning(false);
  };

  const runSingleTest = async (serviceIndex: number) => {
    const service = services[serviceIndex];
    const startTime = Date.now();

    // Update status to running
    setTestResults(prev => prev.map((result, index) => 
      index === serviceIndex ? { ...result, status: 'running', message: 'Testing...' } : result
    ));

    try {
      const response = await service.test();
      const duration = Date.now() - startTime;

      if (response.success) {
        setTestResults(prev => prev.map((result, index) => 
          index === serviceIndex ? {
            ...result,
            status: 'success',
            message: 'Service is working correctly',
            duration
          } : result
        ));
      } else {
        setTestResults(prev => prev.map((result, index) => 
          index === serviceIndex ? {
            ...result,
            status: 'error',
            message: 'Service returned an error',
            duration,
            error: response.error || 'Unknown error'
          } : result
        ));
      }
    } catch (error) {
      const duration = Date.now() - startTime;
      setTestResults(prev => prev.map((result, index) => 
        index === serviceIndex ? {
          ...result,
          status: 'error',
          message: 'Service test failed',
          duration,
          error: error instanceof Error ? error.message : 'Unknown error'
        } : result
      ));
    }
  };

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'pending':
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
      case 'running':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: TestResult['status']) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-100 text-gray-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'success':
        return 'bg-green-100 text-green-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: TestResult['status']) => {
    switch (status) {
      case 'pending':
        return 'Pending';
      case 'running':
        return 'Running';
      case 'success':
        return 'Success';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  const getSuccessRate = () => {
    if (testResults.length === 0) return 0;
    const successful = testResults.filter(result => result.status === 'success').length;
    return Math.round((successful / testResults.length) * 100);
  };

  const getAverageResponseTime = () => {
    const successfulTests = testResults.filter(result => result.status === 'success' && result.duration);
    if (successfulTests.length === 0) return 0;
    const totalDuration = successfulTests.reduce((sum, result) => sum + (result.duration || 0), 0);
    return Math.round(totalDuration / successfulTests.length);
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Server className="h-5 w-5" />
          Python Backend Integration Test
        </CardTitle>
        <CardDescription>
          Comprehensive testing of all Python backend services to ensure proper integration
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Configuration Status */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium">Configuration Status</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center justify-between">
              <span>Feature Enabled:</span>
              <Badge variant={features.isPythonBackendEnabled() ? 'default' : 'secondary'}>
                {features.isPythonBackendEnabled() ? 'Yes' : 'No'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span>Backend Connected:</span>
              <Badge variant={status.isConnected ? 'default' : 'secondary'}>
                {status.isConnected ? 'Yes' : 'No'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span>Backend Available:</span>
              <Badge variant={status.isAvailable ? 'default' : 'secondary'}>
                {status.isAvailable ? 'Yes' : 'No'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span>Last Check:</span>
              <span className="text-muted-foreground">
                {status.lastCheck ? status.lastCheck.toLocaleTimeString() : 'Never'}
              </span>
            </div>
          </div>
        </div>

        <Separator />

        {/* Test Controls */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Service Tests</h3>
            <div className="flex gap-2">
              <Button
                onClick={checkConnection}
                variant="outline"
                size="sm"
                disabled={!features.isPythonBackendEnabled()}
              >
                Check Connection
              </Button>
              <Button
                onClick={runAllTests}
                disabled={!features.isPythonBackendEnabled() || isRunning}
                size="sm"
              >
                {isRunning ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Running Tests...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Run All Tests
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Test Results Summary */}
          {testResults.length > 0 && (
            <div className="grid grid-cols-3 gap-4 p-3 bg-muted rounded-lg">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{getSuccessRate()}%</div>
                <div className="text-xs text-muted-foreground">Success Rate</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {testResults.filter(r => r.status === 'success').length}
                </div>
                <div className="text-xs text-muted-foreground">Passed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {testResults.filter(r => r.status === 'error').length}
                </div>
                <div className="text-xs text-muted-foreground">Failed</div>
              </div>
            </div>
          )}

          {/* Individual Test Results */}
          <div className="space-y-2">
            {services.map((service, index) => {
              const result = testResults[index];
              const Icon = service.icon;
              
              return (
                <div
                  key={service.name}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <Icon className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{service.name}</span>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    {result && (
                      <>
                        <Badge variant="outline" className={getStatusColor(result.status)}>
                          {getStatusIcon(result.status)}
                          <span className="ml-1">{getStatusText(result.status)}</span>
                        </Badge>
                        {result.duration && (
                          <span className="text-xs text-muted-foreground">
                            {result.duration}ms
                          </span>
                        )}
                        {result.message && (
                          <span className="text-xs text-muted-foreground max-w-xs truncate">
                            {result.message}
                          </span>
                        )}
                      </>
                    )}
                    
                    <Button
                      onClick={() => runSingleTest(index)}
                      variant="outline"
                      size="sm"
                      disabled={!features.isPythonBackendEnabled() || isRunning}
                    >
                      <Play className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Performance Metrics */}
        {testResults.length > 0 && (
          <>
            <Separator />
            <div className="space-y-3">
              <h3 className="text-sm font-medium">Performance Metrics</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center justify-between">
                  <span>Average Response Time:</span>
                  <span className="font-mono">{getAverageResponseTime()}ms</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Total Tests:</span>
                  <span className="font-mono">{testResults.length}</span>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Error Details */}
        {testResults.some(result => result.error) && (
          <>
            <Separator />
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-red-600">Error Details</h3>
              <div className="space-y-2">
                {testResults
                  .filter(result => result.error)
                  .map((result, index) => (
                    <div key={index} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                      <div className="font-medium text-red-800">{result.service}</div>
                      <div className="text-sm text-red-600">{result.error}</div>
                    </div>
                  ))}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default PythonBackendIntegrationTest;
