import { createClient } from '@supabase/supabase-js';
import type { User, Session } from '@supabase/supabase-js';
import config from '../config/environment';
import type { 
  Project, 
  Meeting, 
  Document, 
  ChatSession, 
  TranscriptMetadata,
  BotConfiguration,
  EntityPatterns,
  ClassificationSignals,
  ClassificationFeedback
} from '../types';

// Re-export ChatMessage type for components that need it
export type { ChatMessage } from '../types';

const supabaseUrl = config.supabase.url;
const supabaseAnonKey = config.supabase.anonKey;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Supabase environment variables not configured');
}

export const supabase = createClient(
  supabaseUrl || '',
  supabaseAnonKey || '',
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
      flowType: 'pkce'
    }
  }
);

// Database types are now imported from types/index.ts
// All interfaces are now imported from types/index.ts

// Helper functions for common operations
export const supabaseService = {
  // User operations
  async createUser(user: Omit<User, 'created_at'>): Promise<User> {
    const { data, error } = await supabase
      .from('users')
      .insert(user)
      .select()
      .single();

    if (error) {
      throw error;
    }

    return data;
  },

  async getUser(id: string): Promise<User | null> {
    const { data, error } = await supabase
      .from('users')
      .select('*')
      .eq('id', id)
      .single();

    if (error) {
      // Error fetching user
      return null;
    }

    return data;
  },

  // Project operations
  async createProject(project: Omit<Project, 'created_at'>): Promise<Project> {
    const { data, error } = await supabase
      .from('projects')
      .insert(project)
      .select()
      .single();

    if (error) {
      // Error creating project
      throw error;
    }

    return data;
  },

  async getProjects(): Promise<Project[]> {
    const { data, error } = await supabase
      .from('projects')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      // Error fetching projects
      throw error;
    }

    return data || [];
  },

  async getProjectsForUser(userId: string): Promise<Project[]> {
    const { data, error } = await supabase
      .from('projects')
      .select('*')
      .eq('created_by', userId)
      .order('created_at', { ascending: false });

    if (error) {
      // Error fetching projects for user
      throw error;
    }

    return data || [];
  },

  async updateProject(projectId: string, updates: Partial<Project>): Promise<Project> {
    const { data, error } = await supabase
      .from('projects')
      .update(updates)
      .eq('id', projectId)
      .select()
      .single();

    if (error) {
      // Error updating project
      throw error;
    }

    return data;
  },

  async deleteProject(projectId: string): Promise<void> {

    
    const { error } = await supabase
      .from('projects')
      .delete()
      .eq('id', projectId);

    if (error) {
      // Error deleting project
      throw error;
    }
    
    
  },

  // Chat session operations
  async createChatSession(session: Omit<ChatSession, 'started_at'>): Promise<ChatSession> {
    const { data, error } = await supabase
      .from('chat_sessions')
      .insert(session)
      .select()
      .single();

    if (error) {
      // Error creating chat session
      throw error;
    }

    return data;
  },

  async getChatSessions(userId?: string, projectId?: string): Promise<ChatSession[]> {
    let query = supabase
      .from('chat_sessions')
      .select('*')
      .order('started_at', { ascending: false });

    if (userId) {
      query = query.eq('user_id', userId);
    }
    if (projectId) {
      query = query.eq('project_id', projectId);
    }

    const { data, error } = await query;

    if (error) {
      // Error fetching chat sessions
      throw error;
    }

    return data || [];
  },

  async endChatSession(sessionId: string): Promise<void> {
    const { error } = await supabase
      .from('chat_sessions')
      .update({ ended_at: new Date().toISOString() })
      .eq('id', sessionId);

    if (error) {
      // Error ending chat session
      throw error;
    }
  },

  async updateChatSession(sessionId: string, updates: Partial<ChatSession>): Promise<ChatSession> {
    const { data, error } = await supabase
      .from('chat_sessions')
      .update(updates)
      .eq('id', sessionId)
      .select()
      .single();

    if (error) {
      // Error updating chat session
      throw error;
    }

    return data;
  },

  // Chat message operations
  async saveMessages(messages: Omit<ChatMessage, 'created_at'>[]): Promise<void> {
    const { error } = await supabase
      .from('chat_messages')
      .insert(messages);

    if (error) {
      // Error saving messages
      throw error;
    }
  },

  async getMessagesBySession(sessionId: string, limit: number = 50): Promise<ChatMessage[]> {
    const { data, error } = await supabase
      .from('chat_messages')
      .select('*')
      .eq('session_id', sessionId)
      .order('created_at', { ascending: true })
      .limit(limit);

    if (error) {
      // Error fetching messages
      throw error;
    }

    return data || [];
  },

  // Document operations
  async createDocument(document: Omit<Document, 'created_at'>): Promise<Document> {
    const { data, error } = await supabase
      .from('documents')
      .insert(document)
      .select()
      .single();

    if (error) {
      // Error creating document
      throw error;
    }

    return data;
  },

  async getDocuments(projectId: string): Promise<Document[]> {
    const { data, error } = await supabase
      .from('documents')
      .select('*')
      .eq('project_id', projectId)
      .order('created_at', { ascending: false });

    if (error) {
      // Error fetching documents
      throw error;
    }

    return data || [];
  },

  // Google Drive File Watch operations
  async subscribeToDriveFile(userId: string, documentId: string, fileId: string): Promise<{ success: boolean; message: string; watch_id?: string }> {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session?.access_token) {
        throw new Error('No active session');
      }

      const response = await fetch(`${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/drive-subscription/subscribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          file_id: fileId,
          document_id: documentId,
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      // Error subscribing to drive file
      throw error;
    }
  },

  async updateDocument(documentId: string, updates: Partial<Document>): Promise<Document> {
    const { data, error } = await supabase
      .from('documents')
      .update(updates)
      .eq('id', documentId)
      .select()
      .single();

    if (error) {
      // Error updating document
      throw error;
    }

    return data;
  },

  // Real-time subscriptions
  subscribeToMessages(sessionId: string, callback: (payload: Record<string, unknown>) => void) {
    return supabase
      .channel(`chat_messages:${sessionId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'chat_messages',
          filter: `session_id=eq.${sessionId}`,
        },
        callback
      )
      .subscribe();
  },

  subscribeToSessions(userId: string, callback: (payload: Record<string, unknown>) => void) {
    return supabase
      .channel(`chat_sessions:${userId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'chat_sessions',
          filter: `user_id=eq.${userId}`,
        },
        callback
      )
      .subscribe();
  },

  // Check if Supabase is configured
  isConfigured(): boolean {
    return !!(supabaseUrl && supabaseAnonKey);
  },

  async processProjectOnboarding(payload: {
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
  }): Promise<{ success: boolean; message: string; metadata?: Record<string, unknown>; error?: string }> {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session?.access_token) {
        throw new Error('No active session');
      }

      const response = await fetch(`${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/ai/projects/onboarding`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      // Error processing project onboarding
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
}