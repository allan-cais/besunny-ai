// Test script to directly call Attendee API transcript endpoint
const MASTER_ATTENDEE_API_KEY = 'your_master_attendee_api_key_here'; // Replace with actual key

async function testAttendeeAPI() {
  console.log('🧪 Testing Attendee API transcript endpoint...');
  
  const botId = 'bot_KekwtuOP1VjaMJMV';
  
  try {
    // Call the Attendee API transcript endpoint
    const response = await fetch(`https://app.attendee.dev/api/v1/bots/${botId}/transcript`, {
      method: 'GET',
      headers: {
        'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
        'Content-Type': 'application/json',
      },
    });

    console.log(`📡 API Response status: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Failed to get transcript:', {
        status: response.status,
        statusText: response.statusText,
        error: errorText
      });
      return;
    }

    const transcriptData = await response.json();
    console.log('✅ Raw transcript API response:');
    console.log(JSON.stringify(transcriptData, null, 2));

    // Analyze the transcript data structure
    if (Array.isArray(transcriptData)) {
      console.log(`📊 Transcript has ${transcriptData.length} entries`);
      
      // Show first few entries
      transcriptData.slice(0, 3).forEach((entry, index) => {
        console.log(`\nEntry ${index + 1}:`);
        console.log(`  Speaker: ${entry.speaker_name || 'Unknown'}`);
        console.log(`  Timestamp: ${new Date(entry.timestamp_ms).toISOString()}`);
        console.log(`  Duration: ${entry.duration_ms}ms`);
        console.log(`  Text: ${entry.transcription?.transcript || 'No transcript'}`);
      });

      // Count unique speakers
      const speakers = new Set(transcriptData.map(entry => entry.speaker_name).filter(Boolean));
      console.log(`\n👥 Unique speakers: ${Array.from(speakers).join(', ')}`);

      // Calculate total duration
      const totalDuration = transcriptData.reduce((sum, entry) => sum + (entry.duration_ms || 0), 0);
      console.log(`⏱️ Total duration: ${Math.round(totalDuration / 1000)} seconds`);

    } else {
      console.log('📝 Transcript is not an array, format:', typeof transcriptData);
    }

  } catch (error) {
    console.error('❌ Error testing Attendee API:', error);
  }
}

// Run the test
console.log('⚠️  Please replace MASTER_ATTENDEE_API_KEY with your actual API key before running');
// testAttendeeAPI(); 