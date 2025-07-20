// Test script to verify calendar sync functionality
// Run this in your browser console on the meetings page

async function testCalendarSync() {
  console.log('=== Calendar Sync Test ===');
  
  try {
    // Test 1: Check webhook status
    console.log('1. Checking webhook status...');
    const webhookStatus = await calendarService.getSyncStatus();
    console.log('Webhook status:', webhookStatus);
    
    // Test 2: Get raw calendar events from Google
    console.log('2. Getting raw calendar events from Google...');
    const rawEvents = await calendarService.getRawCalendarEvents(7, 60);
    console.log('Raw events result:', rawEvents);
    
    if (rawEvents.ok) {
      console.log(`Found ${rawEvents.events_with_urls} events with meeting URLs out of ${rawEvents.total_events} total events`);
      console.log('Events with URLs:', rawEvents.events_with_urls_only);
    }
    
    // Test 3: Get current meetings in database
    console.log('3. Getting current meetings from database...');
    const currentMeetings = await calendarService.getUpcomingMeetings();
    console.log('Current meetings count:', currentMeetings.length);
    console.log('Current meetings:', currentMeetings.map(m => ({
      title: m.title,
      start_time: m.start_time,
      meeting_url: m.meeting_url ? 'Has URL' : 'No URL',
      google_calendar_event_id: m.google_calendar_event_id
    })));
    
    // Test 4: Perform manual sync
    console.log('4. Performing manual sync...');
    const syncResult = await calendarService.fullSync(undefined, 30, 60);
    console.log('Manual sync result:', syncResult);
    
    // Test 5: Get meetings after sync
    console.log('5. Getting meetings after sync...');
    const updatedMeetings = await calendarService.getUpcomingMeetings();
    console.log('Updated meetings count:', updatedMeetings.length);
    console.log('Updated meetings:', updatedMeetings.map(m => ({
      title: m.title,
      start_time: m.start_time,
      meeting_url: m.meeting_url ? 'Has URL' : 'No URL',
      google_calendar_event_id: m.google_calendar_event_id
    })));
    
    // Test 6: Check for new meetings
    const newMeetings = updatedMeetings.filter(m => 
      !currentMeetings.some(cm => cm.id === m.id)
    );
    console.log('6. New meetings found:', newMeetings.length);
    if (newMeetings.length > 0) {
      console.log('New meetings:', newMeetings.map(m => ({
        title: m.title,
        start_time: m.start_time,
        meeting_url: m.meeting_url ? 'Has URL' : 'No URL',
        google_calendar_event_id: m.google_calendar_event_id
      })));
    }
    
    // Test 7: Compare with raw events
    if (rawEvents.ok) {
      console.log('7. Comparing database meetings with Google Calendar events...');
      const googleEventIds = rawEvents.events_with_urls_only.map(e => e.id);
      const dbEventIds = updatedMeetings.map(m => m.google_calendar_event_id).filter(id => id);
      
      const missingInDb = googleEventIds.filter(id => !dbEventIds.includes(id));
      const extraInDb = dbEventIds.filter(id => !googleEventIds.includes(id));
      
      console.log('Missing in database:', missingInDb.length, missingInDb);
      console.log('Extra in database:', extraInDb.length, extraInDb);
    }
    
    console.log('=== Test Complete ===');
    
  } catch (error) {
    console.error('Test failed:', error);
  }
}

// Test webhook sync specifically
async function testWebhookSync() {
  console.log('=== Webhook Sync Test ===');
  
  try {
    // Test 1: Check webhook status
    console.log('1. Checking webhook status...');
    const webhookStatus = await calendarService.getSyncStatus();
    console.log('Webhook status:', webhookStatus);
    
    if (!webhookStatus.webhook_active) {
      console.log('Webhook is not active. Setting up webhook...');
      const setupResult = await calendarService.setupWebhookSync();
      console.log('Setup result:', setupResult);
    }
    
    // Test 2: Trigger webhook sync
    console.log('2. Triggering webhook sync...');
    const webhookResult = await calendarService.triggerWebhookSync();
    console.log('Webhook sync result:', webhookResult);
    
    // Test 3: Check meetings after webhook sync
    console.log('3. Checking meetings after webhook sync...');
    const meetings = await calendarService.getUpcomingMeetings();
    console.log('Meetings after webhook sync:', meetings.length);
    console.log('Meetings:', meetings.map(m => ({
      title: m.title,
      start_time: m.start_time,
      meeting_url: m.meeting_url ? 'Has URL' : 'No URL',
      google_calendar_event_id: m.google_calendar_event_id
    })));
    
    console.log('=== Webhook Test Complete ===');
    
  } catch (error) {
    console.error('Webhook test failed:', error);
  }
}

// Run the tests
console.log('Running calendar sync tests...');
await testCalendarSync();
console.log('\nRunning webhook sync tests...');
await testWebhookSync(); 