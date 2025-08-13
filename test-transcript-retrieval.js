// Test script to manually trigger polling for transcript retrieval
// IMPORTANT: Set these environment variables before running:
// SUPABASE_URL=your_supabase_url
// SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

const SUPABASE_URL = process.env.SUPABASE_URL || 'https://your-project.supabase.co';
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!SUPABASE_SERVICE_ROLE_KEY) {
  console.error('❌ SUPABASE_SERVICE_ROLE_KEY environment variable is required');
  console.error('Please set it before running this script');
  process.exit(1);
}

async function testTranscriptRetrieval() {
  console.log('🧪 Testing transcript retrieval for completed meeting...');
  
  try {
    // Call the edge function to poll all meetings
    const response = await fetch(`${SUPABASE_URL}/functions/v1/attendee-polling-service`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({})
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Error calling edge function:', response.status, errorText);
      return;
    }

    const result = await response.json();
    console.log('✅ Edge function response:', JSON.stringify(result, null, 2));

    // Check if any meetings were processed
    if (result.result && result.result.length > 0) {
      console.log('📋 Meetings processed:');
      result.result.forEach((meeting) => {
        console.log(`  - Meeting ID: ${meeting.meetingId}`);
        console.log(`  - Status: ${meeting.status}`);
        console.log(`  - Transcript Retrieved: ${meeting.transcript_retrieved}`);
        if (meeting.transcript_summary) {
          console.log(`  - Summary: ${meeting.transcript_summary}`);
        }
        if (meeting.error) {
          console.log(`  - Error: ${meeting.error}`);
        }
      });
    } else {
      console.log('ℹ️ No meetings were processed');
    }

  } catch (error) {
    console.error('❌ Error testing transcript retrieval:', error);
  }
}

// Run the test
testTranscriptRetrieval();
