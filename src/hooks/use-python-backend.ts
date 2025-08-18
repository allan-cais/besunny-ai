/**
 * React Hook for Python Backend API Integration
 * Provides easy access to Python backend services with state management
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { 
  pythonBackendAPI, 
  type ApiResponse,
  type UserProfile,
  type UserPreferences,
  type Project,
  type ProjectMember,
  type AIOrchestrationRequest,
  type AIOrchestrationResponse,
  type PythonBackendConfig
} from '../lib/python-backend-api';

export interface UsePythonBackendOptions {
  config?: Partial<PythonBackendConfig>;
  autoConnect?: boolean;
  retryOnFailure?: boolean;
}

export interface UsePythonBackendReturn {
  // Connection state
  isConnected: boolean;
  isConnecting: boolean;
  connectionError: string | null;
  
  // API state
  isLoading: boolean;
  error: string | null;
  
  // Health check
  health: {
    status: string;
    version: string;
    timestamp: number;
  } | null;
  
  // User management
  userProfile: UserProfile | null;
  userPreferences: UserPreferences | null;
  
  // Project management
  projects: Project[];
  currentProject: Project | null;
  
  // AI orchestration
  aiResponse: AIOrchestrationResponse | null;
  aiHistory: AIOrchestrationResponse[];
  
  // Connection methods
  connect: () => Promise<void>;
  disconnect: () => void;
  
  // Health methods
  checkHealth: () => Promise<void>;
  
  // User methods
  fetchUserProfile: (userId: string) => Promise<void>;
  updateUserProfile: (userId: string, profile: Partial<UserProfile>) => Promise<void>;
  updateUserPreferences: (userId: string, preferences: Partial<UserPreferences>) => Promise<void>;
  
  // Project methods
  fetchProjects: (userId: string) => Promise<void>;
  fetchProject: (projectId: string) => Promise<void>;
  createProject: (project: Omit<Project, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
  updateProject: (projectId: string, updates: Partial<Project>) => Promise<void>;
  deleteProject: (projectId: string) => Promise<void>;
  addProjectMember: (projectId: string, member: Omit<ProjectMember, 'user_id'>) => Promise<void>;
  removeProjectMember: (projectId: string, userId: string) => Promise<void>;
  
  // AI methods
  orchestrateAI: (request: AIOrchestrationRequest) => Promise<void>;
  fetchAIHistory: (userId: string) => Promise<void>;
  
  // Utility methods
  clearError: () => void;
  retryLastOperation: () => Promise<void>;
}

export function usePythonBackend(options: UsePythonBackendOptions = {}): UsePythonBackendReturn {
  const {
    config = {},
    autoConnect = true,
    retryOnFailure = true,
  } = options;

  // State
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Data state
  const [health, setHealth] = useState<any>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [userPreferences, setUserPreferences] = useState<UserPreferences | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [aiResponse, setAiResponse] = useState<AIOrchestrationResponse | null>(null);
  const [aiHistory, setAiHistory] = useState<AIOrchestrationResponse[]>([]);
  
  // Refs for tracking operations
  const lastOperation = useRef<{ type: string; params: any[] } | null>(null);
  const apiInstance = useRef(pythonBackendAPI);

  // Update API configuration
  useEffect(() => {
    if (config.baseUrl) {
      apiInstance.current = new (apiInstance.current.constructor as any)({
        ...apiInstance.current,
        ...config,
      });
    }
  }, [config]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
  }, [autoConnect]);

  // Connection management
  const connect = useCallback(async () => {
    if (isConnecting || isConnected) return;
    
    setIsConnecting(true);
    setConnectionError(null);
    
    try {
      // Test connection with health check
      const healthResponse = await apiInstance.current.checkHealth();
      
      if (healthResponse.success) {
        setIsConnected(true);
        setHealth(healthResponse.data);
        setConnectionError(null);
      } else {
        throw new Error(healthResponse.error || 'Health check failed');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Connection failed';
      setConnectionError(errorMessage);
      setIsConnected(false);
    } finally {
      setIsConnecting(false);
    }
  }, [isConnecting, isConnected]);

  const disconnect = useCallback(() => {
    setIsConnected(false);
    setConnectionError(null);
    setHealth(null);
    // Clear all data
    setUserProfile(null);
    setUserPreferences(null);
    setProjects([]);
    setCurrentProject(null);
    setAiResponse(null);
    setAiHistory([]);
  }, []);

  // Health check
  const checkHealth = useCallback(async () => {
    if (!isConnected) return;
    
    try {
      const response = await apiInstance.current.checkHealth();
      if (response.success) {
        setHealth(response.data);
      }
    } catch (err) {
      console.error('Health check failed:', err);
    }
  }, [isConnected]);

  // User management methods
  const fetchUserProfile = useCallback(async (userId: string) => {
    if (!isConnected) return;
    
    setIsLoading(true);
    setError(null);
    lastOperation.current = { type: 'fetchUserProfile', params: [userId] };
    
    try {
      const response = await apiInstance.current.getUserProfile(userId);
      if (response.success && response.data) {
        setUserProfile(response.data);
        setUserPreferences(response.data.preferences);
      } else {
        throw new Error(response.error || 'Failed to fetch user profile');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected]);

  const updateUserProfile = useCallback(async (userId: string, profile: Partial<UserProfile>) => {
    if (!isConnected) return;
    
    setIsLoading(true);
    setError(null);
    lastOperation.current = { type: 'updateUserProfile', params: [userId, profile] };
    
    try {
      const response = await apiInstance.current.updateUserProfile(userId, profile);
      if (response.success && response.data) {
        setUserProfile(response.data);
        setUserPreferences(response.data.preferences);
      } else {
        throw new Error(response.error || 'Failed to update user profile');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected]);

  const updateUserPreferences = useCallback(async (userId: string, preferences: Partial<UserPreferences>) => {
    if (!isConnected) return;
    
    setIsLoading(true);
    setError(null);
    lastOperation.current = { type: 'updateUserPreferences', params: [userId, preferences] };
    
    try {
      const response = await apiInstance.current.updateUserPreferences(userId, preferences);
      if (response.success && response.data) {
        setUserPreferences(response.data);
        // Update user profile preferences as well
        setUserProfile(prev => prev ? { ...prev, preferences: response.data! } : null);
      } else {
        throw new Error(response.error || 'Failed to update user preferences');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected]);

  // Project management methods
  const fetchProjects = useCallback(async (userId: string) => {
    if (!isConnected) return;
    
    setIsLoading(true);
    setError(null);
    lastOperation.current = { type: 'fetchProjects', params: [userId] };
    
    try {
      const response = await apiInstance.current.getProjects(userId);
      if (response.success && response.data) {
        setProjects(response.data);
      } else {
        throw new Error(response.error || 'Failed to fetch projects');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected]);

  const fetchProject = useCallback(async (projectId: string) => {
    if (!isConnected) return;
    
    setIsLoading(true);
    setError(null);
    lastOperation.current = { type: 'fetchProject', params: [projectId] };
    
    try {
      const response = await apiInstance.current.getProject(projectId);
      if (response.success && response.data) {
        setCurrentProject(response.data);
      } else {
        throw new Error(response.error || 'Failed to fetch project');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected]);

  const createProject = useCallback(async (project: Omit<Project, 'id' | 'created_at' | 'updated_at'>) => {
    if (!isConnected) return;
    
    setIsLoading(true);
    setError(null);
    lastOperation.current = { type: 'createProject', params: [project] };
    
    try {
      const response = await apiInstance.current.createProject(project);
      if (response.success && response.data) {
        setProjects(prev => [...prev, response.data!]);
        setCurrentProject(response.data);
      } else {
        throw new Error(response.error || 'Failed to create project');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected]);

  const updateProject = useCallback(async (projectId: string, updates: Partial<Project>) => {
    if (!isConnected) return;
    
    setIsLoading(true);
    setError(null);
    lastOperation.current = { type: 'updateProject', params: [projectId, updates] };
    
    try {
      const response = await apiInstance.current.updateProject(projectId, updates);
      if (response.success && response.data) {
        const updatedProject = response.data;
        setProjects(prev => prev.map(p => p.id === projectId ? updatedProject : p));
        if (currentProject?.id === projectId) {
          setCurrentProject(updatedProject);
        }
      } else {
        throw new Error(response.error || 'Failed to update project');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected, currentProject]);

  const deleteProject = useCallback(async (projectId: string) => {
    if (!isConnected) return;
    
    setIsLoading(true);
    setError(null);
    lastOperation.current = { type: 'deleteProject', params: [projectId] };
    
    try {
      const response = await apiInstance.current.deleteProject(projectId);
      if (response.success) {
        setProjects(prev => prev.filter(p => p.id !== projectId));
        if (currentProject?.id === projectId) {
          setCurrentProject(null);
        }
      } else {
        throw new Error(response.error || 'Failed to delete project');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected, currentProject]);

  const addProjectMember = useCallback(async (projectId: string, member: Omit<ProjectMember, 'user_id'>) => {
    if (!isConnected) return;
    
    setIsLoading(true);
    setError(null);
    lastOperation.current = { type: 'addProjectMember', params: [projectId, member] };
    
    try {
      const response = await apiInstance.current.addProjectMember(projectId, member);
      if (response.success && response.data) {
        // Update projects list
        setProjects(prev => prev.map(p => {
          if (p.id === projectId) {
            return { ...p, members: [...p.members, response.data!] };
          }
          return p;
        }));
        
        // Update current project if it's the one being modified
        if (currentProject?.id === projectId) {
          setCurrentProject(prev => prev ? {
            ...prev,
            members: [...prev.members, response.data!]
          } : null);
        }
      } else {
        throw new Error(response.error || 'Failed to add project member');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected, currentProject]);

  const removeProjectMember = useCallback(async (projectId: string, userId: string) => {
    if (!isConnected) return;
    
    setIsLoading(true);
    setError(null);
    lastOperation.current = { type: 'removeProjectMember', params: [projectId, userId] };
    
    try {
      const response = await apiInstance.current.removeProjectMember(projectId, userId);
      if (response.success) {
        // Update projects list
        setProjects(prev => prev.map(p => {
          if (p.id === projectId) {
            return { ...p, members: p.members.filter(m => m.user_id !== userId) };
          }
          return p;
        }));
        
        // Update current project if it's the one being modified
        if (currentProject?.id === projectId) {
          setCurrentProject(prev => prev ? {
            ...prev,
            members: prev.members.filter(m => m.user_id !== userId)
          } : null);
        }
      } else {
        throw new Error(response.error || 'Failed to remove project member');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected, currentProject]);

  // AI orchestration methods
  const orchestrateAI = useCallback(async (request: AIOrchestrationRequest) => {
    if (!isConnected) return;
    
    setIsLoading(true);
    setError(null);
    lastOperation.current = { type: 'orchestrateAI', params: [request] };
    
    try {
      const response = await apiInstance.current.orchestrateAI(request);
      if (response.success && response.data) {
        setAiResponse(response.data);
        setAiHistory(prev => [response.data!, ...prev]);
      } else {
        throw new Error(response.error || 'AI orchestration failed');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected]);

  const fetchAIHistory = useCallback(async (userId: string) => {
    if (!isConnected) return;
    
    setIsLoading(true);
    setError(null);
    lastOperation.current = { type: 'fetchAIHistory', params: [userId] };
    
    try {
      const response = await apiInstance.current.getAIHistory(userId);
      if (response.success && response.data) {
        setAiHistory(response.data);
      } else {
        throw new Error(response.error || 'Failed to fetch AI history');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected]);

  // Utility methods
  const clearError = useCallback(() => {
    setError(null);
    setConnectionError(null);
  }, []);

  const retryLastOperation = useCallback(async () => {
    if (!lastOperation.current) return;
    
    const { type, params } = lastOperation.current;
    
    switch (type) {
      case 'fetchUserProfile':
        await fetchUserProfile(params[0]);
        break;
      case 'updateUserProfile':
        await updateUserProfile(params[0], params[1]);
        break;
      case 'updateUserPreferences':
        await updateUserPreferences(params[0], params[1]);
        break;
      case 'fetchProjects':
        await fetchProjects(params[0]);
        break;
      case 'fetchProject':
        await fetchProject(params[0]);
        break;
      case 'createProject':
        await createProject(params[0]);
        break;
      case 'updateProject':
        await updateProject(params[0], params[1]);
        break;
      case 'deleteProject':
        await deleteProject(params[0]);
        break;
      case 'addProjectMember':
        await addProjectMember(params[0], params[1]);
        break;
      case 'removeProjectMember':
        await removeProjectMember(params[0], params[1]);
        break;
      case 'orchestrateAI':
        await orchestrateAI(params[0]);
        break;
      case 'fetchAIHistory':
        await fetchAIHistory(params[0]);
        break;
      default:
        console.warn('Unknown operation type for retry:', type);
    }
  }, [
    fetchUserProfile, updateUserProfile, updateUserPreferences,
    fetchProjects, fetchProject, createProject, updateProject, deleteProject,
    addProjectMember, removeProjectMember, orchestrateAI, fetchAIHistory
  ]);

  // Periodic health check
  useEffect(() => {
    if (!isConnected) return;
    
    const interval = setInterval(checkHealth, 60000); // Check every minute
    
    return () => clearInterval(interval);
  }, [isConnected, checkHealth]);

  return {
    // Connection state
    isConnected,
    isConnecting,
    connectionError,
    
    // API state
    isLoading,
    error,
    
    // Data
    health,
    userProfile,
    userPreferences,
    projects,
    currentProject,
    aiResponse,
    aiHistory,
    
    // Methods
    connect,
    disconnect,
    checkHealth,
    fetchUserProfile,
    updateUserProfile,
    updateUserPreferences,
    fetchProjects,
    fetchProject,
    createProject,
    updateProject,
    deleteProject,
    addProjectMember,
    removeProjectMember,
    orchestrateAI,
    fetchAIHistory,
    clearError,
    retryLastOperation,
  };
}
