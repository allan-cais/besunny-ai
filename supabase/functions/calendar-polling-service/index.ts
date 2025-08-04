import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

// Initialize Supabase client
const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const supabase = createClient(supabaseUrl, supabaseServiceKey);

async function getGoogleCredentials(userId: string): Promise<any> {
  const { data, error } = await supabase
    .from('google_credentials')
    .select('*')
    .eq('user_id', userId)
    .maybeSingle();
  
  if (error || !data) {
    throw new Error('Google credentials not found');
  }
  
  // Check if token is expired and refresh if needed
  if (new Date(data.expires_at) <= new Date()) {
    if (!data.refresh_token) {
      throw new Error('Token expired and no refresh token available');
    }
    
    // Refresh the token
    const refreshResponse = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        client_id: Deno.env.get('GOOGLE_CLIENT_ID')!,
        client_secret: Deno.env.get('GOOGLE_CLIENT_SECRET')!,
        refresh_token: data.refresh_token,
        grant_type: 'refresh_token',
      }),
    });
    
    if (!refreshResponse.ok) {
      throw new Error('Failed to refresh Google token');
    }
    
    const refreshData = await refreshResponse.json();
    
    // Update the credentials in the database
    const { error: updateError } = await supabase
      .from('google_credentials')
      .update({
        access_token: refreshData.access_token,
        expires_at: new Date(Date.now() + refreshData.expires_in * 1000).toISOString(),
      })
      .eq('user_id', userId);
    
    if (updateError) {
      throw new Error('Failed to update refreshed token');
    }
    
    return {
      ...data,
      access_token: refreshData.access_token,
      expires_at: new Date(Date.now() + refreshData.expires_in * 1000).toISOString(),
    };
  }
  
  return data;
}

// Handle deleted calendar event
async function handleDeletedEvent(eventId: string, userId: string): Promise<{ success: boolean; error?: string }> {
  try {
    console.log('Handling deleted event in polling:', eventId, 'for user:', userId);
    
    // Find the meeting in our database
    const { data: meetings, error: findError } = await supabase
      .from('meetings')
      .select('id, title, bot_status, project_id, transcript, attendee_bot_id')
      .eq('google_calendar_event_id', eventId)
      .eq('user_id', userId);
    
    if (findError) {
      console.error('Error finding meeting for deletion:', findError);
      return { success: false, error: findError.message };
    }
    
    if (!meetings || meetings.length === 0) {
      console.log('No meeting found for deleted event:', eventId);
      return { success: true }; // Event not in our database, nothing to delete
    }
    
    // If multiple meetings found, handle each one individually
    if (meetings.length > 1) {
      console.log(`Found ${meetings.length} duplicate meetings for event ${eventId}, processing individually`);
    }
    
    let deleted = 0;
    let cancelled = 0;
    
    for (const meeting of meetings) {
      // Check if the meeting has important data that should be preserved
      const hasImportantData = 
        meeting.bot_status && meeting.bot_status !== 'pending' || // Has active bot
        meeting.project_id || // Assigned to project
        meeting.transcript || // Has transcript
        meeting.attendee_bot_id; // Has bot ID
      
      if (hasImportantData) {
        // Meeting has important data, mark as cancelled instead of deleting
        const { error: updateError } = await supabase
          .from('meetings')
          .update({
            event_status: 'declined',
            bot_status: meeting.bot_status === 'pending' ? 'failed' : meeting.bot_status,
            updated_at: new Date().toISOString()
          })
          .eq('id', meeting.id);
        
        if (!updateError) {
          cancelled++;
        } else {
          console.error('Error updating cancelled meeting:', updateError);
        }
      } else {
        // No important data, safe to delete
        const { error: deleteError } = await supabase
          .from('meetings')
          .delete()
          .eq('id', meeting.id);
        
        if (!deleteError) {
          deleted++;
        } else {
          console.error('Error deleting meeting:', deleteError);
        }
      }
    }
    
    console.log(`Successfully processed ${meetings.length} meetings for deleted event ${eventId}: ${deleted} deleted, ${cancelled} cancelled`);
    return { success: true };
  } catch (error) {
    console.error('Error handling deleted event:', error);
    return { success: false, error: error.message || String(error) };
  }
}

function extractMeetingUrl(event: any): string | null {
  if (!event.description) return null;
  
  // Look for common meeting URL patterns
  const urlPatterns = [
    /https?:\/\/(meet\.google\.com\/[a-z-]+)/i,
    /https?:\/\/(teams\.microsoft\.com\/l\/meetup-join\/[^\\s]+)/i,
    /https?:\/\/(zoom\.us\/j\/\d+)/i,
    /https?:\/\/(us02web\.zoom\.us\/j\/\d+)/i,
    /https?:\/\/(discord\.gg\/[a-zA-Z0-9]+)/i,
    /https?:\/\/(discord\.com\/invite\/[a-zA-Z0-9]+)/i,
  ];
  
  for (const pattern of urlPatterns) {
    const match = event.description.match(pattern);
    if (match) {
      return match[0];
    }
  }
  
  return null;
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').trim();
}

