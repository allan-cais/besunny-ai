// Python Backend Hook
// Replaces use-supabase hook with Python backend services

import { useState, useEffect, useCallback } from 'react';
import { pythonBackendServices } from '../lib/python-backend-services';
import { supabase } from '../lib/supabase';
import type { 
  User, 
  Project, 
  Document, 
  ChatMessage, 
  ChatSession 
} from '../types';

export const usePythonBackend = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isBackendAvailable, setIsBackendAvailable] = useState(false);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Check backend availability on mount
  useEffect(() => {
    const checkBackendHealth = async () => {
      try {
        const response = await pythonBackendServices.checkHealth();
        setIsBackendAvailable(response.success);
      } catch (err) {
        setIsBackendAvailable(false);
        console.warn('Python backend not available:', err);
      }
    };

    checkBackendHealth();
  }, []);

  // Set authentication token from Supabase session
  const setAuthFromSession = useCallback(async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.access_token) {
        pythonBackendServices.setAuthToken(session.access_token);
        return true;
      }
      return false;
    } catch (err) {
      console.error('Failed to get session:', err);
      return false;
    }
  }, []);

  // ============================================================================
  // USER OPERATIONS
  // ============================================================================

  const createUser = useCallback(async (user: Omit<User, 'created_at'>) => {
    if (!isBackendAvailable) {
      return null;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const hasAuth = await setAuthFromSession();
      if (!hasAuth) {
        throw new Error('Not authenticated');
      }

      // For now, fall back to Supabase for user creation
      // User creation handled by Supabase auth
      const { data, error } = await supabase
        .from('users')
        .insert(user)
        .select()
        .single();

      if (error) throw error;
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create user');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [isBackendAvailable, setAuthFromSession]);

  const getUser = useCallback(async (id: string) => {
    if (!isBackendAvailable) {
      return null;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const hasAuth = await setAuthFromSession();
      if (!hasAuth) {
        throw new Error('Not authenticated');
      }

      const response = await pythonBackendServices.getCurrentUser();
      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to fetch user');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch user');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [isBackendAvailable, setAuthFromSession]);

  // ============================================================================
  // PROJECT OPERATIONS
  // ============================================================================

  const createProject = useCallback(async (project: Omit<Project, 'created_at'>) => {
    if (!isBackendAvailable) {
      return null;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const hasAuth = await setAuthFromSession();
      if (!hasAuth) {
        throw new Error('Not authenticated');
      }

      const response = await pythonBackendServices.createProject(project);
      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to create project');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [isBackendAvailable, setAuthFromSession]);

  const getProjects = useCallback(async () => {
    if (!isBackendAvailable) {
      return [];
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const hasAuth = await setAuthFromSession();
      if (!hasAuth) {
        throw new Error('Not authenticated');
      }

      const response = await pythonBackendServices.getProjects();
      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to fetch projects');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch projects');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [isBackendAvailable, setAuthFromSession]);

  const getProjectsForUser = useCallback(async (userId: string) => {
    if (!isBackendAvailable) {
      return [];
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const hasAuth = await setAuthFromSession();
      if (!hasAuth) {
        throw new Error('Not authenticated');
      }

      const response = await pythonBackendServices.getProjects();
      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to fetch user projects');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch user projects');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [isBackendAvailable, setAuthFromSession]);

  // ============================================================================
  // CHAT SESSION OPERATIONS
  // ============================================================================

  const createChatSession = useCallback(async (session: Omit<ChatSession, 'started_at'>) => {
    if (!isBackendAvailable) {
      return null;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const hasAuth = await setAuthFromSession();
      if (!hasAuth) {
        throw new Error('Not authenticated');
      }

      // Chat sessions handled by Supabase
      const { data, error } = await supabase
        .from('chat_sessions')
        .insert(session)
        .select()
        .single();

      if (error) throw error;
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create chat session');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [isBackendAvailable, setAuthFromSession]);

  const updateChatSession = useCallback(async (sessionId: string, updates: Partial<ChatSession>) => {
    if (!isBackendAvailable) {
      return null;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const hasAuth = await setAuthFromSession();
      if (!hasAuth) {
        throw new Error('Not authenticated');
      }

      // Chat sessions handled by Supabase
      const { data, error } = await supabase
        .from('chat_sessions')
        .update(updates)
        .eq('id', sessionId)
        .select()
        .single();

      if (error) throw error;
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update chat session');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [isBackendAvailable, setAuthFromSession]);

  const getChatSessions = useCallback(async (userId?: string, projectId?: string) => {
    if (!isBackendAvailable) {
      return [];
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const hasAuth = await setAuthFromSession();
      if (!hasAuth) {
        throw new Error('Not authenticated');
      }

      // Chat sessions handled by Supabase
      let query = supabase.from('chat_sessions').select('*');
      
      if (userId) query = query.eq('user_id', userId);
      if (projectId) query = query.eq('project_id', projectId);
      
      const { data, error } = await query.order('started_at', { ascending: false });
      if (error) throw error;
      
      return data || [];
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch chat sessions');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [isBackendAvailable, setAuthFromSession]);

  // ============================================================================
  // DOCUMENT OPERATIONS
  // ============================================================================

  const createDocument = useCallback(async (document: Omit<Document, 'created_at'>) => {
    if (!isBackendAvailable) {
      return null;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const hasAuth = await setAuthFromSession();
      if (!hasAuth) {
        throw new Error('Not authenticated');
      }

      const response = await pythonBackendServices.createDocument(document);
      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to create document');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create document');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [isBackendAvailable, setAuthFromSession]);

  const getDocuments = useCallback(async (projectId?: string) => {
    if (!isBackendAvailable) {
      return [];
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const hasAuth = await setAuthFromSession();
      if (!hasAuth) {
        throw new Error('Not authenticated');
      }

      const response = await pythonBackendServices.getProjectDocuments(projectId || '');
      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to fetch documents');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch documents');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [isBackendAvailable, setAuthFromSession]);

  // ============================================================================
  // ATTENDEE OPERATIONS
  // ============================================================================

  const sendBotToMeeting = useCallback(async (options: {
    meeting_url: string;
    bot_name?: string;
    bot_chat_message?: string;
  }) => {
    if (!isBackendAvailable) {
      throw new Error('Python backend not available');
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const hasAuth = await setAuthFromSession();
      if (!hasAuth) {
        throw new Error('Not authenticated');
      }

      const response = await pythonBackendServices.sendBotToMeeting({
        meeting_url: options.meeting_url,
        meeting_time: new Date().toISOString(),
        project_id: '', // Project ID will be set by the backend
        bot_config: {
          name: options.bot_name,
          chat_message: options.bot_chat_message
        },
        recording_enabled: true,
        transcript_enabled: true
      });

      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to send bot to meeting');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send bot to meeting');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [isBackendAvailable, setAuthFromSession]);

  // ============================================================================
  // AI OPERATIONS
  // ============================================================================

  const processProjectOnboarding = useCallback(async (payload: {
    project_id: string;
    user_id: string;
    summary: {
      project_name: string;
      overview: string;
      keywords: string[];
      deliverables: string;
      contacts: {
        internal_lead: string;
        agency_lead: string;
        client_lead: string;
      };
      shoot_date: string;
      location: string;
      references: string;
    };
  }) => {
    if (!isBackendAvailable) {
      throw new Error('Python backend not available');
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const hasAuth = await setAuthFromSession();
      if (!hasAuth) {
        throw new Error('Not authenticated');
      }

      const response = await pythonBackendServices.processProjectOnboarding(payload);
      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to process project onboarding');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process project onboarding');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [isBackendAvailable, setAuthFromSession]);

  // ============================================================================
  // UTILITY OPERATIONS
  // ============================================================================

  const setUsername = useCallback(async (username: string) => {
    if (!isBackendAvailable) {
      throw new Error('Python backend not available');
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const hasAuth = await setAuthFromSession();
      if (!hasAuth) {
        throw new Error('Not authenticated');
      }

      const response = await pythonBackendServices.setUsername(username);
      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to set username');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set username');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [isBackendAvailable, setAuthFromSession]);

  const checkBackendHealth = useCallback(async () => {
    try {
      const response = await pythonBackendServices.checkHealth();
      setIsBackendAvailable(response.success);
      return response.success;
    } catch (err) {
      setIsBackendAvailable(false);
      return false;
    }
  }, []);

  return {
    // State
    isLoading,
    error,
    isBackendAvailable,
    
    // Actions
    clearError,
    setAuthFromSession,
    checkBackendHealth,
    
    // User operations
    createUser,
    getUser,
    
    // Project operations
    createProject,
    getProjects,
    getProjectsForUser,
    
    // Chat session operations
    createChatSession,
    updateChatSession,
    getChatSessions,
    
    // Document operations
    createDocument,
    getDocuments,
    
    // Attendee operations
    sendBotToMeeting,
    
    // AI operations
    processProjectOnboarding,
    
    // Utility operations
    setUsername,
  };
};
