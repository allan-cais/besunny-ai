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
  google_name?: string
  google_picture?: string
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
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
      throw new Error('Server configuration error')
    }

    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Verify the JWT token and get user
    const token = authHeader.replace('Bearer ', '')
    const { data: { user }, error: authError } = await supabase.auth.getUser(token)
    
    if (authError || !user) {
      throw new Error('Invalid or expired token')
    }

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
      throw new Error('OAuth configuration missing')
    }

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
      throw new Error(`Token exchange failed: ${tokenResponse.status}`)
    }

    const tokens: TokenResponse = await tokenResponse.json()

    // Get user information from Google
    const userInfoResponse = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
      headers: {
        'Authorization': `Bearer ${tokens.access_token}`
      }
    })

    if (!userInfoResponse.ok) {
      throw new Error('Failed to fetch user information')
    }

    const userInfo: UserInfo = await userInfoResponse.json()

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
      google_email: userInfo.email,
      google_name: userInfo.name,
      google_picture: userInfo.picture
    }

    // Store credentials in Supabase database
    const { error: dbError } = await supabase
      .from('google_credentials')
      .upsert(credentials, {
        onConflict: 'user_id'
      })

    if (dbError) {
      throw new Error('Failed to store credentials')
    }

    // Update user metadata with Google profile information if not already set
    // This allows email users to get Google profile picture when they connect Google
    const currentMetadata = user.user_metadata || {};
    const updatedMetadata = { ...currentMetadata };
    
    // Only update if the user doesn't already have a name or picture from Google
    if (!currentMetadata.name && userInfo.name) {
      updatedMetadata.name = userInfo.name;
    }
    if (!currentMetadata.picture && userInfo.picture) {
      updatedMetadata.picture = userInfo.picture;
    }
    if (!currentMetadata.provider) {
      updatedMetadata.provider = 'google';
    }

    // Update user metadata if we have new information
    if (JSON.stringify(updatedMetadata) !== JSON.stringify(currentMetadata)) {
      const { error: updateError } = await supabase.auth.admin.updateUserById(
        user.id,
        { user_metadata: updatedMetadata }
      );
      
      if (updateError) {
        // Failed to update user metadata
        // Don't fail the whole operation if metadata update fails
      }
    }

    // Return success response
    const response = {
      success: true,
      email: userInfo.email,
      name: userInfo.name,
      picture: userInfo.picture,
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