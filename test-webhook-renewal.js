// Test script to renew calendar webhooks
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://gkkmaeobxwvramtsjabu.supabase.co';
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseServiceKey) {
  console.error('Please set SUPABASE_SERVICE_ROLE_KEY environment variable');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseServiceKey);

async function testWebhookRenewal() {
  try {
    console.log('Testing webhook renewal...');
    
    // Call the auto-renew endpoint
    const response = await fetch(`${supabaseUrl}/functions/v1/renew-calendar-webhooks/auto-renew`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${supabaseServiceKey}`,
        'Content-Type': 'application/json',
      },
    });
    
    const result = await response.json();
    console.log('Result:', JSON.stringify(result, null, 2));
    
  } catch (error) {
    console.error('Error:', error);
  }
}

testWebhookRenewal(); 