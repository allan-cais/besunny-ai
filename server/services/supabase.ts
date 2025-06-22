import { createClient } from '@supabase/supabase-js';

interface ChatMessage {
  id: string;
  sessionId: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
}

class SupabaseService {
  private client: any;

  constructor() {
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_ANON_KEY;
    
    if (supabaseUrl && supabaseKey) {
      this.client = createClient(supabaseUrl, supabaseKey);
    } else {
      console.warn('Supabase credentials not found. Message storage will be disabled.');
      this.client = null;
    }
  }

  async saveMessages(messages: ChatMessage[]): Promise<void> {
    if (!this.client) {
      console.log('Supabase not configured, skipping message storage:', messages);
      return;
    }

    try {
      const { error } = await this.client
        .from('chat_messages')
        .insert(messages);

      if (error) {
        console.error('Error saving messages to Supabase:', error);
        throw error;
      }

      console.log(`Successfully saved ${messages.length} messages to Supabase`);
    } catch (error) {
      console.error('Failed to save messages to Supabase:', error);
      throw error;
    }
  }

  async getMessagesBySession(sessionId: string, limit: number = 50): Promise<ChatMessage[]> {
    if (!this.client) {
      console.log('Supabase not configured, returning empty message history');
      return [];
    }

    try {
      const { data, error } = await this.client
        .from('chat_messages')
        .select('*')
        .eq('sessionId', sessionId)
        .order('createdAt', { ascending: true })
        .limit(limit);

      if (error) {
        console.error('Error fetching messages from Supabase:', error);
        throw error;
      }

      return data || [];
    } catch (error) {
      console.error('Failed to fetch messages from Supabase:', error);
      return [];
    }
  }

  async createSession(sessionId: string, metadata?: any): Promise<void> {
    if (!this.client) {
      console.log('Supabase not configured, skipping session creation');
      return;
    }

    try {
      const { error } = await this.client
        .from('chat_sessions')
        .insert({
          id: sessionId,
          metadata: metadata || {},
          createdAt: new Date().toISOString(),
        });

      if (error) {
        console.error('Error creating session in Supabase:', error);
        throw error;
      }

      console.log(`Successfully created session ${sessionId} in Supabase`);
    } catch (error) {
      console.error('Failed to create session in Supabase:', error);
      throw error;
    }
  }

  isConfigured(): boolean {
    return this.client !== null;
  }
}

export default new SupabaseService(); 