import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { User, Session } from '@supabase/supabase-js';
import config from '@/config/environment';

// Database types
export interface Database {
  public: {
    Tables: {
      users: {
        Row: {
          id: string;
          email: string;
          name: string | null;
          avatar_url: string | null;
          created_at: string;
          updated_at: string;
          metadata: Record<string, any> | null;
        };
        Insert: {
          id?: string;
          email: string;
          name?: string | null;
          avatar_url?: string | null;
          created_at?: string;
          updated_at?: string;
          metadata?: Record<string, any> | null;
        };
        Update: {
          id?: string;
          email?: string;
          name?: string | null;
          avatar_url?: string | null;
          created_at?: string;
          updated_at?: string;
          metadata?: Record<string, any> | null;
        };
      };
      projects: {
        Row: {
          id: string;
          name: string;
          description: string | null;
          status: 'active' | 'archived' | 'completed' | 'in_progress';
          created_at: string;
          updated_at: string;
          created_by: string;
          settings: Record<string, any> | null;
        };
        Insert: {
          id?: string;
          name: string;
          description?: string | null;
          status?: 'active' | 'archived' | 'completed' | 'in_progress';
          created_at?: string;
          updated_at?: string;
          created_by: string;
          settings?: Record<string, any> | null;
        };
        Update: {
          id?: string;
          name?: string;
          description?: string | null;
          status?: 'active' | 'archived' | 'completed' | 'in_progress';
          created_at?: string;
          updated_at?: string;
          created_by?: string;
          settings?: Record<string, any> | null;
        };
      };
      project_members: {
        Row: {
          id: string;
          user_id: string;
          project_id: string;
          role: 'owner' | 'admin' | 'member' | 'viewer';
          joined_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          project_id: string;
          role?: 'owner' | 'admin' | 'member' | 'viewer';
          joined_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          project_id?: string;
          role?: 'owner' | 'admin' | 'member' | 'viewer';
          joined_at?: string;
        };
      };
      documents: {
        Row: {
          id: string;
          name: string;
          type: 'pdf' | 'docx' | 'txt' | 'email' | 'meeting';
          content: string | null;
          metadata: Record<string, any> | null;
          project_id: string;
          created_at: string;
          updated_at: string;
          status: 'processing' | 'completed' | 'error';
          classification: Record<string, any> | null;
        };
        Insert: {
          id?: string;
          name: string;
          type: 'pdf' | 'docx' | 'txt' | 'email' | 'meeting';
          content?: string | null;
          metadata?: Record<string, any> | null;
          project_id: string;
          created_at?: string;
          updated_at?: string;
          status?: 'processing' | 'completed' | 'error';
          classification?: Record<string, any> | null;
        };
        Update: {
          id?: string;
          name?: string;
          type?: 'pdf' | 'docx' | 'txt' | 'email' | 'meeting';
          content?: string | null;
          metadata?: Record<string, any> | null;
          project_id?: string;
          created_at?: string;
          updated_at?: string;
          status?: 'processing' | 'completed' | 'error';
          classification?: Record<string, any> | null;
        };
      };
      meetings: {
        Row: {
          id: string;
          title: string;
          description: string | null;
          start_time: string;
          end_time: string;
          project_id: string | null;
          transcript: Record<string, any> | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          title: string;
          description?: string | null;
          start_time: string;
          end_time: string;
          project_id?: string | null;
          transcript?: Record<string, any> | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          title?: string;
          description?: string | null;
          start_time?: string;
          end_time?: string;
          project_id?: string | null;
          transcript?: Record<string, any> | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      emails: {
        Row: {
          id: string;
          subject: string;
          sender: string;
          recipients: string[];
          content: string;
          html_content: string | null;
          project_id: string | null;
          classification: Record<string, any> | null;
          created_at: string;
          read: boolean;
        };
        Insert: {
          id?: string;
          subject: string;
          sender: string;
          recipients: string[];
          content: string;
          html_content?: string | null;
          project_id?: string | null;
          classification?: Record<string, any> | null;
          created_at?: string;
          read?: boolean;
        };
        Update: {
          id?: string;
          subject?: string;
          sender?: string;
          recipients?: string[];
          content?: string;
          html_content?: string | null;
          project_id?: string | null;
          classification?: Record<string, any> | null;
          created_at?: string;
          read?: boolean;
        };
      };
      ai_classifications: {
        Row: {
          id: string;
          document_id: string;
          model: string;
          category: string;
          confidence: number;
          tags: string[];
          summary: string;
          entities: Record<string, any>[];
          metadata: Record<string, any> | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          document_id: string;
          model: string;
          category: string;
          confidence: number;
          tags: string[];
          summary: string;
          entities: Record<string, any>[];
          metadata?: Record<string, any> | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          document_id?: string;
          model?: string;
          category?: string;
          confidence?: number;
          tags?: string[];
          summary?: string;
          entities?: Record<string, any>[];
          metadata?: Record<string, any> | null;
          created_at?: string;
        };
      };
      google_integrations: {
        Row: {
          id: string;
          user_id: string;
          service: 'calendar' | 'drive' | 'gmail';
          access_token: string;
          refresh_token: string;
          expires_at: number;
          scopes: string[];
          is_active: boolean;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          service: 'calendar' | 'drive' | 'gmail';
          access_token: string;
          refresh_token: string;
          expires_at: number;
          scopes: string[];
          is_active?: boolean;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          service?: 'calendar' | 'drive' | 'gmail';
          access_token?: string;
          refresh_token?: string;
          expires_at?: number;
          scopes?: string[];
          is_active?: boolean;
          created_at?: string;
          updated_at?: string;
        };
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      [_ in never]: never;
    };
    Enums: {
      [_ in never]: never;
    };
  };
}

// Create Supabase client
export const supabase: SupabaseClient<Database> = createClient<Database>(
  config.supabaseUrl,
  config.supabaseAnonKey,
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
      flowType: 'pkce',
      storage: typeof window !== 'undefined' ? window.localStorage : undefined,
    },
    realtime: {
      params: {
        eventsPerSecond: 10,
      },
    },
    global: {
      headers: {
        'X-Client-Info': 'besunny-ai-frontend',
      },
    },
  }
);

// Export types
export type { User, Session };

// Utility functions
export const getSupabaseClient = () => supabase;

// Auth helpers
export const getCurrentUser = async (): Promise<User | null> => {
  const { data: { user } } = await supabase.auth.getUser();
  return user;
};

export const getCurrentSession = async (): Promise<Session | null> => {
  const { data: { session } } = await supabase.auth.getSession();
  return session;
};

// Database helpers
export const getTable = <T extends keyof Database['public']['Tables']>(
  table: T
) => {
  return supabase.from(table);
};

// Real-time subscription helpers
export const subscribeToChanges = <T extends keyof Database['public']['Tables']>(
  table: T,
  callback: (payload: any) => void
) => {
  return supabase.channel(`table-db-changes:${table}`).on(
    'postgres_changes',
    { event: '*', schema: 'public', table: table as string },
    callback
  ).subscribe();
};

// Error handling
export const handleSupabaseError = (error: any): string => {
  if (error?.message) {
    return error.message;
  }
  if (error?.error_description) {
    return error.error_description;
  }
  return 'An unexpected error occurred';
};

// Export default client
export default supabase;