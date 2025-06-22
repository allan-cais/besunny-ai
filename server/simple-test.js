// Simple test for n8n webhook
const fetch = (async () => {
  const { default: fetch } = await import('node-fetch');
  return fetch;
})();

async function testN8n() {
  const n8nWebhookUrl = 'https://n8n.customaistudio.io/webhook/kirit-rag-webhook';
  
  console.log('Testing n8n webhook...');
  
  try {
    const response = await (await fetch)(n8nWebhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: 'Hello, this is a test message',
        sessionId: 'test-session-123',
        messageId: 'test-msg-456',
        timestamp: new Date().toISOString(),
        metadata: {
          userAgent: 'test',
          ip: '127.0.0.1',
        }
      }),
    });
    
    console.log(`Status: ${response.status}`);
    console.log(`Headers:`, Object.fromEntries(response.headers.entries()));
    
    const text = await response.text();
    console.log(`Response length: ${text.length}`);
    console.log(`Response: "${text}"`);
    
    if (!text || text.trim() === '') {
      console.log('Empty response - this is the issue!');
    }
    
  } catch (error) {
    console.error('Error:', error.message);
  }
}

testN8n(); 