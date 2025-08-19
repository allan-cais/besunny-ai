import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Loader2, CheckCircle, XCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { productionConfig, healthCheckConfig, apiEndpoints } from '../config/production-config';

interface HealthStatus {
  status: 'loading' | 'healthy' | 'unhealthy' | 'error';
  message: string;
  timestamp: number;
  responseTime: number;
}

interface BackendHealth {
  main: HealthStatus;
  status: HealthStatus;
  ready: HealthStatus;
  live: HealthStatus;
  frontendTest: HealthStatus;
}

export const BackendConnectionTest: React.FC = () => {
  const [health, setHealth] = useState<BackendHealth>({
    main: { status: 'loading', message: 'Checking...', timestamp: 0, responseTime: 0 },
    status: { status: 'loading', message: 'Checking...', timestamp: 0, responseTime: 0 },
    ready: { status: 'loading', message: 'Checking...', timestamp: 0, responseTime: 0 },
    live: { status: 'loading', message: 'Checking...', timestamp: 0, responseTime: 0 },
    frontendTest: { status: 'loading', message: 'Checking...', timestamp: 0, responseTime: 0 }
  });

  const [isRunning, setIsRunning] = useState(false);
  const [lastCheck, setLastCheck] = useState<number>(0);

  const backendUrl = productionConfig.backend.baseUrl;

  const checkEndpoint = async (endpoint: string, name: keyof BackendHealth): Promise<HealthStatus> => {
    const startTime = Date.now();
    
    try {
      const response = await fetch(`${backendUrl}${endpoint}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(healthCheckConfig.timeout)
      });

      const responseTime = Date.now() - startTime;
      
      if (response.ok) {
        const data = await response.json();
        return {
          status: 'healthy',
          message: data.message || 'Endpoint is healthy',
          timestamp: Date.now(),
          responseTime
        };
      } else {
        return {
          status: 'unhealthy',
          message: `HTTP ${response.status}: ${response.statusText}`,
          timestamp: Date.now(),
          responseTime
        };
      }
    } catch (error) {
      const responseTime = Date.now() - startTime;
      const message = error instanceof Error ? error.message : 'Unknown error';
      
      return {
        status: 'error',
        message: `Connection failed: ${message}`,
        timestamp: Date.now(),
        responseTime
      };
    }
  };

  const runHealthChecks = async () => {
    setIsRunning(true);
    setLastCheck(Date.now());

    // Run all health checks in parallel for maximum efficiency
    const healthChecks = await Promise.allSettled([
      checkEndpoint(apiEndpoints.health, 'main'),
      checkEndpoint(apiEndpoints.healthStatus, 'status'),
      checkEndpoint(apiEndpoints.healthReady, 'ready'),
      checkEndpoint(apiEndpoints.healthLive, 'live'),
      checkEndpoint(apiEndpoints.frontendTest, 'frontendTest')
    ]);

    // Update health status
    setHealth({
      main: healthChecks[0].status === 'fulfilled' ? healthChecks[0].value : { status: 'error', message: 'Check failed', timestamp: Date.now(), responseTime: 0 },
      status: healthChecks[1].status === 'fulfilled' ? healthChecks[1].value : { status: 'error', message: 'Check failed', timestamp: Date.now(), responseTime: 0 },
      ready: healthChecks[2].status === 'fulfilled' ? healthChecks[2].value : { status: 'error', message: 'Check failed', timestamp: Date.now(), responseTime: 0 },
      live: healthChecks[3].status === 'fulfilled' ? healthChecks[3].value : { status: 'error', message: 'Check failed', timestamp: Date.now(), responseTime: 0 },
      frontendTest: healthChecks[4].status === 'fulfilled' ? healthChecks[4].value : { status: 'error', message: 'Check failed', timestamp: Date.now(), responseTime: 0 }
    });

    setIsRunning(false);
  };

  useEffect(() => {
    runHealthChecks();
    
    // Set up periodic health checks
    const interval = setInterval(runHealthChecks, healthCheckConfig.interval);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'unhealthy':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return <Badge variant="default" className="bg-green-100 text-green-800">Healthy</Badge>;
      case 'unhealthy':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Unhealthy</Badge>;
      case 'error':
        return <Badge variant="destructive">Error</Badge>;
      default:
        return <Badge variant="outline">Loading</Badge>;
    }
  };

  const overallStatus = Object.values(health).every(h => h.status === 'healthy') ? 'healthy' : 'degraded';

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Backend Health Monitor</span>
          <div className="flex items-center gap-2">
            {getStatusBadge(overallStatus)}
            <Button
              variant="outline"
              size="sm"
              onClick={runHealthChecks}
              disabled={isRunning}
            >
              <RefreshCw className={`h-4 w-4 ${isRunning ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardTitle>
        <CardDescription>
          Real-time monitoring of backend service health and connectivity
          {lastCheck > 0 && (
            <span className="block text-xs text-muted-foreground mt-1">
              Last checked: {new Date(lastCheck).toLocaleTimeString()}
            </span>
          )}
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Health Status Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(health).map(([key, status]) => (
            <Card key={key} className="p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</h4>
                {getStatusIcon(status.status)}
              </div>
              <p className="text-sm text-muted-foreground mb-2">{status.message}</p>
              <div className="flex items-center justify-between text-xs">
                <span>Response: {status.responseTime}ms</span>
                <span>{new Date(status.timestamp).toLocaleTimeString()}</span>
              </div>
            </Card>
          ))}
        </div>

        {/* Overall Status */}
        <Alert className={overallStatus === 'healthy' ? 'border-green-200 bg-green-50' : 'border-yellow-200 bg-yellow-50'}>
          <AlertDescription>
            <strong>Overall Status:</strong> {overallStatus === 'healthy' ? 'All systems operational' : 'Some systems experiencing issues'}
          </AlertDescription>
        </Alert>

        {/* Configuration Info */}
        <Card className="p-4 bg-muted/50">
          <h4 className="font-medium mb-2">Configuration</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium">Backend URL:</span>
              <span className="ml-2 font-mono text-xs">{backendUrl}</span>
            </div>
            <div>
              <span className="font-medium">Check Interval:</span>
              <span className="ml-2">{healthCheckConfig.interval / 1000}s</span>
            </div>
            <div>
              <span className="font-medium">Timeout:</span>
              <span className="ml-2">{healthCheckConfig.timeout / 1000}s</span>
            </div>
            <div>
              <span className="font-medium">Retries:</span>
              <span className="ml-2">{healthCheckConfig.retries}</span>
            </div>
          </div>
        </Card>
      </CardContent>
    </Card>
  );
};
