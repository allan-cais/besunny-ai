// Debug test script for n8n webhook integration

async function testN8nWebhook() {
  const fetch = (await import('node-fetch')).default;
  const n8nWebhookUrl = 'https://n8n.customaistudio.io/webhook/kirit-rag-webhook';
  
  console.log('🔍 Testing n8n webhook integration...');
  console.log(`📡 Webhook URL: ${n8nWebhookUrl}`);
  
  const requestBody = {
    message: 'Hello, this is a test message',
    sessionId: 'test-session-123',
    messageId: 'test-msg-456',
    timestamp: new Date().toISOString(),
    metadata: {
      userAgent: 'debug-test',
      ip: '127.0.0.1',
    }
  };
  
  console.log('📤 Request body:', JSON.stringify(requestBody, null, 2));
  
  try {
    console.log('📡 Making request to n8n...');
    
    const response = await fetch(n8nWebhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });
    
    console.log(`📥 Response status: ${response.status}`);
    console.log(`📥 Response headers:`, Object.fromEntries(response.headers.entries()));
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const responseText = await response.text();
    console.log(`📨 Response text length: ${responseText.length}`);
    console.log(`📨 Response text: "${responseText}"`);
    
    if (!responseText || responseText.trim() === '') {
      console.log('⚠️  Empty response from n8n webhook');
      console.log('💡 This means the n8n workflow is not configured to return a response');
      console.log('💡 You need to configure your n8n workflow to return a response');
    } else {
      console.log('✅ Received response from n8n webhook');
    }
    
  } catch (error) {
    console.error('❌ Error testing n8n webhook:', error.message);
  }
}

async function testLocalAPI() {
  const fetch = (await import('node-fetch')).default;
  console.log('\n🔍 Testing local API...');
  
  try {
    const response = await fetch('http://localhost:3001/api/chat', {
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
    
    console.log(`📥 Local API response status: ${response.status}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      fullResponse += chunk;
      console.log(`📨 Chunk: ${chunk.trim()}`);
    }
    
    console.log(`📨 Full response: ${fullResponse}`);
    
  } catch (error) {
    console.error('❌ Error testing local API:', error.message);
  }
}

async function runTests() {
  console.log('🚀 Starting debug tests...\n');
  
  await testN8nWebhook();
  await testLocalAPI();
  
  console.log('\n✨ Debug tests completed!');
}

// Run tests if this file is executed directly
if (require.main === module) {
  runTests();
}

module.exports = { testN8nWebhook, testLocalAPI }; 