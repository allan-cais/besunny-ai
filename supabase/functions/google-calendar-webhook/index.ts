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

// Handle deleted calendar event
async function handleDeletedEvent(eventId: string, userId: string): Promise<{ success: boolean; error?: string }> {
  try {
    console.log('Handling deleted event in webhook:', eventId, 'for user:', userId);
    
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
      console.log('=== WEBHOOK NOTIFICATION RECEIVED ===');
      console.log('Timestamp:', new Date().toISOString());
      console.log('URL:', req.url);
      console.log('Headers:', Object.fromEntries(req.headers.entries()));
      
      // Try to parse body as JSON (for test/manual sync requests)
      let body: any = null;
      try {
        body = await req.json();
        console.log('Body:', JSON.stringify(body, null, 2));
      } catch (parseError) {
        console.log('No JSON body found - this is likely a real Google Calendar webhook');
        // For real Google Calendar webhooks, the body is empty and info is in headers
      }
      
      // Check if this is an internal function call (test/sync) or real Google webhook
      const authHeader = req.headers.get('Authorization');
      const isInternalCall = body && (body.state === 'test' || body.state === 'sync');
      
      // For internal calls, validate the service role key
      if (isInternalCall) {
        console.log('Internal function call detected');
        if (!authHeader) {
          console.log('Missing authorization header for internal call');
          return withCORS(new Response(JSON.stringify({ error: 'Missing authorization header' }), { status: 401 }));
        }
        
        const expectedToken = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        if (authHeader !== `Bearer ${expectedToken}`) {
          console.log('Invalid authorization token for internal call');
          return withCORS(new Response(JSON.stringify({ error: 'Invalid authorization token' }), { status: 401 }));
        }
        
        console.log('Internal call authorization validated');
      } else {
        console.log('Real Google Calendar webhook detected - skipping internal auth check');
      }
      
      // Handle different notification types
      if (body && body.state === 'sync') {
        console.log('Processing MANUAL sync request');
        // This is a manual sync request (not a real webhook)
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
          `timeMin=${new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()}&timeMax=${new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString()}&singleEvents=true&orderBy=startTime`,
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
            sync_range_start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
            sync_range_end: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString(),
          });
        
        // Update webhook record (updated_at will be automatically updated by trigger)
        await supabase
          .from('calendar_webhooks')
          .update({ is_active: true })
          .eq('user_id', userId);
        
        console.log(`Manual sync completed: ${processed} processed, ${created} created, ${updated} updated`);
        
        return withCORS(new Response(JSON.stringify({
          ok: true,
          processed,
          created,
          updated,
          errors,
        }), { status: 200 }));
        
      } else if (body && body.state === 'test') {
        console.log('Processing TEST webhook notification');
        // This is a test webhook notification
        const userId = body.userId;
        
        if (!userId) {
          return withCORS(new Response(JSON.stringify({ error: 'Missing userId' }), { status: 400 }));
        }
        
        console.log('Test webhook received for user:', userId);
        
        // Log the test webhook
        await supabase
          .from('calendar_sync_logs')
          .insert({
            user_id: userId,
            sync_type: 'webhook_test',
            status: 'completed',
            events_processed: 0,
            meetings_created: 0,
            meetings_updated: 0,
            notes: 'Test webhook notification received successfully',
          });
        
        return withCORS(new Response(JSON.stringify({
          ok: true,
          message: 'Test webhook received successfully',
          timestamp: new Date().toISOString(),
        }), { status: 200 }));
        
      } else {
        // Handle real Google Calendar webhook notifications
        // Real Google Calendar webhooks have empty bodies and info in headers
        console.log('=== REAL GOOGLE CALENDAR WEBHOOK NOTIFICATION RECEIVED ===');
        console.log('Headers:', Object.fromEntries(req.headers.entries()));
        console.log('Body:', body);
        
        // Extract user ID from webhook URL params or headers
        let userId = url.searchParams.get('userId');
          
        // If not in URL, try to extract from webhook body or headers
        if (!userId) {
          // Check for X-Goog-Resource-URI header which might contain user info
          const resourceUri = req.headers.get('X-Goog-Resource-URI');
          if (resourceUri) {
            console.log('Resource URI from header:', resourceUri);
          }
          
          // Check for X-Goog-Channel-ID header
          const channelId = req.headers.get('X-Goog-Channel-ID');
          if (channelId) {
            console.log('Channel ID from header:', channelId);
            // Try to find user by channel ID in database
            const { data: webhook } = await supabase
              .from('calendar_webhooks')
              .select('user_id')
              .eq('webhook_id', channelId)
              .eq('is_active', true)
              .single();
            
            if (webhook) {
              userId = webhook.user_id;
              console.log('Found user ID from channel ID:', userId);
            }
          }
        }
        
        if (!userId) {
          console.error('Could not determine userId from webhook notification');
          // Log this as a failed webhook for debugging
          await supabase
            .from('calendar_sync_logs')
            .insert({
              user_id: null,
              sync_type: 'webhook',
              status: 'failed',
              error_message: 'Could not determine userId from webhook notification',
              events_processed: 0,
            });
          
          return withCORS(new Response(JSON.stringify({ 
            ok: true, 
            message: 'Webhook received but userId not found' 
          }), { status: 200 }));
        }
        
        console.log('Processing real Google Calendar webhook notification for user:', userId);
        
        // Get user's Google credentials
        const credentials = await getGoogleCredentials(userId);
        
        // Get current webhook info to check if we have a sync token
        const { data: webhook } = await supabase
          .from('calendar_webhooks')
          .select('sync_token')
          .eq('user_id', userId)
          .eq('google_calendar_id', 'primary')
          .eq('is_active', true)
          .single();
        
        let syncResult;
        
        if (webhook?.sync_token) {
            // Try incremental sync first
            console.log('Attempting incremental sync with sync token');
            try {
              const response = await fetch(
                `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
                `syncToken=${webhook.sync_token}&singleEvents=true&showDeleted=true`,
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
                
                console.log(`Incremental sync found ${events.length} events, nextSyncToken: ${nextSyncToken}`);
                
                let processed = 0;
                let created = 0;
                let updated = 0;
                let deleted = 0;
                
                // Process events
                for (const event of events) {
                  // Check if event is deleted/cancelled
                  if (event.status === 'cancelled' || event.deleted) {
                    console.log('Processing deleted event in webhook:', event.id);
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
                
                // Update sync token and webhook activity in database
                await supabase
                  .from('calendar_webhooks')
                  .update({ 
                    sync_token: nextSyncToken,
                    last_webhook_received: new Date().toISOString()
                  })
                  .eq('user_id', userId);
                
                // Log the incremental sync
                await supabase
                  .from('calendar_sync_logs')
                  .insert({
                    user_id: userId,
                    sync_type: 'incremental',
                    status: 'completed',
                    events_processed: processed,
                    meetings_created: created,
                    meetings_updated: updated,
                    meetings_deleted: deleted,
                  });
                
                syncResult = { processed, created, updated, deleted };
              } else if (response.status === 410) {
                // Sync token is invalid, need to do full sync
                console.log('Sync token invalid (410), performing full sync');
                throw new Error('Sync token invalid');
              } else {
                const errorText = await response.text();
                throw new Error(`Calendar API error: ${response.status} - ${errorText}`);
              }
            } catch (error) {
              console.log('Incremental sync failed, falling back to full sync:', error.message);
              // Fall back to full sync
            }
          }
          
          // If incremental sync failed or no sync token, do full sync
          if (!syncResult) {
            console.log('Performing full sync for webhook notification');
            
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
              console.error('Calendar API error:', calendarResponse.status, errorText);
              throw new Error(`Calendar API error: ${calendarResponse.status} - ${errorText}`);
            }
            
            const calendarData = await calendarResponse.json();
            const events = calendarData.items || [];
            const nextSyncToken = calendarData.nextSyncToken;
            
            console.log(`Full sync found ${events.length} events, nextSyncToken: ${nextSyncToken}`);
            
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
            
            // Update sync token and webhook activity in database
            await supabase
              .from('calendar_webhooks')
              .update({ 
                sync_token: nextSyncToken,
                last_webhook_received: new Date().toISOString()
              })
              .eq('user_id', userId);
            
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
                sync_range_start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
                sync_range_end: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString(),
              });
            
            syncResult = { processed, created, updated, errors };
          }
          
          console.log(`Real webhook sync completed:`, syncResult);
          
          return withCORS(new Response(JSON.stringify({
            ok: true,
            ...syncResult,
          }), { status: 200 }));
      }
    } catch (error) {
      console.error('Webhook processing error:', error);
      
      // Log the error for debugging
      try {
        await supabase
          .from('calendar_sync_logs')
          .insert({
            user_id: null,
            sync_type: 'webhook',
            status: 'failed',
            error_message: error.message || String(error),
            events_processed: 0,
          });
      } catch (logError) {
        console.error('Failed to log webhook error:', logError);
      }
      
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
      const webhookUrl = `${Deno.env.get('SUPABASE_URL')}/functions/v1/google-calendar-webhook/notify?userId=${userId}`;
      
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