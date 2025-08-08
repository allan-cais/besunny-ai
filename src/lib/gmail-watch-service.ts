import { supabase } from './supabase';

export interface GmailWatchStatus {
  isActive: boolean;
  expiration?: string;
  historyId?: string;
}

export interface VirtualEmailDetection {
  id: string;
  virtual_email: string;
  username: string;
  email_type: 'to' | 'cc';
  gmail_message_id: string;
  document_id?: string;
  detected_at: string;
}

export const gmailWatchService = {
  // Set up Gmail watch for a user
  async setupGmailWatch(userEmail: string): Promise<{ success: boolean; error?: string }> {
    try {

      const session = (await supabase.auth.getSession()).data.session;
      if (!session) throw new Error('Not authenticated');

      const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/setup-gmail-watch`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ userEmail }),
      });

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Failed to setup Gmail watch');
      }

      return { success: true };
    } catch (error) {
      console.error('Error setting up Gmail watch:', error);
      return { success: false, error: error.message || 'Failed to setup Gmail watch' };
    }
  },

  // Get Gmail watch status for a user
  async getGmailWatchStatus(userEmail: string): Promise<GmailWatchStatus> {
    try {

      const { data, error } = await supabase
        .from('gmail_watches')
        .select('is_active, expiration, history_id')
        .eq('user_email', userEmail)
        .single();

      if (error) {
        // Handle 406 error (table not accessible) or other RLS issues
        if (error.code === '406' || error.message?.includes('Not Acceptable')) {
          return { isActive: false };
        }
        throw error;
      }

      if (!data) {
        return { isActive: false };
      }

      return {
        isActive: data.is_active,
        expiration: data.expiration,
        historyId: data.history_id,
      };
    } catch (error) {
      console.error('Error getting Gmail watch status:', error);
      return { isActive: false };
    }
  },

  // Get virtual email detections for a user
  async getVirtualEmailDetections(limit: number = 50): Promise<VirtualEmailDetection[]> {
    try {
      const { data, error } = await supabase
        .from('virtual_email_detections')
        .select('*')
        .order('detected_at', { ascending: false })
        .limit(limit);

      if (error) throw error;
      return data || [];
    } catch (error) {
      console.error('Error getting virtual email detections:', error);
      return [];
    }
  },

  // Get user's virtual email address
  async getUserVirtualEmail(): Promise<string | null> {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return null;

      const { data, error } = await supabase
        .from('users')
        .select('username')
        .eq('id', user.id)
        .single();

      if (error || !data?.username) return null;

      return `ai+${data.username}@besunny.ai`;
    } catch (error) {
      console.error('Error getting user virtual email:', error);
      return null;
    }
  },

  // Test virtual email detection by polling Gmail
  async testVirtualEmailDetection(): Promise<{ success: boolean; error?: string }> {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user?.email) {
        return { success: false, error: 'No user email found' };
      }

      const session = (await supabase.auth.getSession()).data.session;
      if (!session) throw new Error('Not authenticated');

      // Poll Gmail for new messages
      const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/gmail-polling-service`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ userEmail: user.email }),
      });

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Failed to poll Gmail');
      }

      return { 
        success: true,
        message: `Polled ${result.processed} messages, found ${result.detections} virtual emails${result.skipped ? ' (skipped due to recent webhook)' : ''}`
      };
    } catch (error) {
      console.error('Error testing virtual email detection:', error);
      return { success: false, error: error.message || 'Failed to test virtual email detection' };
    }
  },

  // Renew Gmail watch (called when watch is about to expire)
  async renewGmailWatch(userEmail: string): Promise<{ success: boolean; error?: string }> {
    try {
      // First, stop the current watch
      const { data: currentWatch, error: watchError } = await supabase
        .from('gmail_watches')
        .select('*')
        .eq('user_email', userEmail)
        .single();

      // Handle RLS access issues gracefully
      if (watchError) {
        if (watchError.code === '406' || watchError.message?.includes('Not Acceptable')) {
          // If we can't access the table, just try to set up a new watch
          return await this.setupGmailWatch(userEmail);
        }
        throw watchError;
      }

      if (currentWatch?.is_active) {
        // Stop the current watch (this would require a separate function)
        const { error: updateError } = await supabase
          .from('gmail_watches')
          .update({ is_active: false })
          .eq('user_email', userEmail);
        
        if (updateError && updateError.code !== '406') {
          throw updateError;
        }
      }

      // Set up a new watch
      return await this.setupGmailWatch(userEmail);
    } catch (error) {
      console.error('Error renewing Gmail watch:', error);
      return { success: false, error: error.message || 'Failed to renew Gmail watch' };
    }
  },

  // Get statistics about virtual email usage
  async getVirtualEmailStats(): Promise<{
    totalDetections: number;
    recentDetections: number;
    byType: { to: number; cc: number };
  }> {
    try {
      const { data: detections, error } = await supabase
        .from('virtual_email_detections')
        .select('email_type, detected_at');

      if (error) throw error;

      const now = new Date();
      const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

      const totalDetections = detections?.length || 0;
      const recentDetections = detections?.filter(d => 
        new Date(d.detected_at) > oneWeekAgo
      ).length || 0;

      const byType = {
        to: detections?.filter(d => d.email_type === 'to').length || 0,
        cc: detections?.filter(d => d.email_type === 'cc').length || 0,
      };

      return {
        totalDetections,
        recentDetections,
        byType,
      };
    } catch (error) {
      console.error('Error getting virtual email stats:', error);
      return {
        totalDetections: 0,
        recentDetections: 0,
        byType: { to: 0, cc: 0 },
      };
    }
  },
}; 