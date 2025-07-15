// Test script to verify webhook renewal works
// Run with: node test-renewal.js

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://gkkmaeobxwvramtsjabu.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdra21hZW9ieHd2cmFtdHNqYWJ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ5NzI5NzAsImV4cCI6MjA1MDU0ODk3MH0.12ae7f93d2d7f32e45e9b064758f95778ea2982f3b34ad095d75a8f7e874e9a8';

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function testRenewal() {
  try {
    console.log('🔍 Getting current session...');
    
    // Get current session
    const { data: { session }, error: sessionError } = await supabase.auth.getSession();
    
    if (sessionError || !session) {
      console.error('❌ No active session found. Please log in first.');
      return;
    }
    
    console.log('✅ Session found for user:', session.user.email);
    
    // Test the webhook renewal
    console.log('🔄 Testing webhook renewal...');
    const response = await fetch(`${supabaseUrl}/functions/v1/renew-calendar-webhooks/renew`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ userId: session.user.id }),
    });
    
    const result = await response.json();
    
    if (result.ok) {
      console.log('✅ Webhook renewed successfully!');
      console.log('📋 Webhook ID:', result.webhook_id);
      console.log('💬 Message:', result.message);
    } else {
      console.error('❌ Failed to renew webhook:');
      console.error('   Error:', result.error);
    }
    
  } catch (error) {
    console.error('💥 Error:', error.message);
  }
}

testRenewal(); 