async function processCalendarEvent(event: any, userId: string, credentials: any): Promise<{ action: string; meetingId?: string }> {
  try {
    // Skip events without start time
    if (!event.start) {
      return { action: 'skipped_no_start_time' };
    }
    
    // Skip all-day events
    if (event.start.date) {
      return { action: 'skipped_all_day' };
    }
    
    // Extract meeting URL
    const meetingUrl = extractMeetingUrl(event);
    
    // Skip events without meeting URLs (for bot functionality)
    if (!meetingUrl) {
      return { action: 'skipped_no_meeting_url' };
    }
    
    // Check if meeting already exists
    const { data: existingMeeting, error: findError } = await supabase
      .from('meetings')
      .select('id, title, start_time, end_time, meeting_url, bot_status')
      .eq('google_calendar_event_id', event.id)
      .eq('user_id', userId)
      .maybeSingle();
    
    if (findError) {
      console.error('Error finding existing meeting:', findError);
      return { action: 'error_find_failed' };
    }
    
    // Prepare meeting data
    const startTime = new Date(event.start.dateTime);
    const endTime = event.end?.dateTime ? new Date(event.end.dateTime) : new Date(startTime.getTime() + 60 * 60 * 1000);
    
    const meetingData = {
      title: event.summary || 'Untitled Meeting',
      description: event.description ? stripHtml(event.description) : null,
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString(),
      meeting_url: meetingUrl,
      google_calendar_event_id: event.id,
      user_id: userId,
      bot_status: 'pending',
      updated_at: new Date().toISOString(),
    };
    
    if (existingMeeting) {
      // Check if meeting needs update
      const needsUpdate = 
        existingMeeting.title !== meetingData.title ||
        existingMeeting.start_time !== meetingData.start_time ||
        existingMeeting.end_time !== meetingData.end_time ||
        existingMeeting.meeting_url !== meetingData.meeting_url;
      
      if (needsUpdate) {
        const { error: updateError } = await supabase
          .from('meetings')
          .update(meetingData)
          .eq('id', existingMeeting.id);
        
        if (updateError) {
          console.error('Error updating meeting:', updateError);
          return { action: 'error_update_failed' };
        }
        
        console.log(`Updated meeting: ${meetingData.title}`);
        return { action: 'updated', meetingId: existingMeeting.id };
      } else {
        return { action: 'no_change' };
      }
    } else {
      // Create new meeting
      const { data: newMeeting, error: insertError } = await supabase
        .from('meetings')
        .insert(meetingData)
        .select('id')
        .single();
      
      if (insertError) {
        console.error('Error creating meeting:', insertError);
        return { action: 'error_create_failed' };
      }
      
      console.log(`Created new meeting: ${meetingData.title}`);
      return { action: 'created', meetingId: newMeeting.id };
    }
  } catch (error) {
    console.error('Error processing calendar event:', error);
    return { action: 'error_processing_failed' };
  }
}

