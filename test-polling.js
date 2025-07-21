// Test script to manually trigger polling and see API responses
import fetch from 'node-fetch';

const SUPABASE_URL = 'https://gkkmaeobxwvramtsjabu.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdra21hZW9ieHd2cmFtdHNqYWJ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMxMTg2MjEsImV4cCI6MjA2ODY5NDYyMX0.Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8';

async function testPolling() {
  try {
    console.log('🧪 Testing polling functionality...\n');

    // First, let's get the meetings that need polling
    console.log('1️⃣ Getting meetings that need polling...');
    const pendingResponse = await fetch(`${SUPABASE_URL}/functions/v1/attendee-polling-service/get-pending`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        'Content-Type': 'application/json',
      },
    });

    if (!pendingResponse.ok) {
      throw new Error(`Failed to get pending meetings: ${pendingResponse.status}`);
    }

    const pendingData = await pendingResponse.json();
    console.log('📋 Pending meetings:', JSON.stringify(pendingData, null, 2));

    if (!pendingData.meetings || pendingData.meetings.length === 0) {
      console.log('ℹ️ No meetings need polling at the moment');
      return;
    }

    // Test polling the first meeting
    const firstMeeting = pendingData.meetings[0];
    console.log(`\n2️⃣ Testing polling for meeting: ${firstMeeting.id} (${firstMeeting.title})`);

    const pollResponse = await fetch(`${SUPABASE_URL}/functions/v1/attendee-polling-service/poll-meeting`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ meetingId: firstMeeting.id }),
    });

    if (!pollResponse.ok) {
      const errorText = await pollResponse.text();
      throw new Error(`Failed to poll meeting: ${pollResponse.status} - ${errorText}`);
    }

    const pollResult = await pollResponse.json();
    console.log('📊 Polling result:', JSON.stringify(pollResult, null, 2));

    // Also test the general poll-all endpoint
    console.log('\n3️⃣ Testing poll-all functionality...');
    const pollAllResponse = await fetch(`${SUPABASE_URL}/functions/v1/attendee-polling-service/poll-now`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        'Content-Type': 'application/json',
      },
    });

    if (!pollAllResponse.ok) {
      const errorText = await pollAllResponse.text();
      throw new Error(`Failed to poll all meetings: ${pollAllResponse.status} - ${errorText}`);
    }

    const pollAllResult = await pollAllResponse.json();
    console.log('📊 Poll-all result:', JSON.stringify(pollAllResult, null, 2));

  } catch (error) {
    console.error('❌ Error testing polling:', error);
  }
}

// Run the test
testPolling(); 