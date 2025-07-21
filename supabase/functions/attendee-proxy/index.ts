import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';

const MASTER_ATTENDEE_API_KEY = Deno.env.get('MASTER_ATTENDEE_API_KEY');
// const ENCRYPTION_SECRET = Deno.env.get('ATTENDEE_ENCRYPTION_SECRET') || 'dev-secret';
const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

function withCORS(resp: Response) {
  resp.headers.set('Access-Control-Allow-Origin', '*');
  resp.headers.set('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  resp.headers.set('Access-Control-Allow-Headers', 'authorization, x-client-info, apikey, content-type');
  return resp;
}

// Encryption/decryption functions commented out for potential future use
/*
async function encrypt(text: string, password: string): Promise<string> {
  const encoder = new TextEncoder();
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const keyMaterial = await crypto.subtle.importKey('raw', encoder.encode(password), { name: 'PBKDF2' }, false, ['deriveKey']);
  const key = await crypto.subtle.deriveKey({ name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' }, keyMaterial, { name: 'AES-GCM', length: 256 }, false, ['encrypt']);
  const encrypted = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, encoder.encode(text));
  const combined = new Uint8Array(salt.length + iv.length + encrypted.byteLength);
  combined.set(salt, 0);
  combined.set(iv, salt.length);
  combined.set(new Uint8Array(encrypted), salt.length + iv.length);
  return btoa(String.fromCharCode(...combined));
}

async function decrypt(encryptedText: string, password: string): Promise<string> {
  const decoder = new TextDecoder();
  const combined = new Uint8Array(atob(encryptedText).split('').map(c => c.charCodeAt(0)));
  const salt = combined.slice(0, 16);
  const iv = combined.slice(16, 28);
  const data = combined.slice(28);
  const encoder = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey('raw', encoder.encode(password), { name: 'PBKDF2' }, false, ['deriveKey']);
  const key = await crypto.subtle.deriveKey({ name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' }, keyMaterial, { name: 'AES-GCM', length: 256 }, false, ['decrypt']);
  const decrypted = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, key, data);
  return decoder.decode(decrypted);
}

async function getDecryptedApiKey(userId: string): Promise<string | null> {
  const { data, error } = await supabase
    .from('user_api_keys')
    .select('api_key')
    .eq('user_id', userId)
    .eq('service', 'attendee')
    .maybeSingle();
  if (error || !data) return null;
  return await decrypt(data.api_key, ENCRYPTION_SECRET);
}
*/

function getUserIdFromAuth(req: Request): string | null {
  const auth = req.headers.get('Authorization');
  if (!auth || !auth.startsWith('Bearer ')) return null;
  const jwt = auth.replace('Bearer ', '');
  const payload = JSON.parse(atob(jwt.split('.')[1]));
  return payload.sub || null;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return withCORS(new Response('ok', { status: 200 }));
  }

  const url = new URL(req.url);
  const method = req.method;
  const userId = getUserIdFromAuth(req);
  if (!userId) {
    return withCORS(new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 }));
  }

  if (!MASTER_ATTENDEE_API_KEY) {
    return withCORS(new Response(JSON.stringify({ error: 'Master API key not configured' }), { status: 500 }));
  }

  // Store API key endpoint commented out - using master key instead
  /*
  if (url.pathname.endsWith('/store-key') && method === 'POST') {
    try {
      const { apiKey } = await req.json();
      if (!apiKey) return withCORS(new Response(JSON.stringify({ ok: false, error: 'Missing apiKey' }), { status: 400 }));
      const encryptedKey = await encrypt(apiKey, ENCRYPTION_SECRET);
      const { error } = await supabase.from('user_api_keys').upsert({
        user_id: userId,
        service: 'attendee',
        api_key: encryptedKey
      }, { onConflict: 'user_id,service' });
      if (error) throw error;
      return withCORS(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }
  */

  // Test API key (POST /test-key) - now just validates the master key
  if (url.pathname.endsWith('/test-key') && method === 'POST') {
    try {
      // Proxy to Attendee API with POST and dummy payload
      const response = await fetch('https://app.attendee.dev/api/v1/bots', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          meeting_url: 'https://zoom.us/j/00000000000',
          bot_name: 'Sunny AI Assistant'
        })
      });
      const body = await response.text();
      if (response.status === 401 || response.status === 403) {
        // Auth error means invalid API key
        console.log('Attendee API error:', response.status, body);
        return withCORS(new Response(JSON.stringify({ ok: false, error: 'Invalid API key', status: response.status, body }), { status: 200 }));
      }
      // Any other error (e.g. 400, 422) means the key is valid but the payload is bad
      return withCORS(new Response(JSON.stringify({ ok: true, status: response.status, body }), { status: 200 }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // Send bot to meeting (POST /send-bot)
  if (url.pathname.endsWith('/send-bot') && method === 'POST') {
    try {
      const body = await req.json();
      console.log('Sending bot to Attendee API with body:', body);
      
      const response = await fetch('https://app.attendee.dev/api/v1/bots', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body)
      });
      
      console.log('Attendee API response status:', response.status);
      const data = await response.json();
      console.log('Attendee API response data:', data);
      
      return withCORS(new Response(JSON.stringify({ ok: response.ok, status: response.status, data }), { status: response.status }));
    } catch (e) {
      console.error('Error in send-bot:', e);
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // Get transcript (GET /transcript?bot_id=...)
  if (url.pathname.endsWith('/transcript') && method === 'GET') {
    try {
      const botId = url.searchParams.get('bot_id');
      if (!botId) return withCORS(new Response(JSON.stringify({ ok: false, error: 'Missing bot_id' }), { status: 400 }));
      const response = await fetch(`https://app.attendee.dev/api/v1/bots/${botId}/transcript`, {
        method: 'GET',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      return withCORS(new Response(JSON.stringify({ ok: response.ok, status: response.status, data }), { status: response.status }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // List all bots (GET /list-bots)
  if (url.pathname.endsWith('/list-bots') && method === 'GET') {
    try {
      const response = await fetch('https://app.attendee.dev/api/v1/bots', {
        method: 'GET',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`Attendee API error: ${response.status}`);
      }
      
      const data = await response.json();
      return withCORS(new Response(JSON.stringify({ ok: true, data }), { status: 200 }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // Get bot details (GET /bot-details?bot_id=...)
  if (url.pathname.endsWith('/bot-details') && method === 'GET') {
    try {
      const botId = url.searchParams.get('bot_id');
      if (!botId) return withCORS(new Response(JSON.stringify({ ok: false, error: 'Missing bot_id' }), { status: 400 }));
      const response = await fetch(`https://app.attendee.dev/api/v1/bots/${botId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      return withCORS(new Response(JSON.stringify({ ok: response.ok, status: response.status, data }), { status: response.status }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // Update scheduled bot (PATCH /update-bot)
  if (url.pathname.endsWith('/update-bot') && method === 'PATCH') {
    try {
      const { bot_id, updates } = await req.json();
      if (!bot_id) return withCORS(new Response(JSON.stringify({ ok: false, error: 'Missing bot_id' }), { status: 400 }));
      const response = await fetch(`https://app.attendee.dev/api/v1/bots/${bot_id}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates)
      });
      const data = await response.json();
      return withCORS(new Response(JSON.stringify({ ok: response.ok, status: response.status, data }), { status: response.status }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // Delete scheduled bot (DELETE /delete-bot)
  if (url.pathname.endsWith('/delete-bot') && method === 'DELETE') {
    try {
      const { bot_id } = await req.json();
      if (!bot_id) return withCORS(new Response(JSON.stringify({ ok: false, error: 'Missing bot_id' }), { status: 400 }));
      const response = await fetch(`https://app.attendee.dev/api/v1/bots/${bot_id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      return withCORS(new Response(JSON.stringify({ ok: response.ok, status: response.status, data }), { status: response.status }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // Get chat messages (GET /chat-messages?bot_id=...)
  if (url.pathname.endsWith('/chat-messages') && method === 'GET') {
    try {
      const botId = url.searchParams.get('bot_id');
      const cursor = url.searchParams.get('cursor');
      const updatedAfter = url.searchParams.get('updated_after');
      if (!botId) return withCORS(new Response(JSON.stringify({ ok: false, error: 'Missing bot_id' }), { status: 400 }));
      
      let apiUrl = `https://app.attendee.dev/api/v1/bots/${botId}/chat_messages`;
      const params = new URLSearchParams();
      if (cursor) params.append('cursor', cursor);
      if (updatedAfter) params.append('updated_after', updatedAfter);
      if (params.toString()) apiUrl += `?${params.toString()}`;
      
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      return withCORS(new Response(JSON.stringify({ ok: response.ok, status: response.status, data }), { status: response.status }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // Send chat message (POST /send-chat)
  if (url.pathname.endsWith('/send-chat') && method === 'POST') {
    try {
      const { bot_id, message, to, to_user_uuid } = await req.json();
      if (!bot_id || !message) return withCORS(new Response(JSON.stringify({ ok: false, error: 'Missing bot_id or message' }), { status: 400 }));
      
      const body: any = { message, to: to || 'everyone' };
      if (to_user_uuid) body.to_user_uuid = to_user_uuid;
      
      const response = await fetch(`https://app.attendee.dev/api/v1/bots/${bot_id}/send_chat_message`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body)
      });
      const data = await response.json();
      return withCORS(new Response(JSON.stringify({ ok: response.ok, status: response.status, data }), { status: response.status }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // Output speech (POST /speech)
  if (url.pathname.endsWith('/speech') && method === 'POST') {
    try {
      const { bot_id, text, text_to_speech_settings } = await req.json();
      if (!bot_id || !text) return withCORS(new Response(JSON.stringify({ ok: false, error: 'Missing bot_id or text' }), { status: 400 }));
      
      const response = await fetch(`https://app.attendee.dev/api/v1/bots/${bot_id}/speech`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text, text_to_speech_settings })
      });
      const data = await response.json();
      return withCORS(new Response(JSON.stringify({ ok: response.ok, status: response.status, data }), { status: response.status }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // Output audio (POST /output-audio)
  if (url.pathname.endsWith('/output-audio') && method === 'POST') {
    try {
      const { bot_id, type, data } = await req.json();
      if (!bot_id || !type || !data) return withCORS(new Response(JSON.stringify({ ok: false, error: 'Missing bot_id, type, or data' }), { status: 400 }));
      
      const response = await fetch(`https://app.attendee.dev/api/v1/bots/${bot_id}/output_audio`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ type, data })
      });
      const responseData = await response.json();
      return withCORS(new Response(JSON.stringify({ ok: response.ok, status: response.status, data: responseData }), { status: response.status }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // Output image (POST /output-image)
  if (url.pathname.endsWith('/output-image') && method === 'POST') {
    try {
      const { bot_id, type, data } = await req.json();
      if (!bot_id || !type || !data) return withCORS(new Response(JSON.stringify({ ok: false, error: 'Missing bot_id, type, or data' }), { status: 400 }));
      
      const response = await fetch(`https://app.attendee.dev/api/v1/bots/${bot_id}/output_image`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ type, data })
      });
      const responseData = await response.json();
      return withCORS(new Response(JSON.stringify({ ok: response.ok, status: response.status, data: responseData }), { status: response.status }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // Output video (POST /output-video)
  if (url.pathname.endsWith('/output-video') && method === 'POST') {
    try {
      const { bot_id, url: videoUrl } = await req.json();
      if (!bot_id || !videoUrl) return withCORS(new Response(JSON.stringify({ ok: false, error: 'Missing bot_id or url' }), { status: 400 }));
      
      const response = await fetch(`https://app.attendee.dev/api/v1/bots/${bot_id}/output_video`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: videoUrl })
      });
      const data = await response.json();
      return withCORS(new Response(JSON.stringify({ ok: response.ok, status: response.status, data }), { status: response.status }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // Get participant events (GET /participant-events?bot_id=...)
  if (url.pathname.endsWith('/participant-events') && method === 'GET') {
    try {
      const botId = url.searchParams.get('bot_id');
      const after = url.searchParams.get('after');
      const before = url.searchParams.get('before');
      const cursor = url.searchParams.get('cursor');
      if (!botId) return withCORS(new Response(JSON.stringify({ ok: false, error: 'Missing bot_id' }), { status: 400 }));
      
      let apiUrl = `https://app.attendee.dev/api/v1/bots/${botId}/participant_events`;
      const params = new URLSearchParams();
      if (after) params.append('after', after);
      if (before) params.append('before', before);
      if (cursor) params.append('cursor', cursor);
      if (params.toString()) apiUrl += `?${params.toString()}`;
      
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      return withCORS(new Response(JSON.stringify({ ok: response.ok, status: response.status, data }), { status: response.status }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // Pause recording (POST /pause-recording)
  if (url.pathname.endsWith('/pause-recording') && method === 'POST') {
    try {
      const { bot_id } = await req.json();
      if (!bot_id) return withCORS(new Response(JSON.stringify({ ok: false, error: 'Missing bot_id' }), { status: 400 }));
      
      const response = await fetch(`https://app.attendee.dev/api/v1/bots/${bot_id}/pause_recording`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      return withCORS(new Response(JSON.stringify({ ok: response.ok, status: response.status, data }), { status: response.status }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // Resume recording (POST /resume-recording)
  if (url.pathname.endsWith('/resume-recording') && method === 'POST') {
    try {
      const { bot_id } = await req.json();
      if (!bot_id) return withCORS(new Response(JSON.stringify({ ok: false, error: 'Missing bot_id' }), { status: 400 }));
      
      const response = await fetch(`https://app.attendee.dev/api/v1/bots/${bot_id}/resume_recording`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      return withCORS(new Response(JSON.stringify({ ok: response.ok, status: response.status, data }), { status: response.status }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // Get recording URL (GET /recording?bot_id=...)
  if (url.pathname.endsWith('/recording') && method === 'GET') {
    try {
      const botId = url.searchParams.get('bot_id');
      if (!botId) return withCORS(new Response(JSON.stringify({ ok: false, error: 'Missing bot_id' }), { status: 400 }));
      
      const response = await fetch(`https://app.attendee.dev/api/v1/bots/${botId}/recording`, {
        method: 'GET',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      return withCORS(new Response(JSON.stringify({ ok: response.ok, status: response.status, data }), { status: response.status }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // Leave meeting (POST /leave-meeting)
  if (url.pathname.endsWith('/leave-meeting') && method === 'POST') {
    try {
      const { bot_id } = await req.json();
      if (!bot_id) return withCORS(new Response(JSON.stringify({ ok: false, error: 'Missing bot_id' }), { status: 400 }));
      
      const response = await fetch(`https://app.attendee.dev/api/v1/bots/${bot_id}/leave`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      return withCORS(new Response(JSON.stringify({ ok: response.ok, status: response.status, data }), { status: response.status }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  // Delete bot data (POST /delete-data)
  if (url.pathname.endsWith('/delete-data') && method === 'POST') {
    try {
      const { bot_id } = await req.json();
      if (!bot_id) return withCORS(new Response(JSON.stringify({ ok: false, error: 'Missing bot_id' }), { status: 400 }));
      
      const response = await fetch(`https://app.attendee.dev/api/v1/bots/${bot_id}/delete_data`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      return withCORS(new Response(JSON.stringify({ ok: response.ok, status: response.status, data }), { status: response.status }));
    } catch (e) {
      return withCORS(new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500 }));
    }
  }

  return withCORS(new Response(JSON.stringify({ error: 'Not found' }), { status: 404 }));
});
