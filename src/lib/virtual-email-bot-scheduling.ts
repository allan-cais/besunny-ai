import { supabase } from './supabase';
import { apiKeyService } from './api-keys';

export interface VirtualEmailBotScheduling {
  // Check if a meeting has virtual email attendees
  checkForVirtualEmailAttendees(meetingId: string): Promise<{
    hasVirtualEmail: boolean;
    virtualEmailAddress?: string;
    username?: string;
  }>;
  
  // Auto-schedule bot for meetings with virtual email attendees
  autoScheduleBotForVirtualEmail(meetingId: string): Promise<{
    success: boolean;
    botId?: string;
    error?: string;
  }>;
  
  // Get user's virtual email address
  getUserVirtualEmail(userId: string): Promise<string>;
  
  // Process incoming calendar events for virtual email attendees
  processCalendarEventForVirtualEmail(eventData: any): Promise<{
    processed: boolean;
    meetingId?: string;
    autoScheduled?: boolean;
  }>;
}

export const virtualEmailBotScheduling: VirtualEmailBotScheduling = {
  
  async checkForVirtualEmailAttendees(meetingId: string) {
    try {
      const { data: meeting, error } = await supabase
        .from('meetings')
        .select('*')
        .eq('id', meetingId)
        .single();
      
      if (error || !meeting) {
        throw new Error('Meeting not found');
      }
      
      // For now, we'll check if the meeting was created via virtual email
      // In a full implementation, you'd parse the calendar event attendees
      const hasVirtualEmail = meeting.auto_scheduled_via_email || false;
      const virtualEmailAddress = meeting.virtual_email_attendee;
      
      // Extract username from virtual email if present
      let username: string | undefined;
      if (virtualEmailAddress && virtualEmailAddress.includes('+')) {
        const match = virtualEmailAddress.match(/inbound\+([^@]+)@sunny\.ai/);
        username = match ? match[1] : undefined;
      }
      
      return {
        hasVirtualEmail,
        virtualEmailAddress,
        username
      };
    } catch (error) {
      console.error('Error checking for virtual email attendees:', error);
      return { hasVirtualEmail: false };
    }
  },
  
  async autoScheduleBotForVirtualEmail(meetingId: string) {
    try {
      // Get meeting details
      const { data: meeting, error } = await supabase
        .from('meetings')
        .select('*')
        .eq('id', meetingId)
        .single();
      
      if (error || !meeting) {
        throw new Error('Meeting not found');
      }
      
      if (!meeting.meeting_url) {
        throw new Error('Meeting has no URL');
      }
      
      // Use default configuration for auto-scheduled bots
      const defaultConfig = {
        bot_name: 'Sunny AI Assistant',
        bot_chat_message: {
          to: 'everyone',
          message: 'Hi, I\'m here to transcribe this meeting!',
        },
        // Note: transcription_settings.language is not supported by Attendee API
        // Language will use API defaults
        auto_join: true,
        recording_enabled: true
      };
      
      // Send bot to meeting
      const result = await apiKeyService.sendBotToMeeting(meeting.meeting_url, defaultConfig);
      
      // Update meeting with bot details and enable polling
      await supabase
        .from('meetings')
        .update({
          attendee_bot_id: result.id || result.bot_id,
          bot_status: 'bot_scheduled',
          bot_deployment_method: 'automatic',
          bot_configuration: defaultConfig,
          // polling_enabled field removed
          updated_at: new Date().toISOString()
        })
        .eq('id', meetingId);
      
      return {
        success: true,
        botId: result.id || result.bot_id
      };
    } catch (error) {
      console.error('Error auto-scheduling bot:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },
  
  async getUserVirtualEmail(userId: string) {
    try {
      // Get user's username from the users table
      const { data: user, error } = await supabase
        .from('users')
        .select('username')
        .eq('id', userId)
        .single();
      
      if (error || !user?.username) {
        throw new Error('User not found or username not set');
      }
      
      // Create virtual email using the username from the users table
      return `ai+${user.username}@besunny.ai`;
    } catch (error) {
      console.error('Error getting user virtual email:', error);
      throw error;
    }
  },
  
  async processCalendarEventForVirtualEmail(eventData: any) {
    try {
      // Check if event has virtual email attendees
      const attendees = eventData.attendees || [];
      const virtualEmailPattern = /ai\+([^@]+)@besunny\.ai/;
      
      let virtualEmailAttendee: string | undefined;
      let username: string | undefined;
      
      for (const attendee of attendees) {
        if (virtualEmailPattern.test(attendee.email)) {
          virtualEmailAttendee = attendee.email;
          const match = attendee.email.match(virtualEmailPattern);
          username = match ? match[1] : undefined;
          break;
        }
      }
      
      if (!virtualEmailAttendee || !username) {
        return { processed: false };
      }
      
      // Find the user by username
      const { data: user, error: userError } = await supabase
        .from('users')
        .select('id')
        .ilike('email', `%${username}%`)
        .single();
      
      if (userError || !user) {
        console.error('User not found for virtual email:', virtualEmailAttendee);
        return { processed: false };
      }
      
      // Check if meeting already exists
      const { data: existingMeeting } = await supabase
        .from('meetings')
        .select('id')
        .eq('google_calendar_event_id', eventData.id)
        .eq('user_id', user.id)
        .single();
      
      if (existingMeeting) {
        // Update existing meeting to mark it for auto-scheduling
        await supabase
          .from('meetings')
          .update({
            auto_scheduled_via_email: true,
            virtual_email_attendee: virtualEmailAttendee,
            bot_deployment_method: 'scheduled',
            updated_at: new Date().toISOString()
          })
          .eq('id', existingMeeting.id);
        
        return {
          processed: true,
          meetingId: existingMeeting.id,
          autoScheduled: false // Already exists, just marked for scheduling
        };
      }
      
      // Create new meeting with auto-scheduling flag
      const { data: newMeeting, error: meetingError } = await supabase
        .from('meetings')
        .insert({
          user_id: user.id,
          google_calendar_event_id: eventData.id,
          title: eventData.summary || 'Untitled Meeting',
          description: eventData.description,
          meeting_url: eventData.hangoutLink || eventData.conferenceData?.entryPoints?.[0]?.uri,
          start_time: eventData.start?.dateTime || eventData.start?.date,
          end_time: eventData.end?.dateTime || eventData.end?.date,
          event_status: 'accepted',
          bot_status: 'pending',
          auto_scheduled_via_email: true,
          virtual_email_attendee: virtualEmailAttendee,
          bot_deployment_method: 'scheduled',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })
        .select()
        .single();
      
      if (meetingError) {
        throw meetingError;
      }
      
      return {
        processed: true,
        meetingId: newMeeting.id,
        autoScheduled: true
      };
    } catch (error) {
      console.error('Error processing calendar event for virtual email:', error);
      return { processed: false };
    }
  }
}; 