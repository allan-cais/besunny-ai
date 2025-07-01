import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  scope: string;
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    // Only allow POST (for cron job or admin use)
    if (req.method !== 'POST') {
      return new Response('Method not allowed', { status: 405, headers: corsHeaders });
    }

    // Initialize Supabase client with service role key
    const supabaseUrl = Deno.env.get('PROJECT_URL');
    const supabaseServiceKey = Deno.env.get('SERVICE_ROLE_KEY');
    if (!supabaseUrl || !supabaseServiceKey) {
      throw new Error('Missing Supabase configuration');
    }
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Get Google OAuth config from environment
    const clientId = Deno.env.get('GOOGLE_CLIENT_ID');
    const clientSecret = Deno.env.get('GOOGLE_CLIENT_SECRET');
    if (!clientId || !clientSecret) {
      throw new Error('Missing Google OAuth configuration');
    }

    // Find all users whose tokens expire in the next 10 minutes
    const now = new Date();
    const soon = new Date(now.getTime() + 10 * 60 * 1000); // 10 minutes from now
    const { data: users, error } = await supabase
      .from('google_credentials')
      .select('*')
      .lt('expires_at', soon.toISOString());

    if (error) {
      throw new Error('Failed to query google_credentials: ' + error.message);
    }

    if (!users || users.length === 0) {
      return new Response(JSON.stringify({ refreshed: 0, message: 'No tokens need refresh.' }), { status: 200, headers: corsHeaders });
    }

    let refreshed = 0;
    let failed = 0;
    const results: any[] = [];

    for (const user of users) {
      if (!user.refresh_token) {
        results.push({ user_id: user.user_id, error: 'No refresh_token' });
        failed++;
        continue;
      }
      try {
        // Refresh the token
        const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({
            client_id: clientId,
            client_secret: clientSecret,
            refresh_token: user.refresh_token,
            grant_type: 'refresh_token',
          }),
        });
        if (!tokenResponse.ok) {
          const errorText = await tokenResponse.text();
          results.push({ user_id: user.user_id, error: 'Google refresh failed: ' + errorText });
          failed++;
          continue;
        }
        const tokens: TokenResponse = await tokenResponse.json();
        // Calculate new expiry
        const expiresAt = new Date();
        expiresAt.setSeconds(expiresAt.getSeconds() + tokens.expires_in);
        // Update credentials in DB
        const { error: updateError } = await supabase
          .from('google_credentials')
          .update({
            access_token: tokens.access_token,
            expires_at: expiresAt.toISOString(),
            scope: tokens.scope,
            // Only update refresh_token if Google returns a new one
            ...(tokens.refresh_token ? { refresh_token: tokens.refresh_token } : {}),
          })
          .eq('user_id', user.user_id);
        if (updateError) {
          results.push({ user_id: user.user_id, error: 'DB update failed: ' + updateError.message });
          failed++;
        } else {
          results.push({ user_id: user.user_id, refreshed: true });
          refreshed++;
        }
      } catch (err) {
        results.push({ user_id: user.user_id, error: err.message });
        failed++;
      }
    }

    return new Response(JSON.stringify({ refreshed, failed, results }), { status: 200, headers: corsHeaders });
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), { status: 500, headers: corsHeaders });
  }
}); 