// Smart calendar polling with webhook activity check
async function pollCalendarForUser(userId: string): Promise<{ processed: number; created: number; updated: number; deleted: number; skipped: boolean }> {
  try {
    // Get current calendar watch status
    const { data: watchStatus } = await supabase
      .from('calendar_webhooks')
      .select('sync_token, last_webhook_received, is_active')
      .eq('user_id', userId)
      .eq('google_calendar_id', 'primary')
      .eq('is_active', true)
      .single();
    
    if (!watchStatus) {
      console.log(`No active calendar watch found for user ${userId}`);
      return { processed: 0, created: 0, updated: 0, deleted: 0, skipped: true };
    }
    
    // Smart polling: Skip if webhook was received recently (within 6 hours)
    if (watchStatus.last_webhook_received) {
      const lastWebhookTime = new Date(watchStatus.last_webhook_received);
      const sixHoursAgo = new Date(Date.now() - 6 * 60 * 60 * 1000);
      
      if (lastWebhookTime > sixHoursAgo) {
        console.log(`Skipping polling for user ${userId} - webhook received recently at ${lastWebhookTime.toISOString()}`);
        return { processed: 0, created: 0, updated: 0, deleted: 0, skipped: true };
      }
    }
    
    // Get Google credentials
    const credentials = await getGoogleCredentials(userId);
    
    let processed = 0;
    let created = 0;
    let updated = 0;
    let deleted = 0;
    
    // Try incremental sync first if we have a sync token
    if (watchStatus.sync_token) {
      try {
        console.log(`Attempting incremental sync for user ${userId} with sync token`);
        
        const response = await fetch(
          `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
          `syncToken=${watchStatus.sync_token}&singleEvents=true&showDeleted=true`,
          {
            headers: {
              'Authorization': `Bearer ${credentials.access_token}`,
            },
          }
        );
        
        if (response.ok) {
          const calendarData = await response.json();
          const events = calendarData.items || [];
          const nextSyncToken = calendarData.nextSyncToken;
          
          console.log(`Incremental sync found ${events.length} events for user ${userId}`);
          
          // Process events
          for (const event of events) {
            // Check if event is deleted/cancelled
            if (event.status === 'cancelled' || event.deleted) {
              const deleteResult = await handleDeletedEvent(event.id, userId);
              if (deleteResult.success) {
                deleted++;
              }
              processed++;
            } else {
              const result = await processCalendarEvent(event, userId, credentials);
              processed++;
              
              if (result.action === 'created') {
                created++;
              } else if (result.action === 'updated') {
                updated++;
              } else if (result.action === 'deleted') {
                deleted++;
              }
            }
          }
          
          // Update sync token in database
          await supabase
            .from('calendar_webhooks')
            .update({ 
              sync_token: nextSyncToken,
              last_poll_at: new Date().toISOString()
            })
            .eq('user_id', userId);
          
          console.log(`Incremental sync completed for user ${userId}: ${processed} processed, ${created} created, ${updated} updated, ${deleted} deleted`);
          
          return { processed, created, updated, deleted, skipped: false };
        } else if (response.status === 410) {
          // Sync token is invalid, need to do full sync
          console.log(`Sync token invalid (410) for user ${userId}, performing full sync`);
        } else {
          const errorText = await response.text();
          throw new Error(`Calendar API error: ${response.status} - ${errorText}`);
        }
      } catch (error) {
        console.log(`Incremental sync failed for user ${userId}, falling back to full sync:`, error.message);
        // Fall back to full sync
      }
    }
    
    // Perform full sync
    console.log(`Performing full sync for user ${userId}`);
    
    const calendarResponse = await fetch(
      `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
      `timeMin=${new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()}&timeMax=${new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString()}&singleEvents=true&orderBy=startTime`,
      {
        headers: {
          'Authorization': `Bearer ${credentials.access_token}`,
        },
      }
    );
    
    if (!calendarResponse.ok) {
      const errorText = await calendarResponse.text();
      throw new Error(`Calendar API error: ${calendarResponse.status} - ${errorText}`);
    }
    
    const calendarData = await calendarResponse.json();
    const events = calendarData.items || [];
    const nextSyncToken = calendarData.nextSyncToken;
    
    console.log(`Full sync found ${events.length} events for user ${userId}`);
    
    // Process each event
    for (const event of events) {
      try {
        const result = await processCalendarEvent(event, userId, credentials);
        processed++;
        
        if (result.action === 'created') {
          created++;
        } else if (result.action === 'updated') {
          updated++;
        } else if (result.action === 'deleted') {
          deleted++;
        }
      } catch (error) {
        console.error('Error processing event:', error);
      }
    }
    
    // Update sync token in database
    await supabase
      .from('calendar_webhooks')
      .update({ 
        sync_token: nextSyncToken,
        last_poll_at: new Date().toISOString()
      })
      .eq('user_id', userId);
    
    console.log(`Full sync completed for user ${userId}: ${processed} processed, ${created} created, ${updated} updated, ${deleted} deleted`);
    
    return { processed, created, updated, deleted, skipped: false };
  } catch (error) {
    console.error(`Error polling calendar for user ${userId}:`, error);
    return { processed: 0, created: 0, updated: 0, deleted: 0, skipped: false };
  }
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    // Only allow POST
    if (req.method !== 'POST') {
      return new Response('Method not allowed', { status: 405, headers: corsHeaders });
    }

    const { userId } = await req.json();
    
    if (!userId) {
      return new Response(JSON.stringify({ error: 'Missing userId' }), { 
        status: 400, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      });
    }

    console.log(`Starting calendar polling for user: ${userId}`);

    const result = await pollCalendarForUser(userId);

    console.log(`Calendar polling completed for user ${userId}:`, result);

    return new Response(JSON.stringify({
      success: true,
      message: `Calendar polling completed for user ${userId}`,
      ...result,
    }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Calendar polling service error:', error);
    return new Response(JSON.stringify({ 
      error: error.message || 'Failed to run calendar polling service' 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
}); 