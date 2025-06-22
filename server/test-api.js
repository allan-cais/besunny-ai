// Simple test script for the chat API
const fetch = require('node-fetch');

const BASE_URL = 'http://localhost:3001';

async function testHealth() {
  try {
    const response = await fetch(`${BASE_URL}/api/health`);
    const data = await response.json();
    console.log('✅ Health check:', data);
  } catch (error) {
    console.error('❌ Health check failed:', error.message);
  }
}

async function testChat() {
  try {
    console.log('🧪 Testing chat API...');
    
    const response = await fetch(`${BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: 'Hello, this is a test message',
        sessionId: 'test-session-123',
        messageId: 'test-msg-456'
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    console.log('✅ Chat API response received');
    console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()));
    
    // Read the streaming response
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      console.log('📨 Chunk received:', chunk.trim());
    }
    
  } catch (error) {
    console.error('❌ Chat API test failed:', error.message);
  }
}

async function runTests() {
  console.log('🚀 Starting API tests...\n');
  
  await testHealth();
  console.log('');
  
  await testChat();
  console.log('\n✨ Tests completed!');
}

// Run tests if this file is executed directly
if (require.main === module) {
  runTests();
}

module.exports = { testHealth, testChat }; 