// Python Backend Status Indicator
// Shows the current status of the Python backend integration

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { usePythonBackend } from '@/hooks/use-python-backend';
import { features } from '@/config';
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
  const { status, checkConnection, isFeatureEnabled } = usePythonBackend();

  const getStatusIcon = () => {
    if (!status.isEnabled) {
      return <Settings className="h-4 w-4" />;
    }
    if (status.isConnected) {
      return <CheckCircle className="h-4 w-4" />;
    }
    if (status.error) {
      return <XCircle className="h-4 w-4" />;
    }
    return <AlertCircle className="h-4 w-4" />;
  };

  const getStatusColor = () => {
    if (!status.isEnabled) {
      return 'bg-gray-100 text-gray-800 hover:bg-gray-100';
    }
    if (status.isConnected) {
      return 'bg-green-100 text-green-800 hover:bg-green-100';
    }
    if (status.error) {
      return 'bg-red-100 text-red-800 hover:bg-red-100';
    }
    return 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100';
  };

  const getStatusText = () => {
    if (!status.isEnabled) {
      return 'Disabled';
    }
    if (status.isConnected) {
      return 'Connected';
    }
    if (status.error) {
      return 'Error';
    }
    return 'Checking...';
  };

  const getStatusDescription = () => {
    if (!status.isEnabled) {
      return 'Python backend is disabled in configuration';
    }
    if (status.isConnected) {
      return 'Python backend is available and ready';
    }
    if (status.error) {
      return status.error;
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
            disabled={!status.isEnabled}
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
        {status.isEnabled && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Service Status</h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-2">
                <Wifi className={`h-3 w-3 ${isFeatureEnabled('calendar') ? 'text-green-600' : 'text-gray-400'}`} />
                <span>Calendar</span>
              </div>
              <div className="flex items-center gap-2">
                <Wifi className={`h-3 w-3 ${isFeatureEnabled('documents') ? 'text-green-600' : 'text-gray-400'}`} />
                <span>Documents</span>
              </div>
              <div className="flex items-center gap-2">
                <Wifi className={`h-3 w-3 ${isFeatureEnabled('projects') ? 'text-green-600' : 'text-gray-400'}`} />
                <span>Projects</span>
              </div>
              <div className="flex items-center gap-2">
                <Wifi className={`h-3 w-3 ${isFeatureEnabled('drive') ? 'text-green-600' : 'text-gray-400'}`} />
                <span>Drive</span>
              </div>
              <div className="flex items-center gap-2">
                <Wifi className={`h-3 w-3 ${isFeatureEnabled('emails') ? 'text-green-600' : 'text-gray-400'}`} />
                <span>Emails</span>
              </div>
              <div className="flex items-center gap-2">
                <Wifi className={`h-3 w-3 ${isFeatureEnabled('classification') ? 'text-green-600' : 'text-gray-400'}`} />
                <span>AI Classification</span>
              </div>
            </div>
          </div>
        )}

        {/* Connection Details */}
        {status.isEnabled && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Connection Details</h4>
            <div className="text-xs space-y-1 text-muted-foreground">
              <div className="flex justify-between">
                <span>Enabled:</span>
                <span className={status.isEnabled ? 'text-green-600' : 'text-red-600'}>
                  {status.isEnabled ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Available:</span>
                <span className={status.isAvailable ? 'text-green-600' : 'text-red-600'}>
                  {status.isAvailable ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Connected:</span>
                <span className={status.isConnected ? 'text-green-600' : 'text-red-600'}>
                  {status.isConnected ? 'Yes' : 'No'}
                </span>
              </div>
              {status.lastCheck && (
                <div className="flex justify-between">
                  <span>Last Check:</span>
                  <span>{status.lastCheck.toLocaleTimeString()}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error Details */}
        {status.error && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-red-600">Error Details</h4>
            <p className="text-xs text-red-600 bg-red-50 p-2 rounded">
              {status.error}
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
