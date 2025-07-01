import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

interface TokenResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number
  scope: string
}

interface UserInfo {
  id: string
  email: string
  name?: string
  picture?: string
}

interface GoogleCredentials {
  user_id: string
  access_token: string
  refresh_token?: string
  token_type: string
  expires_at: string
  scope: string
  google_email: string
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    console.log('[exchange-google-token] Request received:', req.method, req.url)

    // Validate request method
    if (req.method !== 'POST') {
      throw new Error('Method not allowed')
    }

    // Get and validate authorization header
    const authHeader = req.headers.get('Authorization')
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      throw new Error('Missing or invalid authorization header')
    }

    // Initialize Supabase client with service role key
    const supabaseUrl = Deno.env.get('PROJECT_URL')
    const supabaseServiceKey = Deno.env.get('SERVICE_ROLE_KEY')
    
    if (!supabaseUrl || !supabaseServiceKey) {
      console.error('[exchange-google-token] Missing Supabase configuration')
      throw new Error('Server configuration error')
    }

    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Verify the JWT token and get user
    const token = authHeader.replace('Bearer ', '')
    const { data: { user }, error: authError } = await supabase.auth.getUser(token)
    
    if (authError || !user) {
      console.error('[exchange-google-token] Authentication error:', authError)
      throw new Error('Invalid or expired token')
    }

    console.log('[exchange-google-token] Authenticated user:', user.id)

    // Parse request body
    const { code } = await req.json()
    
    if (!code || typeof code !== 'string') {
      throw new Error('Missing or invalid authorization code')
    }

    // Get Google OAuth configuration from environment
    const clientId = Deno.env.get('GOOGLE_CLIENT_ID')
    const clientSecret = Deno.env.get('GOOGLE_CLIENT_SECRET')
    const redirectUri = Deno.env.get('GOOGLE_REDIRECT_URI')

    if (!clientId || !clientSecret || !redirectUri) {
      console.error('[exchange-google-token] Missing Google OAuth configuration')
      throw new Error('OAuth configuration missing')
    }

    console.log('[exchange-google-token] Exchanging authorization code for tokens...')

    // Exchange authorization code for tokens
    const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        client_id: clientId,
        client_secret: clientSecret,
        code: code,
        grant_type: 'authorization_code',
        redirect_uri: redirectUri,
      }),
    })

    if (!tokenResponse.ok) {
      const errorText = await tokenResponse.text()
      console.error('[exchange-google-token] Google token exchange failed:', tokenResponse.status, errorText)
      throw new Error(`Token exchange failed: ${tokenResponse.status}`)
    }

    const tokens: TokenResponse = await tokenResponse.json()
    console.log('[exchange-google-token] Tokens received, fetching user info...')

    // Get user information from Google
    const userInfoResponse = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
      headers: {
        'Authorization': `Bearer ${tokens.access_token}`
      }
    })

    if (!userInfoResponse.ok) {
      console.error('[exchange-google-token] Failed to fetch user info:', userInfoResponse.status)
      throw new Error('Failed to fetch user information')
    }

    const userInfo: UserInfo = await userInfoResponse.json()
    console.log('[exchange-google-token] User info received:', userInfo.email)

    // Calculate token expiration time
    const expiresAt = new Date()
    expiresAt.setSeconds(expiresAt.getSeconds() + tokens.expires_in)

    // Prepare credentials for storage
    const credentials: GoogleCredentials = {
      user_id: user.id,
      access_token: tokens.access_token,
      refresh_token: tokens.refresh_token,
      token_type: tokens.token_type,
      expires_at: expiresAt.toISOString(),
      scope: tokens.scope,
      google_email: userInfo.email
    }

    console.log('[exchange-google-token] Storing credentials in database...')

    // Store credentials in Supabase database
    const { error: dbError } = await supabase
      .from('google_credentials')
      .upsert(credentials, {
        onConflict: 'user_id'
      })

    if (dbError) {
      console.error('[exchange-google-token] Database error:', dbError)
      throw new Error('Failed to store credentials')
    }

    console.log('[exchange-google-token] Credentials stored successfully')

    // Return success response
    const response = {
      success: true,
      email: userInfo.email,
      expires_at: expiresAt.toISOString(),
      message: 'Google account connected successfully'
    }

    return new Response(
      JSON.stringify(response),
      {
        status: 200,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    )

  } catch (error) {
    console.error('[exchange-google-token] Error:', error.message)
    
    const errorResponse = {
      success: false,
      error: error.message,
      message: 'Failed to connect Google account'
    }

    return new Response(
      JSON.stringify(errorResponse),
      {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    )
  }
}) 