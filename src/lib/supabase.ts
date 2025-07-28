import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('Supabase environment variables are not configured. Please check your .env file.');
}

export const supabase = createClient(
  supabaseUrl || '',
  supabaseAnonKey || ''
);

// Database types for the master schema
export interface User {
  id: string;
  email: string;
  name?: string;
  role?: string;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  status?: string;
  created_by?: string;
  created_at: string;
}

export interface KnowledgeSpace {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  created_at: string;
}

export interface Document {
  id: string;
  project_id: string;
  knowledge_space_id?: string;
  source?: string;
  source_id?: string;
  title?: string;
  summary?: string;
  author?: string;
  received_at?: string;
  file_url?: string;
  status?: 'active' | 'updated' | 'deleted' | 'error';
  file_id?: string; // Google Drive file ID
  last_synced_at?: string;
  watch_active?: boolean;
  created_at: string;
  type?: 'email' | 'document' | 'spreadsheet' | 'presentation' | 'image' | 'folder' | 'meeting_transcript';
  file_size?: string;
  transcript_duration_seconds?: number;
  transcript_metadata?: any;
  meeting_id?: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  project_id: string;
  chunk_index?: number;
  text?: string;
  embedding_id?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface Tag {
  id: string;
  name?: string;
  type?: string;
  created_at: string;
}

export interface DocumentTag {
  id: string;
  document_id: string;
  tag_id: string;
  applied_by?: string;
  created_at: string;
}

export interface Summary {
  id: string;
  project_id: string;
  date?: string;
  summary?: string;
  alerts?: Record<string, unknown>;
  references?: string[];
  created_by?: string;
  created_at: string;
}

export interface Receipt {
  id: string;
  project_id: string;
  vendor?: string;
  amount?: number;
  date?: string;
  category?: string;
  receipt_image_url?: string;
  document_id?: string;
  created_at: string;
}

export interface ChatSession {
  id: string;
  user_id?: string;
  project_id?: string;
  started_at: string;
  ended_at?: string;
  name?: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role?: string;
  message?: string;
  used_chunks?: string[];
  created_at: string;
}

export interface AgentLog {
  id: string;
  agent_name?: string;
  input_id?: string;
  input_type?: string;
  output?: Record<string, unknown>;
  confidence?: number;
  notes?: string;
  created_at: string;
}

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
      console.error('Error creating user:', error);
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
      console.error('Error fetching user:', error);
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
      console.error('Error creating project:', error);
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
      console.error('Error fetching projects:', error);
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
      console.error('Error fetching projects for user:', error);
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
      console.error('Error updating project:', error);
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
      console.error('Error deleting project:', error);
      console.error('Error details:', {
        message: error.message,
        details: error.details,
        hint: error.hint,
        code: error.code
      });
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
      console.error('Error creating chat session:', error);
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
      console.error('Error fetching chat sessions:', error);
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
      console.error('Error ending chat session:', error);
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
      console.error('Error updating chat session:', error);
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
      console.error('Error saving messages:', error);
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
      console.error('Error fetching messages:', error);
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
      console.error('Error creating document:', error);
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
      console.error('Error fetching documents:', error);
      throw error;
    }

    return data || [];
  },

  // Google Drive File Watch operations
  async subscribeToDriveFile(userId: string, documentId: string, fileId: string): Promise<{ success: boolean; message: string; watch_id?: string }> {
    const { data, error } = await supabase.functions.invoke('subscribe-to-drive-file', {
      body: {
        user_id: userId,
        document_id: documentId,
        file_id: fileId,
      },
    });

    if (error) {
      console.error('Error subscribing to drive file:', error);
      throw error;
    }

    return data;
  },

  async updateDocument(documentId: string, updates: Partial<Document>): Promise<Document> {
    const { data, error } = await supabase
      .from('documents')
      .update(updates)
      .eq('id', documentId)
      .select()
      .single();

    if (error) {
      console.error('Error updating document:', error);
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
  }): Promise<{ success: boolean; message: string; metadata?: any; error?: string }> {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session?.access_token) {
        throw new Error('No active session');
      }

      const response = await fetch(`${supabaseUrl}/functions/v1/project-onboarding-ai`, {
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
      console.error('Error processing project onboarding:', error);
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
}