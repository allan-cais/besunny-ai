// Test script for the project-onboarding-ai edge function
// Run this with: node test-ai-function.js

const fetch = require('node-fetch');

async function testAIFunction() {
  const SUPABASE_URL = 'https://gkkmaeobxwvramtsjabu.supabase.co';
  const FUNCTION_URL = `${SUPABASE_URL}/functions/v1/project-onboarding-ai`;
  
  // You'll need to get a valid JWT token from your app
  const JWT_TOKEN = 'YOUR_JWT_TOKEN_HERE'; // Replace with actual token
  
  const testPayload = {
    project_id: 'test-project-' + Date.now(),
    user_id: 'test-user-id',
    summary: {
      project_name: 'Test Video Production Project',
      overview: 'A commercial video production for a tech company',
      keywords: ['video', 'production', 'commercial', 'tech'],
      deliverables: '30-second commercial, behind-the-scenes footage, social media clips',
      contacts: {
        internal_lead: 'John Smith',
        agency_lead: 'Jane Doe',
        client_lead: 'Bob Johnson'
      },
      shoot_date: '2024-02-15',
      location: 'San Francisco, CA',
      references: 'https://example.com/reference'
    }
  };

  try {
    console.log('Testing AI function with payload:', JSON.stringify(testPayload, null, 2));
    
    const response = await fetch(FUNCTION_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${JWT_TOKEN}`,
      },
      body: JSON.stringify(testPayload)
    });

    console.log('Response status:', response.status);
    console.log('Response headers:', Object.fromEntries(response.headers.entries()));
    
    const result = await response.text();
    console.log('Response body:', result);
    
    try {
      const jsonResult = JSON.parse(result);
      console.log('Parsed JSON result:', JSON.stringify(jsonResult, null, 2));
    } catch (e) {
      console.log('Response is not valid JSON');
    }
    
  } catch (error) {
    console.error('Error testing function:', error);
  }
}

// Instructions for use:
console.log('To test the AI function:');
console.log('1. Get a JWT token from your app (check browser dev tools)');
console.log('2. Replace YOUR_JWT_TOKEN_HERE with the actual token');
console.log('3. Run: node test-ai-function.js');
console.log('');

// Uncomment the line below to run the test
// testAIFunction(); 