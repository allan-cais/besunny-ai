import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import supabaseService from './services/supabase';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Types
interface ChatMessage {
  id: string;
  sessionId: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
}

interface ChatRequest {
  message: string;
  sessionId: string;
  messageId: string;
}

// Chat API endpoint
app.post('/api/chat', async (req, res) => {
  const { message, sessionId, messageId }: ChatRequest = req.body;

  if (!message || !sessionId) {
    return res.status(400).json({ error: 'Missing required fields' });
  }

  // Set headers for streaming
  res.setHeader('Content-Type', 'text/plain');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Cache-Control');

  let userMessage: ChatMessage | null = null;
  let assistantMessage: ChatMessage | null = null;

  try {
    console.log('🚀 Starting chat request...');
    
    // Create user message
    userMessage = {
      id: messageId,
      sessionId,
      role: 'user',
      content: message,
      createdAt: new Date().toISOString()
    };

    // Create assistant message placeholder
    assistantMessage = {
      id: (Date.now() + 1).toString(),
      sessionId,
      role: 'assistant',
      content: '',
      createdAt: new Date().toISOString()
    };

    // Get n8n webhook URL from environment
    const n8nWebhookUrl = process.env.N8N_WEBHOOK_URL;
    
    if (!n8nWebhookUrl) {
      throw new Error('N8N_WEBHOOK_URL not configured');
    }

    console.log(`📡 Calling n8n webhook: ${n8nWebhookUrl}`);

    // Prepare the request to n8n
    const n8nRequest = {
      message,
      sessionId,
      messageId: assistantMessage.id,
      timestamp: new Date().toISOString(),
      // Add any additional metadata you want to send to n8n
      metadata: {
        userAgent: req.get('User-Agent'),
        ip: req.ip,
      }
    };

    console.log('📤 Sending request to n8n:', JSON.stringify(n8nRequest, null, 2));

    // Make request to n8n webhook
    console.log('📡 Making fetch request...');
    const n8nResponse = await fetch(n8nWebhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(n8nRequest),
    });

    console.log(`📥 n8n response status: ${n8nResponse.status}`);
    console.log(`📥 n8n response headers:`, Object.fromEntries(n8nResponse.headers.entries()));

    if (!n8nResponse.ok) {
      throw new Error(`N8N webhook failed: ${n8nResponse.status} ${n8nResponse.statusText}`);
    }

    // Check if n8n supports streaming
    const contentType = n8nResponse.headers.get('content-type');
    const isStreaming = contentType?.includes('text/event-stream') || 
                       contentType?.includes('text/plain') ||
                       n8nResponse.headers.get('transfer-encoding') === 'chunked';

    console.log(`📊 Response type: ${isStreaming ? 'streaming' : 'non-streaming'}`);
    console.log(`📊 Content-Type: ${contentType}`);

    let accumulatedContent = '';

    if (isStreaming && n8nResponse.body) {
      console.log('📡 Processing streaming response...');
      // Handle streaming response from n8n
      const reader = n8nResponse.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          console.log('✅ Streaming completed');
          // Send completion signal
          res.write('data: [DONE]\n\n');
          break;
        }

        const chunk = decoder.decode(value);
        console.log(`📨 Received chunk: ${chunk.length} bytes`);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.trim()) {
            // Forward the chunk from n8n to the client
            res.write(`data: ${JSON.stringify({ content: line })}\n\n`);
            accumulatedContent += line;
          }
        }
      }
    } else {
      console.log('📡 Processing non-streaming response...');
      // Handle non-streaming response from n8n
      const responseText = await n8nResponse.text();
      console.log(`📨 Response text length: ${responseText.length}`);
      console.log(`📨 Response text: "${responseText}"`);
      
      if (!responseText || responseText.trim() === '') {
        console.log('⚠️  Empty response from n8n webhook, providing default response');
        // If n8n returns empty response, provide a default response
        const defaultResponse = `I received your message: "${message}". This is a default response since the n8n workflow didn't return any content. Please check your n8n workflow configuration to ensure it returns a response.`;
        
        console.log('📤 Sending default response...');
        // Simulate streaming by sending the response in chunks
        const words = defaultResponse.split(' ');
        for (const word of words) {
          res.write(`data: ${JSON.stringify({ content: word + ' ' })}\n\n`);
          accumulatedContent += word + ' ';
          // Add a small delay to simulate streaming
          await new Promise(resolve => setTimeout(resolve, 50));
        }
        console.log('✅ Default response sent');
      } else {
        console.log('📤 Sending n8n response...');
        
        // Try to parse as JSON first (n8n might return JSON with an 'output' field)
        let responseContent = responseText;
        try {
          const jsonResponse = JSON.parse(responseText);
          if (jsonResponse.output) {
            responseContent = jsonResponse.output;
            console.log('📨 Parsed JSON response with output field:', responseContent);
          } else if (jsonResponse.message) {
            responseContent = jsonResponse.message;
            console.log('📨 Parsed JSON response with message field:', responseContent);
          } else if (jsonResponse.content) {
            responseContent = jsonResponse.content;
            console.log('📨 Parsed JSON response with content field:', responseContent);
          } else {
            console.log('📨 JSON response without expected fields, using full response');
          }
        } catch (parseError) {
          console.log('📨 Response is not JSON, treating as plain text');
          responseContent = responseText;
        }
        
        // Simulate streaming by sending the response in chunks
        const words = responseContent.split(' ');
        for (const word of words) {
          res.write(`data: ${JSON.stringify({ content: word + ' ' })}\n\n`);
          accumulatedContent += word + ' ';
          // Add a small delay to simulate streaming
          await new Promise(resolve => setTimeout(resolve, 50));
        }
        console.log('✅ n8n response sent');
      }
      
      res.write('data: [DONE]\n\n');
    }

    // Update assistant message with final content
    if (assistantMessage) {
      assistantMessage.content = accumulatedContent;
    }

    console.log(`💾 Saving messages to Supabase...`);

    // Save messages to Supabase
    if (userMessage && assistantMessage) {
      await supabaseService.saveMessages([userMessage, assistantMessage]);
    }

    console.log(`✅ Chat request completed successfully`);

    res.end();

  } catch (error) {
    console.error('❌ Chat API error:', error);
    console.error('❌ Error stack:', error instanceof Error ? error.stack : 'No stack trace');
    
    // Update assistant message with error content
    if (assistantMessage) {
      assistantMessage.content = 'Sorry, I encountered an error. Please try again.';
    }

    // Save error messages to Supabase
    if (userMessage && assistantMessage) {
      try {
        await supabaseService.saveMessages([userMessage, assistantMessage]);
      } catch (saveError) {
        console.error('Failed to save error messages:', saveError);
      }
    }
    
    // Send error response
    console.log('📤 Sending error response...');
    res.write(`data: ${JSON.stringify({ content: 'Sorry, I encountered an error. Please try again.' })}\n\n`);
    res.write('data: [DONE]\n\n');
    res.end();
  }
});

// Get chat history endpoint
app.get('/api/chat/:sessionId', async (req, res) => {
  const { sessionId } = req.params;
  const limit = parseInt(req.query.limit as string) || 50;

  try {
    const messages = await supabaseService.getMessagesBySession(sessionId, limit);
    res.json({ messages });
  } catch (error) {
    console.error('Error fetching chat history:', error);
    res.status(500).json({ error: 'Failed to fetch chat history' });
  }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    supabase: supabaseService.isConfigured() ? 'configured' : 'not configured',
    n8n_webhook: process.env.N8N_WEBHOOK_URL || 'not configured'
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📡 Chat API available at http://localhost:${PORT}/api/chat`);
  console.log(`🏥 Health check at http://localhost:${PORT}/api/health`);
  console.log(`🔗 N8N Webhook: ${process.env.N8N_WEBHOOK_URL || 'not configured'}`);
  console.log(`💾 Supabase: ${supabaseService.isConfigured() ? 'Configured' : 'Not configured'}`);
});

export default app; 