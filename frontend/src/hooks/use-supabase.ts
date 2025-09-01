import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../lib/supabase';
import type { User, Project, Document } from '../types';

// Simple hook for basic Supabase operations
export const useSupabase = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // User operations
  const createUser = useCallback(async (user: Omit<User, 'created_at'>) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const { data, error: apiError } = await supabase
        .from('users')
        .insert(user)
        .select()
        .single();
      
      if (apiError) throw apiError;
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create user');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getUser = useCallback(async (id: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const { data, error: apiError } = await supabase
        .from('users')
        .select('*')
        .eq('id', id)
        .single();
      
      if (apiError) throw apiError;
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch user');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Project operations
  const createProject = useCallback(async (project: Omit<Project, 'created_at'>) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const { data, error: apiError } = await supabase
        .from('projects')
        .insert(project)
        .select()
        .single();
      
      if (apiError) throw apiError;
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getProjects = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const { data, error: apiError } = await supabase
        .from('projects')
        .select('*')
        .order('created_at', { ascending: false });
      
      if (apiError) throw apiError;
      return data || [];
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch projects');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getProjectsForUser = useCallback(async (userId: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const { data, error: apiError } = await supabase
        .from('projects')
        .select('*')
        .eq('created_by', userId)
        .order('created_at', { ascending: false });
      
      if (apiError) throw apiError;
      return data || [];
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch user projects');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateProject = useCallback(async (projectId: string, updates: Partial<Project>) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const { data, error: apiError } = await supabase
        .from('projects')
        .update(updates)
        .eq('id', projectId)
        .select()
        .single();
      
      if (apiError) throw apiError;
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update project');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteProject = useCallback(async (projectId: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const { error: apiError } = await supabase
        .from('projects')
        .delete()
        .eq('id', projectId);
      
      if (apiError) throw apiError;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete project');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Document operations
  const createDocument = useCallback(async (document: Omit<Document, 'created_at'>) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const { data, error: apiError } = await supabase
        .from('documents')
        .insert(document)
        .select()
        .single();
      
      if (apiError) throw apiError;
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create document');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getDocuments = useCallback(async (projectId: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const { data, error: apiError } = await supabase
        .from('documents')
        .select('*')
        .eq('project_id', projectId)
        .order('created_at', { ascending: false });
      
      if (apiError) throw apiError;
      return data || [];
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch documents');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateDocument = useCallback(async (documentId: string, updates: Partial<Document>) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const { data, error: apiError } = await supabase
        .from('documents')
        .update(updates)
        .eq('id', documentId)
        .select()
        .single();
      
      if (apiError) throw apiError;
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update document');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteDocument = useCallback(async (documentId: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const { error: apiError } = await supabase
        .from('documents')
        .delete()
        .eq('id', documentId);
      
      if (apiError) throw apiError;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document');
      throw err;
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
    updateProject,
    deleteProject,
    
    // Document operations
    createDocument,
    getDocuments,
    updateDocument,
    deleteDocument,
    
    // Configuration check
    isConfigured: true, // Supabase client is always configured if imported
  };
};

// Simple subscription hook
export const useSupabaseSubscription = (table: string, callback: (payload: any) => void) => {
  useEffect(() => {
    const subscription = supabase
      .channel(`table-db-changes:${table}`)
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table },
        callback
      )
      .subscribe();

    return () => {
      subscription.unsubscribe();
    };
  }, [table, callback]);
}; 