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
      const response = await fetch('https://app.attendee.dev/api/v1/bots', {
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

  return withCORS(new Response(JSON.stringify({ error: 'Not found' }), { status: 404 }));
});
