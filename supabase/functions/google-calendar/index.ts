import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';

const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

function withCORS(resp: Response) {
  resp.headers.set('Access-Control-Allow-Origin', '*');
  resp.headers.set('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  resp.headers.set('Access-Control-Allow-Headers', 'authorization, x-client-info, apikey, content-type');
  return resp;
}

function getUserIdFromAuth(req: Request): string | null {
  const auth = req.headers.get('Authorization');
  if (!auth || !auth.startsWith('Bearer ')) return null;
  const jwt = auth.replace('Bearer ', '');
  const payload = JSON.parse(atob(jwt.split('.')[1]));
  return payload.sub || null;
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

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return withCORS(new Response('ok', { status: 200 }));
  }

  const url = new URL(req.url);
  const method = req.method;
  const userId = getUserIdFromAuth(req);
  
  if (!userId) {
    return withCORS(new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 }));
  }

  // Fetch calendar events (GET /events)
  if (url.pathname.endsWith('/events') && method === 'GET') {
    try {
      const credentials = await getGoogleCredentials(userId);
      const projectId = url.searchParams.get('project_id');
      
      // Get events from the next 7 days
      const now = new Date();
      const nextWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
      
      const calendarResponse = await fetch(
        `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
        `timeMin=${now.toISOString()}&timeMax=${nextWeek.toISOString()}&singleEvents=true&orderBy=startTime`,
        {
          headers: {
            'Authorization': `Bearer ${credentials.access_token}`,
          },
        }
      );
      
      if (!calendarResponse.ok) {
        const errorBody = await calendarResponse.text();
        const errorMsg = `Calendar API error: ${calendarResponse.status}`;
        return withCORS(new Response(JSON.stringify({
          ok: false,
          error: errorMsg,
          google_error: errorBody
        }), { status: 500 }));
      }
      
      const calendarData = await calendarResponse.json();
      const events = calendarData.items || [];
      
      // Process events and extract meeting URLs
      const meetings = [];
      
      for (const event of events) {
        const meetingUrl = extractMeetingUrl(event);
        
        if (meetingUrl) {
          const meeting = {
            user_id: userId,
            project_id: projectId,
            google_calendar_event_id: event.id,
            title: event.summary || 'Untitled Meeting',
            description: event.description || '',
            meeting_url: meetingUrl,
            start_time: event.start.dateTime || event.start.date,
            end_time: event.end.dateTime || event.end.date,
            status: 'pending',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };
          
          // Check if meeting already exists
          const { data: existingMeeting } = await supabase
            .from('meetings')
            .select('id')
            .eq('google_calendar_event_id', event.id)
            .eq('user_id', userId)
            .maybeSingle();
          
          if (!existingMeeting) {
            // Insert new meeting
            const { data: insertedMeeting, error: insertError } = await supabase
              .from('meetings')
              .insert(meeting)
              .select()
              .single();
            
            if (insertError) {
              // No logging
            } else {
              meetings.push(insertedMeeting);
            }
          } else {
            // Update existing meeting
            const { data: updatedMeeting, error: updateError } = await supabase
              .from('meetings')
              .update({
                title: meeting.title,
                description: meeting.description,
                start_time: meeting.start_time,
                end_time: meeting.end_time,
                meeting_url: meeting.meeting_url,
                updated_at: new Date().toISOString(),
              })
              .eq('id', existingMeeting.id)
              .select()
              .single();
            
            if (updateError) {
              // No logging
            } else {
              meetings.push(updatedMeeting);
            }
          }
        }
      }
      
      return withCORS(new Response(JSON.stringify({
        ok: true,
        meetings,
        total_events: events.length,
        meetings_with_urls: meetings.length,
      }), { status: 200 }));
      
    } catch (e) {
      return withCORS(new Response(JSON.stringify({
        ok: false,
        error: e.message || String(e),
      }), { status: 500 }));
    }
  }

  // Get meetings for a project (GET /meetings?project_id=...)
  if (url.pathname.endsWith('/meetings') && method === 'GET') {
    try {
      const projectId = url.searchParams.get('project_id');
      
      let query = supabase
        .from('meetings')
        .select('*')
        .eq('user_id', userId)
        .gte('start_time', new Date().toISOString())
        .order('start_time', { ascending: true });
      
      if (projectId) {
        query = query.eq('project_id', projectId);
      }
      
      const { data: meetings, error } = await query;
      
      if (error) {
        throw error;
      }
      
      return withCORS(new Response(JSON.stringify({
        ok: true,
        meetings: meetings || [],
      }), { status: 200 }));
      
    } catch (e) {
      return withCORS(new Response(JSON.stringify({
        ok: false,
        error: e.message,
      }), { status: 500 }));
    }
  }

  return withCORS(new Response(JSON.stringify({ error: 'Not found' }), { status: 404 }));
}); 