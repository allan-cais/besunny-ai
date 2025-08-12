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

    // Initialize Supabase client with service role key
    const supabaseUrl = Deno.env.get('PROJECT_URL')
    const supabaseServiceKey = Deno.env.get('SERVICE_ROLE_KEY')
    
    if (!supabaseUrl || !supabaseServiceKey) {
      throw new Error('Server configuration error')
    }

    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Parse request body
    const { code } = await req.json()
    
    if (!code || typeof code !== 'string') {
      throw new Error('Missing or invalid authorization code')
    }

    // Get Google OAuth configuration from environment
    const clientId = Deno.env.get('GOOGLE_CLIENT_ID')
    const clientSecret = Deno.env.get('GOOGLE_CLIENT_SECRET')
    const redirectUri = Deno.env.get('GOOGLE_LOGIN_REDIRECT_URI')

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

    // Check if user already exists with this Google user ID
    const { data: existingUser, error: lookupError } = await supabase
      .rpc('get_user_by_google_id', { google_user_id: userInfo.id })

    if (lookupError) {
      throw new Error('Failed to check existing user')
    }

    let userId: string

    if (existingUser && existingUser.length > 0) {
      // User exists, update their credentials
      userId = existingUser[0].user_id
      
      const { error: updateError } = await supabase
        .from('google_credentials')
        .update({
          access_token: tokens.access_token,
          refresh_token: tokens.refresh_token,
          token_type: tokens.token_type,
          expires_at: expiresAt.toISOString(),
          scope: tokens.scope,
          google_email: userInfo.email,
          google_name: userInfo.name,
          google_picture: userInfo.picture,
          updated_at: new Date().toISOString()
        })
        .eq('user_id', userId)
        .eq('login_provider', true)

      if (updateError) {
        throw new Error('Failed to update user credentials')
      }
    } else {
      // Create new user or link existing email account
      const { data: newUserId, error: createError } = await supabase
        .rpc('handle_google_oauth_login', {
          google_user_id: userInfo.id,
          google_email: userInfo.email,
          google_name: userInfo.name || '',
          google_picture: userInfo.picture || '',
          access_token: tokens.access_token,
          refresh_token: tokens.refresh_token,
          token_type: tokens.token_type,
          expires_at: expiresAt.toISOString(),
          scope: tokens.scope
        })

      if (createError) {
        throw new Error('Failed to create user account')
      }

      userId = newUserId
    }

    // Create a session for the user
    const { data: session, error: sessionError } = await supabase.auth.admin.createSession({
      user_id: userId,
      expires_in: 3600 // 1 hour
    })

    if (sessionError) {
      throw new Error('Failed to create session')
    }

    // Return success response with session
    const response = {
      success: true,
      user: {
        id: userId,
        email: userInfo.email,
        name: userInfo.name,
        picture: userInfo.picture
      },
      session: session.session,
      message: 'Successfully authenticated with Google'
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
    // Google OAuth login error
    
    const errorResponse = {
      success: false,
      error: error.message,
      message: 'Failed to authenticate with Google'
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