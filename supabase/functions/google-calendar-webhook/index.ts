import { serve } from 'std/http/server.ts';
import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

function withCORS(resp: Response) {
  resp.headers.set('Access-Control-Allow-Origin', '*');
  resp.headers.set('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  resp.headers.set('Access-Control-Allow-Headers', 'authorization, x-client-info, apikey, content-type');
  return resp;
}

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

function extractMeetingUrl(event: any): string | null {
  // Check for Google Meet URL in conferenceData
  if (event.conferenceData?.entryPoints) {
    const meetEntry = event.conferenceData.entryPoints.find(
      (entry: any) => entry.entryPointType === 'video'
    );
    if (meetEntry?.uri) {
      return meetEntry.uri;
    }
  }
  
  // Check for Google Meet URL in description
  if (event.description) {
    const meetRegex = /https:\/\/meet\.google\.com\/[a-z-]+/i;
    const match = event.description.match(meetRegex);
    if (match) {
      return match[0];
    }
  }
  
  // Check for other video conferencing URLs
  const videoUrls = [
    /https:\/\/zoom\.us\/j\/\d+/i,
    /https:\/\/teams\.microsoft\.com\/l\/meetup-join\/[^\\s]+/i,
    /https:\/\/meet\.google\.com\/[a-z-]+/i,
  ];
  
  if (event.description) {
    for (const regex of videoUrls) {
      const match = event.description.match(regex);
      if (match) {
        return match[0];
      }
    }
  }
  
  return null;
}

function stripHtml(html: string): string {
  if (!html) return '';
  const tmp = html.replace(/<[^>]+>/g, ' ');
  return tmp.replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/\s+/g, ' ').trim();
}

