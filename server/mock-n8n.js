// Mock n8n webhook server for testing
const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 3002;

app.use(cors());
app.use(express.json());

// Mock n8n webhook endpoint
app.post('/webhook/chat', async (req, res) => {
  console.log('📥 Mock n8n received request:', req.body);
  
  const { message, sessionId, messageId } = req.body;
  
  // Set headers for streaming response
  res.setHeader('Content-Type', 'text/plain');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  
  // Simulate AI response
  const responses = [
    `Hello! I received your message: "${message}". This is a mock response from the n8n webhook.`,
    `I'm processing your request for session ${sessionId} with message ID ${messageId}.`,
    `This is a simulated streaming response to demonstrate the chat functionality.`,
    `The backend is working correctly and can handle real-time streaming from n8n webhooks.`,
    `You can replace this mock with your actual n8n workflow that connects to your preferred LLM.`
  ];
  
  // Send response in chunks to simulate streaming
  for (const response of responses) {
    const words = response.split(' ');
    
    for (const word of words) {
      res.write(word + ' ');
      // Add delay to simulate real streaming
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    res.write('\n\n');
    await new Promise(resolve => setTimeout(resolve, 200));
  }
  
  res.end();
});

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    service: 'mock-n8n-webhook',
    timestamp: new Date().toISOString() 
  });
});

app.listen(PORT, () => {
  console.log(`🤖 Mock n8n webhook server running on port ${PORT}`);
  console.log(`📡 Webhook endpoint: http://localhost:${PORT}/webhook/chat`);
  console.log(`🏥 Health check: http://localhost:${PORT}/health`);
  console.log('');
  console.log('💡 To use this mock webhook, set N8N_WEBHOOK_URL=http://localhost:3002/webhook/chat');
});

module.exports = app; 