// Test script using frontend authentication
import fetch from 'node-fetch';

const SUPABASE_URL = 'https://gkkmaeobxwvramtsjabu.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdra21hZW9ieHd2cmFtdHNqYWJ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMxMTg2MjEsImV4cCI6MjA2ODY5NDYyMX0.Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8';

async function testPollingWithAuth() {
  try {
    console.log('🧪 Testing polling with frontend authentication...\n');

    // First, let's check what meetings exist in the database
    console.log('1️⃣ Checking meetings in database...');
    
    const meetingsResponse = await fetch(`${SUPABASE_URL}/rest/v1/meetings?select=id,title,bot_status,attendee_bot_id,polling_enabled,last_polled_at,next_poll_at&attendee_bot_id=not.is.null&order=updated_at.desc`, {
      method: 'GET',
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        'Content-Type': 'application/json',
      },
    });

    if (!meetingsResponse.ok) {
      const errorText = await meetingsResponse.text();
      throw new Error(`Failed to get meetings: ${meetingsResponse.status} - ${errorText}`);
    }

    const meetings = await meetingsResponse.json();
    console.log('📋 Meetings with bots:', JSON.stringify(meetings, null, 2));

    if (meetings.length === 0) {
      console.log('ℹ️ No meetings with bots found');
      return;
    }

    // Check the polling status view
    console.log('\n2️⃣ Checking polling status view...');
    const pollingStatusResponse = await fetch(`${SUPABASE_URL}/rest/v1/polling_status?select=*`, {
      method: 'GET',
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        'Content-Type': 'application/json',
      },
    });

    if (pollingStatusResponse.ok) {
      const pollingStatus = await pollingStatusResponse.json();
      console.log('📊 Polling status:', JSON.stringify(pollingStatus, null, 2));
    } else {
      console.log('⚠️ Could not get polling status view');
    }

    // Test the get_meetings_for_polling function
    console.log('\n3️⃣ Testing get_meetings_for_polling function...');
    const pendingResponse = await fetch(`${SUPABASE_URL}/rest/v1/rpc/get_meetings_for_polling`, {
      method: 'POST',
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        'Content-Type': 'application/json',
      },
    });

    if (pendingResponse.ok) {
      const pendingMeetings = await pendingResponse.json();
      console.log('📋 Meetings ready for polling:', JSON.stringify(pendingMeetings, null, 2));
    } else {
      const errorText = await pendingResponse.text();
      console.log('⚠️ Could not get pending meetings:', errorText);
    }

  } catch (error) {
    console.error('❌ Error testing polling:', error);
  }
}

// Run the test
testPollingWithAuth(); 