async function processCalendarEvent(event: any, userId: string, credentials: any): Promise<{ action: string; meetingId?: string }> {
  const meetingUrl = extractMeetingUrl(event);
  
  if (!meetingUrl) {
    return { action: 'skipped_no_url' };
  }
  
  // Determine attendee status
  let attendeeStatus = 'needsAction';
  if (Array.isArray(event.attendees)) {
    const selfAttendee = event.attendees.find((a: any) => a.self);
    if (selfAttendee && selfAttendee.responseStatus) {
      attendeeStatus = selfAttendee.responseStatus;
    }
  } else if (event.creator && event.creator.email === credentials.google_email) {
    attendeeStatus = 'accepted';
  }
  
  const meeting = {
    user_id: userId,
    google_calendar_event_id: event.id,
    title: event.summary || 'Untitled Meeting',
    description: stripHtml(event.description || ''),
    meeting_url: meetingUrl,
    start_time: event.start.dateTime || event.start.date,
    end_time: event.end.dateTime || event.end.date,
    event_status: attendeeStatus,
    bot_status: 'pending',
    updated_at: new Date().toISOString(),
  };
  
  // Check if meeting already exists
  const { data: existingMeeting } = await supabase
    .from('meetings')
    .select('id, bot_status, attendee_bot_id')
    .eq('google_calendar_event_id', event.id)
    .eq('user_id', userId)
    .maybeSingle();
  
  if (!existingMeeting) {
    // Insert new meeting
    const { data: insertedMeeting, error: insertError } = await supabase
      .from('meetings')
      .insert({
        ...meeting,
        created_at: new Date().toISOString(),
      })
      .select()
      .single();
    
    if (insertError) {
      console.error('Failed to insert meeting:', insertError);
      return { action: 'error_insert' };
    }
    
    return { action: 'created', meetingId: insertedMeeting.id };
  } else {
    // Update existing meeting, but preserve bot_status and attendee_bot_id
    const { data: updatedMeeting, error: updateError } = await supabase
      .from('meetings')
      .update({
        ...meeting,
        bot_status: existingMeeting.bot_status,
        attendee_bot_id: existingMeeting.attendee_bot_id,
      })
      .eq('id', existingMeeting.id)
      .select()
      .single();
    
    if (updateError) {
      console.error('Failed to update meeting:', updateError);
      return { action: 'error_update' };
    }
    
    return { action: 'updated', meetingId: updatedMeeting.id };
  }
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return withCORS(new Response('ok', { status: 200 }));
  }

  const url = new URL(req.url);
  const method = req.method;

  // Webhook verification endpoint (GET /verify)
  if (url.pathname.endsWith('/verify') && method === 'GET') {
    const challenge = url.searchParams.get('challenge');
    if (challenge) {
      return withCORS(new Response(challenge, { status: 200 }));
    }
    return withCORS(new Response('No challenge provided', { status: 400 }));
  }

  // Webhook notification endpoint (POST /notify)
  if (url.pathname.endsWith('/notify') && method === 'POST') {
    try {
      const body = await req.json();
      
      // Handle different notification types
      if (body.state === 'sync') {
        // This is a sync notification - process the changed events
        const userId = body.userId;
        const resourceId = body.resourceId;
        
        if (!userId || !resourceId) {
          return withCORS(new Response(JSON.stringify({ error: 'Missing userId or resourceId' }), { status: 400 }));
        }
        
        // Get user's Google credentials
        const credentials = await getGoogleCredentials(userId);
        
        // Get the changed events from Google Calendar
        const calendarResponse = await fetch(
          `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
          `timeMin=${new Date().toISOString()}&singleEvents=true&orderBy=startTime`,
          {
            headers: {
              'Authorization': `Bearer ${credentials.access_token}`,
            },
          }
        );
        
        if (!calendarResponse.ok) {
          throw new Error(`Calendar API error: ${calendarResponse.status}`);
        }
        
        const calendarData = await calendarResponse.json();
        const events = calendarData.items || [];
        
        let processed = 0;
        let created = 0;
        let updated = 0;
        let errors = 0;
        
        // Process each event
        for (const event of events) {
          try {
            const result = await processCalendarEvent(event, userId, credentials);
            processed++;
            
            if (result.action === 'created') {
              created++;
            } else if (result.action === 'updated') {
              updated++;
            } else if (result.action.startsWith('error')) {
              errors++;
            }
          } catch (error) {
            console.error('Error processing event:', error);
            errors++;
          }
        }
        
        // Log the sync operation
        await supabase
          .from('calendar_sync_logs')
          .insert({
            user_id: userId,
            sync_type: 'webhook',
            status: 'completed',
            events_processed: processed,
            meetings_created: created,
            meetings_updated: updated,
            sync_range_start: new Date().toISOString(),
            sync_range_end: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
          });
        
        // Update last_sync_at in webhook record
        await supabase
          .from('calendar_webhooks')
          .update({ last_sync_at: new Date().toISOString() })
          .eq('user_id', userId);
        
        return withCORS(new Response(JSON.stringify({
          ok: true,
          processed,
          created,
          updated,
          errors,
        }), { status: 200 }));
        
      } else {
        // Handle other notification types (calendar list changes, etc.)
        return withCORS(new Response(JSON.stringify({ ok: true, message: 'Notification received' }), { status: 200 }));
      }
      
    } catch (error) {
      console.error('Webhook processing error:', error);
      return withCORS(new Response(JSON.stringify({
        ok: false,
        error: error.message || String(error),
      }), { status: 500 }));
    }
  }

  // Setup webhook subscription (POST /setup)
  if (url.pathname.endsWith('/setup') && method === 'POST') {
    try {
      const { userId } = await req.json();
      
      if (!userId) {
        return withCORS(new Response(JSON.stringify({ error: 'Missing userId' }), { status: 400 }));
      }
      
      const credentials = await getGoogleCredentials(userId);
      const webhookUrl = `${Deno.env.get('SUPABASE_URL')}/functions/v1/google-calendar-webhook/notify`;
      
      // Set up the webhook subscription
      const webhookResponse = await fetch(
        'https://www.googleapis.com/calendar/v3/calendars/primary/events/watch',
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${credentials.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            id: `calendar-webhook-${userId}-${Date.now()}`,
            type: 'web_hook',
            address: webhookUrl,
            params: {
              userId: userId,
            },
            expiration: Date.now() + (7 * 24 * 60 * 60 * 1000), // 7 days in ms
          }),
        }
      );
      
      if (!webhookResponse.ok) {
        const errorText = await webhookResponse.text();
        throw new Error(`Failed to setup webhook: ${webhookResponse.status} - ${errorText}`);
      }
      
      const webhookData = await webhookResponse.json();
      

      
      // Validate expiration value
      if (!webhookData.expiration) {
        throw new Error('No expiration value received from Google API');
      }
      
      // Convert expiration to proper date
      let expirationDate: Date;
      try {
        if (typeof webhookData.expiration === 'number') {
          expirationDate = new Date(webhookData.expiration);
        } else if (typeof webhookData.expiration === 'string') {
          expirationDate = new Date(parseInt(webhookData.expiration));
        } else {
          throw new Error(`Unexpected expiration type: ${typeof webhookData.expiration}`);
        }
        
        if (isNaN(expirationDate.getTime())) {
          throw new Error(`Invalid expiration value: ${webhookData.expiration}`);
        }
      } catch (dateError) {
        console.error('Date parsing error:', dateError);
        throw new Error(`Failed to parse expiration date: ${dateError.message}`);
      }
      
      // Store webhook info in database
      await supabase
        .from('calendar_webhooks')
        .upsert({
          user_id: userId,
          google_calendar_id: 'primary',
          webhook_id: webhookData.id,
          resource_id: webhookData.resourceId,
          expiration_time: expirationDate.toISOString(),
          is_active: true,
        }, {
          onConflict: 'user_id,google_calendar_id',
        });
      
      return withCORS(new Response(JSON.stringify({
        ok: true,
        webhook_id: webhookData.id,
        resource_id: webhookData.resourceId,
        expiration: webhookData.expiration,
      }), { status: 200 }));
      
    } catch (error) {
      console.error('Webhook setup error:', error);
      return withCORS(new Response(JSON.stringify({
        ok: false,
        error: error.message || String(error),
      }), { status: 500 }));
    }
  }

  return withCORS(new Response(JSON.stringify({ error: 'Not found' }), { status: 404 }));
}); 