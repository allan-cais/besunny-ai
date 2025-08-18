/**
 * Python Backend Hook
 * Optimized for maximum efficiency and reliability
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { pythonBackendServices, BackendHealthStatus, BackendMetrics } from '../lib/python-backend-services';
import { productionConfig } from '../config/production-config';

export interface UsePythonBackendOptions {
  autoConnect?: boolean;
  autoHealthCheck?: boolean;
  healthCheckInterval?: number;
}

export interface UsePythonBackendReturn {
  // Connection state
  isConnected: boolean;
  isConnecting: boolean;
  isHealthy: boolean;
  
  // Health status
  health: BackendHealthStatus | null;
  metrics: BackendMetrics | null;
  
  // Connection management
  connect: () => Promise<void>;
  disconnect: () => void;
  checkConnection: () => Promise<void>;
  
  // Error handling
  error: string | null;
  clearError: () => void;
  
  // Utility
  baseUrl: string;
  isEnabled: boolean;
}

export function usePythonBackend(options: UsePythonBackendOptions = {}): UsePythonBackendReturn {
  const {
    autoConnect = true,
    autoHealthCheck = true,
    healthCheckInterval = 30000, // 30 seconds
  } = options;

  // State
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isHealthy, setIsHealthy] = useState(false);
  const [health, setHealth] = useState<BackendHealthStatus | null>(null);
  const [metrics, setMetrics] = useState<BackendMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Refs
  const healthCheckIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isInitializedRef = useRef(false);

  // Check if Python backend is enabled
  const isEnabled = productionConfig.features.pythonBackend;

  // Get base URL
  const baseUrl = productionConfig.backend.baseUrl;

  // Initialize services
  const initializeServices = useCallback(async () => {
    if (!isEnabled || isInitializedRef.current) return;
    
    try {
      await pythonBackendServices.initialize();
      isInitializedRef.current = true;
    } catch (err) {
      console.error('Failed to initialize Python backend services:', err);
      setError(err instanceof Error ? err.message : 'Initialization failed');
    }
  }, [isEnabled]);

  // Connection management
  const connect = useCallback(async () => {
    if (!isEnabled || isConnecting || isConnected) return;
    
    setIsConnecting(true);
    setError(null);
    
    try {
      await initializeServices();
      
      // Test connection with health check
      const healthStatus = await pythonBackendServices.checkHealth();
      
      setIsConnected(healthStatus.isConnected);
      setIsHealthy(healthStatus.isHealthy);
      setHealth(healthStatus);
      setError(healthStatus.error || null);
      
      if (healthStatus.isConnected && healthStatus.isHealthy) {
        console.log('Python backend connected successfully');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Connection failed';
      setError(errorMessage);
      setIsConnected(false);
      setIsHealthy(false);
      console.error('Python backend connection failed:', err);
    } finally {
      setIsConnecting(false);
    }
  }, [isEnabled, isConnecting, isConnected, initializeServices]);

  const disconnect = useCallback(() => {
    setIsConnected(false);
    setIsHealthy(false);
    setHealth(null);
    setMetrics(null);
    setError(null);
    
    if (healthCheckIntervalRef.current) {
      clearInterval(healthCheckIntervalRef.current);
      healthCheckIntervalRef.current = null;
    }
    
    console.log('Python backend disconnected');
  }, []);

  const checkConnection = useCallback(async () => {
    if (!isEnabled || !isConnected) return;
    
    try {
      const healthStatus = await pythonBackendServices.checkHealth();
      const currentMetrics = pythonBackendServices.getMetrics();
      
      setHealth(healthStatus);
      setMetrics(currentMetrics);
      setIsHealthy(healthStatus.isHealthy);
      setError(healthStatus.error || null);
      
      // Update connection state if health check fails
      if (!healthStatus.isConnected) {
        setIsConnected(false);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Health check failed';
      setError(errorMessage);
      setIsHealthy(false);
      console.error('Python backend health check failed:', err);
    }
  }, [isEnabled, isConnected]);

  // Error handling
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Auto-connect effect
  useEffect(() => {
    if (autoConnect && isEnabled) {
      connect();
    }
    
    return () => {
      if (healthCheckIntervalRef.current) {
        clearInterval(healthCheckIntervalRef.current);
      }
    };
  }, [autoConnect, isEnabled, connect]);

  // Auto health check effect
  useEffect(() => {
    if (!autoHealthCheck || !isConnected || !isEnabled) return;
    
    // Initial health check
    checkConnection();
    
    // Set up periodic health checks
    healthCheckIntervalRef.current = setInterval(checkConnection, healthCheckInterval);
    
    return () => {
      if (healthCheckIntervalRef.current) {
        clearInterval(healthCheckIntervalRef.current);
      }
    };
  }, [autoHealthCheck, isConnected, isEnabled, healthCheckInterval, checkConnection]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (healthCheckIntervalRef.current) {
        clearInterval(healthCheckIntervalRef.current);
      }
    };
  }, []);

  return {
    // Connection state
    isConnected,
    isConnecting,
    isHealthy,
    
    // Health status
    health,
    metrics,
    
    // Connection management
    connect,
    disconnect,
    checkConnection,
    
    // Error handling
    error,
    clearError,
    
    // Utility
    baseUrl,
    isEnabled,
  };
}
