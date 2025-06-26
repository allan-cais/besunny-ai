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
  created_at: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  project_id: string;
  chunk_index?: number;
  text?: string;
  embedding_id?: string;
  metadata?: any;
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
  alerts?: any;
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
  output?: any;
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

  // Real-time subscriptions
  subscribeToMessages(sessionId: string, callback: (payload: any) => void) {
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

  subscribeToSessions(userId: string, callback: (payload: any) => void) {
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
  }
}; 