import React, { useState, useEffect } from 'react';
import { pythonBackendConfig } from '../config/python-backend-config';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Loader2, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface BackendStatus {
  health: 'loading' | 'healthy' | 'unhealthy' | 'error';
  frontendTest: 'loading' | 'success' | 'error';
  v1Health: 'loading' | 'success' | 'error';
  apiTest: 'loading' | 'success' | 'error';
}

interface TestResult {
  status: 'loading' | 'success' | 'error';
  data?: any;
  error?: string;
}

export const BackendConnectionTest: React.FC = () => {
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({
    health: 'loading',
    frontendTest: 'loading',
    v1Health: 'loading',
    apiTest: 'loading',
  });

  const [testResults, setTestResults] = useState<Record<string, TestResult>>({});
  const [isRunning, setIsRunning] = useState(false);

  const backendUrl = pythonBackendConfig.baseUrl;

  const runTest = async (endpoint: string, testName: string): Promise<TestResult> => {
    try {
      const response = await fetch(`${backendUrl}${endpoint}`);
      if (response.ok) {
        const data = await response.json();
        return { status: 'success', data };
      } else {
        return { status: 'error', error: `HTTP ${response.status}: ${response.statusText}` };
      }
    } catch (error) {
      return { status: 'error', error: error instanceof Error ? error.message : 'Unknown error' };
    }
  };

  const runAllTests = async () => {
    setIsRunning(true);
    setBackendStatus({
      health: 'loading',
      frontendTest: 'loading',
      v1Health: 'loading',
      apiTest: 'loading',
    });

    // Test 1: Health Check
    const healthResult = await runTest('/health', 'Health Check');
    setBackendStatus(prev => ({ ...prev, health: healthResult.status === 'success' ? 'healthy' : 'unhealthy' }));
    setTestResults(prev => ({ ...prev, health: healthResult }));

    // Test 2: Frontend Integration Test
    const frontendResult = await runTest('/api/frontend-test', 'Frontend Integration');
    setBackendStatus(prev => ({ ...prev, frontendTest: frontendResult.status === 'success' ? 'success' : 'error' }));
    setTestResults(prev => ({ ...prev, frontendTest: frontendResult }));

    // Test 3: V1 Health Check
    const v1Result = await runTest('/v1/health', 'V1 Router Health');
    setBackendStatus(prev => ({ ...prev, v1Health: v1Result.status === 'success' ? 'success' : 'error' }));
    setTestResults(prev => ({ ...prev, v1Health: v1Result }));

    // Test 4: API Test
    const apiResult = await runTest('/api/test', 'Basic API');
    setBackendStatus(prev => ({ ...prev, apiTest: apiResult.status === 'success' ? 'success' : 'error' }));
    setTestResults(prev => ({ ...prev, apiTest: apiResult }));

    setIsRunning(false);
  };

  useEffect(() => {
    runAllTests();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'unhealthy':
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'loading':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'success':
        return <Badge variant="default" className="bg-green-500">Success</Badge>;
      case 'unhealthy':
      case 'error':
        return <Badge variant="destructive">Error</Badge>;
      case 'loading':
        return <Badge variant="secondary">Loading</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const allTestsPassed = Object.values(backendStatus).every(status => 
    status === 'healthy' || status === 'success'
  );

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🔗 Backend Connection Test
            {allTestsPassed && <Badge variant="default" className="bg-green-500">All Tests Passed</Badge>}
          </CardTitle>
          <CardDescription>
            Testing connection to BeSunny.ai Backend v17 at {backendUrl}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Health Check */}
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-2">
                {getStatusIcon(backendStatus.health)}
                <span>Health Check</span>
              </div>
              {getStatusBadge(backendStatus.health)}
            </div>

            {/* Frontend Test */}
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-2">
                {getStatusIcon(backendStatus.frontendTest)}
                <span>Frontend Integration</span>
              </div>
              {getStatusBadge(backendStatus.frontendTest)}
            </div>

            {/* V1 Health */}
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-2">
                {getStatusIcon(backendStatus.v1Health)}
                <span>V1 Router</span>
              </div>
              {getStatusBadge(backendStatus.v1Health)}
            </div>

            {/* API Test */}
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-2">
                {getStatusIcon(backendStatus.apiTest)}
                <span>Basic API</span>
              </div>
              {getStatusBadge(backendStatus.apiTest)}
            </div>
          </div>

          <Button 
            onClick={runAllTests} 
            disabled={isRunning}
            className="w-full"
          >
            {isRunning ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Running Tests...
              </>
            ) : (
              'Run Tests Again'
            )}
          </Button>

          {allTestsPassed && (
            <Alert className="border-green-200 bg-green-50">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800">
                🎉 All backend tests passed! Your v17 backend is fully operational and ready for frontend integration.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Detailed Test Results */}
      <Card>
        <CardHeader>
          <CardTitle>📊 Detailed Test Results</CardTitle>
          <CardDescription>View detailed responses from each endpoint</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {Object.entries(testResults).map(([testName, result]) => (
            <div key={testName} className="border rounded-lg p-4">
              <h4 className="font-semibold mb-2 capitalize">{testName}</h4>
              {result.status === 'loading' && (
                <div className="flex items-center gap-2 text-blue-600">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading...
                </div>
              )}
              {result.status === 'success' && result.data && (
                <div className="space-y-2">
                  <Badge variant="default" className="bg-green-500">Success</Badge>
                  <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
                    {JSON.stringify(result.data, null, 2)}
                  </pre>
                </div>
              )}
              {result.status === 'error' && result.error && (
                <div className="space-y-2">
                  <Badge variant="destructive">Error</Badge>
                  <p className="text-red-600">{result.error}</p>
                </div>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Connection Info */}
      <Card>
        <CardHeader>
          <CardTitle>🔧 Connection Information</CardTitle>
          <CardDescription>Backend configuration and endpoints</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-600">Backend URL</label>
              <p className="text-sm font-mono bg-gray-100 p-2 rounded">{backendUrl}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Environment</label>
              <p className="text-sm">{pythonBackendConfig.enableLogging ? 'Development' : 'Production'}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Timeout</label>
              <p className="text-sm">{pythonBackendConfig.timeout}ms</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Retry Attempts</label>
              <p className="text-sm">{pythonBackendConfig.retryAttempts}</p>
            </div>
          </div>
          
          <div className="pt-2">
            <label className="text-sm font-medium text-gray-600">Available Endpoints</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2">
              <code className="text-xs bg-gray-100 p-1 rounded">/health</code>
              <code className="text-xs bg-gray-100 p-1 rounded">/api/frontend-test</code>
              <code className="text-xs bg-gray-100 p-1 rounded">/v1/health</code>
              <code className="text-xs bg-gray-100 p-1 rounded">/api/test</code>
              <code className="text-xs bg-gray-100 p-1 rounded">/docs</code>
              <code className="text-xs bg-gray-100 p-1 rounded">/</code>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
