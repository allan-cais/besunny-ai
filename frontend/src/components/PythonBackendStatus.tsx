// Python Backend Status Indicator
// Shows the current status of the Python backend integration

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { usePythonBackend } from '@/hooks/use-python-backend';
import { features, config } from '@/config';
import { 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  RefreshCw, 
  Server, 
  Wifi, 
  WifiOff,
  Settings
} from 'lucide-react';

interface PythonBackendStatusProps {
  showDetails?: boolean;
  className?: string;
}

export function PythonBackendStatus({ showDetails = false, className = '' }: PythonBackendStatusProps) {
  const { isConnected, isEnabled, error, checkConnection } = usePythonBackend();

  const getStatusIcon = () => {
    if (!isEnabled) {
      // Check if we're still waiting for config to load
      if (config.pythonBackend.url === '') {
        return <RefreshCw className="h-4 w-4 animate-spin" />;
      }
      return <Settings className="h-4 w-4" />;
    }
    if (isConnected) {
      return <CheckCircle className="h-4 w-4" />;
    }
    if (error) {
      return <XCircle className="h-4 w-4" />;
    }
    return <AlertCircle className="h-4 w-4" />;
  };

  const getStatusColor = () => {
    if (!isEnabled) {
      // Check if we're still waiting for config to load
      if (config.pythonBackend.url === '') {
        return 'bg-blue-100 text-blue-800 hover:bg-blue-100';
      }
      return 'bg-gray-100 text-gray-800 hover:bg-gray-100';
    }
    if (isConnected) {
      return 'bg-green-100 text-green-800 hover:bg-green-100';
    }
    if (error) {
      return 'bg-red-100 text-red-800 hover:bg-red-100';
    }
    return 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100';
  };

  const getStatusText = () => {
    if (!isEnabled) {
      // Check if we're still waiting for config to load
      if (config.pythonBackend.url === '') {
        return 'Loading...';
      }
      return 'Disabled';
    }
    if (isConnected) {
      return 'Connected';
    }
    if (error) {
      return 'Error';
    }
    return 'Checking...';
  };

  const getStatusDescription = () => {
    if (!isEnabled) {
      // Check if we're still waiting for config to load
      if (config.pythonBackend.url === '') {
        return 'Loading Python backend configuration...';
      }
      return 'Python backend is disabled in configuration';
    }
    if (isConnected) {
      return 'Python backend is available and ready';
    }
    if (error) {
      return error;
    }
    return 'Checking Python backend availability...';
  };

  const handleRefresh = async () => {
    await checkConnection();
  };

  if (!features.isPythonBackendEnabled() && !showDetails) {
    return null;
  }

  if (!showDetails) {
    return (
      <Badge 
        variant="secondary" 
        className={`${getStatusColor()} text-xs cursor-pointer`}
        onClick={handleRefresh}
        title="Click to refresh status"
      >
        <Server className="h-3 w-3 mr-1" />
        Python Backend: {getStatusText()}
      </Badge>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Server className="h-4 w-4" />
          Python Backend Status
        </CardTitle>
        <CardDescription>
          Integration status with Python backend services
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status Overview */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <span className="font-medium">{getStatusText()}</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={!isEnabled}
          >
            <RefreshCw className="h-3 w-3 mr-1" />
            Refresh
          </Button>
        </div>

        {/* Status Description */}
        <p className="text-sm text-muted-foreground">
          {getStatusDescription()}
        </p>

        {/* Feature Status */}
        {isEnabled && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Service Status</h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
                              <div className="flex items-center gap-2">
                  <Wifi className={`h-3 w-3 ${features.isPythonBackendEnabled() ? 'text-green-600' : 'text-gray-400'}`} />
                  <span>Calendar</span>
                </div>
                <div className="flex items-center gap-2">
                  <Wifi className={`h-3 w-3 ${features.isPythonBackendEnabled() ? 'text-green-600' : 'text-gray-400'}`} />
                  <span>Documents</span>
                </div>
                <div className="flex items-center gap-2">
                  <Wifi className={`h-3 w-3 ${features.isPythonBackendEnabled() ? 'text-green-600' : 'text-gray-400'}`} />
                  <span>Projects</span>
                </div>
                <div className="flex items-center gap-2">
                  <Wifi className={`h-3 w-3 ${features.isPythonBackendEnabled() ? 'text-green-600' : 'text-gray-400'}`} />
                  <span>Drive</span>
                </div>
                <div className="flex items-center gap-2">
                  <Wifi className={`h-3 w-3 ${features.isPythonBackendEnabled() ? 'text-green-600' : 'text-gray-400'}`} />
                  <span>Emails</span>
                </div>
                <div className="flex items-center gap-2">
                  <Wifi className={`h-3 w-3 ${features.isPythonBackendEnabled() ? 'text-green-600' : 'text-gray-400'}`} />
                  <span>AI Classification</span>
                </div>
            </div>
          </div>
        )}

        {/* Connection Details */}
        {isEnabled && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Connection Details</h4>
            <div className="text-xs space-y-1 text-muted-foreground">
              <div className="flex justify-between">
                <span>Enabled:</span>
                <span className={isEnabled ? 'text-green-600' : 'text-red-600'}>
                  {isEnabled ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Available:</span>
                <span className={isConnected ? 'text-green-600' : 'text-red-600'}>
                  {isConnected ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Connected:</span>
                <span className={isConnected ? 'text-green-600' : 'text-red-600'}>
                  {isConnected ? 'Yes' : 'No'}
                </span>
              </div>
              {error && (
                <div className="flex justify-between">
                  <span>Last Check:</span>
                  <span>{new Date().toLocaleTimeString()}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error Details */}
        {error && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-red-600">Error Details</h4>
            <p className="text-xs text-red-600 bg-red-50 p-2 rounded">
              {error}
            </p>
          </div>
        )}

        {/* Configuration Info */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium">Configuration</h4>
          <div className="text-xs space-y-1 text-muted-foreground">
            <div className="flex justify-between">
              <span>Backend URL:</span>
              <span className="font-mono">
                {features.isPythonBackendEnabled() ? 'Configured' : 'Not configured'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Feature Flag:</span>
              <span className={features.isPythonBackendEnabled() ? 'text-green-600' : 'text-red-600'}>
                {features.isPythonBackendEnabled() ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default PythonBackendStatus;
