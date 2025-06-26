import { useState, useEffect, useCallback } from 'react';
import { 
  supabaseService, 
  ChatMessage, 
  ChatSession, 
  User, 
  Project, 
  Document,
  KnowledgeSpace,
  DocumentChunk,
  Tag,
  Summary,
  Receipt,
  AgentLog
} from '../lib/supabase';

export const useSupabase = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // User operations
  const createUser = useCallback(async (user: Omit<User, 'created_at'>) => {
    if (!supabaseService.isConfigured()) {
      console.warn('Supabase not configured');
      return null;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const newUser = await supabaseService.createUser(user);
      return newUser;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create user');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getUser = useCallback(async (id: string) => {
    if (!supabaseService.isConfigured()) {
      console.warn('Supabase not configured');
      return null;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const user = await supabaseService.getUser(id);
      return user;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch user');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Project operations
  const createProject = useCallback(async (project: Omit<Project, 'created_at'>) => {
    if (!supabaseService.isConfigured()) {
      console.warn('Supabase not configured');
      return null;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const newProject = await supabaseService.createProject(project);
      return newProject;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getProjects = useCallback(async () => {
    if (!supabaseService.isConfigured()) {
      console.warn('Supabase not configured');
      return [];
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const projects = await supabaseService.getProjects();
      return projects;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch projects');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getProjectsForUser = useCallback(async (userId: string) => {
    if (!supabaseService.isConfigured()) {
      console.warn('Supabase not configured');
      return [];
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const projects = await supabaseService.getProjectsForUser(userId);
      return projects;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch user projects');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Chat session operations
  const createChatSession = useCallback(async (session: Omit<ChatSession, 'started_at'>) => {
    if (!supabaseService.isConfigured()) {
      console.warn('Supabase not configured');
      return null;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const newSession = await supabaseService.createChatSession(session);
      return newSession;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create chat session');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getChatSessions = useCallback(async (userId?: string, projectId?: string) => {
    if (!supabaseService.isConfigured()) {
      console.warn('Supabase not configured');
      return [];
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const sessions = await supabaseService.getChatSessions(userId, projectId);
      return sessions;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch chat sessions');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  const endChatSession = useCallback(async (sessionId: string) => {
    if (!supabaseService.isConfigured()) {
      console.warn('Supabase not configured');
      return;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      await supabaseService.endChatSession(sessionId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to end chat session');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Chat message operations
  const saveMessages = useCallback(async (messages: Omit<ChatMessage, 'created_at'>[]) => {
    if (!supabaseService.isConfigured()) {
      console.warn('Supabase not configured');
      return;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      await supabaseService.saveMessages(messages);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save messages');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getMessagesBySession = useCallback(async (sessionId: string, limit: number = 50) => {
    if (!supabaseService.isConfigured()) {
      console.warn('Supabase not configured');
      return [];
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const messages = await supabaseService.getMessagesBySession(sessionId, limit);
      return messages;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch messages');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Document operations
  const createDocument = useCallback(async (document: Omit<Document, 'created_at'>) => {
    if (!supabaseService.isConfigured()) {
      console.warn('Supabase not configured');
      return null;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const newDocument = await supabaseService.createDocument(document);
      return newDocument;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create document');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getDocuments = useCallback(async (projectId: string) => {
    if (!supabaseService.isConfigured()) {
      console.warn('Supabase not configured');
      return [];
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const documents = await supabaseService.getDocuments(projectId);
      return documents;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch documents');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    isLoading,
    error,
    clearError,
    
    // User operations
    createUser,
    getUser,
    
    // Project operations
    createProject,
    getProjects,
    getProjectsForUser,
    
    // Chat session operations
    createChatSession,
    getChatSessions,
    endChatSession,
    
    // Chat message operations
    saveMessages,
    getMessagesBySession,
    
    // Document operations
    createDocument,
    getDocuments,
    
    isConfigured: supabaseService.isConfigured(),
  };
};

// Hook for real-time subscriptions to messages
export const useSupabaseSubscription = (sessionId: string, callback: (payload: any) => void) => {
  useEffect(() => {
    if (!supabaseService.isConfigured() || !sessionId) {
      return;
    }

    const subscription = supabaseService.subscribeToMessages(sessionId, callback);

    return () => {
      subscription.unsubscribe();
    };
  }, [sessionId, callback]);
};

// Hook for real-time subscriptions to sessions
export const useSupabaseSessionSubscription = (userId: string, callback: (payload: any) => void) => {
  useEffect(() => {
    if (!supabaseService.isConfigured() || !userId) {
      return;
    }

    const subscription = supabaseService.subscribeToSessions(userId, callback);

    return () => {
      subscription.unsubscribe();
    };
  }, [userId, callback]);
}; 