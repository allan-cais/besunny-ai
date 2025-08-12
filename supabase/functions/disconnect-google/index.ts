import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Get the authorization header
    const authHeader = req.headers.get('Authorization')
    if (!authHeader) {
      throw new Error('No authorization header')
    }

    // Create Supabase client with service role key
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Verify the JWT token
    const token = authHeader.replace('Bearer ', '')
    const { data: { user }, error: authError } = await supabase.auth.getUser(token)
    
    if (authError || !user) {
      throw new Error('Invalid token')
    }

    // Get user's Google credentials
    const { data: credentials, error: credError } = await supabase
      .from('google_credentials')
      .select('*')
      .eq('user_id', user.id)
      .maybeSingle()

    if (credError) {
      // Database error fetching credentials
      throw new Error('Failed to fetch credentials')
    }

    if (!credentials) {
      return new Response(
        JSON.stringify({
          success: true,
          message: 'No Google credentials found to disconnect'
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200,
        }
      )
    }

    // Revoke the access token at Google
    if (credentials.access_token) {
      try {
        const revokeResponse = await fetch('https://oauth2.googleapis.com/revoke', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams({
            token: credentials.access_token
          }),
        })

        if (!revokeResponse.ok) {
          console.warn('Failed to revoke access token at Google:', await revokeResponse.text())
        } else {
          console.log('Successfully revoked access token at Google')
        }
      } catch (error) {
        console.warn('Error revoking access token:', error)
      }
    }

    // Revoke the refresh token at Google (if it exists)
    if (credentials.refresh_token) {
      try {
        const revokeResponse = await fetch('https://oauth2.googleapis.com/revoke', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams({
            token: credentials.refresh_token
          }),
        })

        if (!revokeResponse.ok) {
          console.warn('Failed to revoke refresh token at Google:', await revokeResponse.text())
        } else {
          console.log('Successfully revoked refresh token at Google')
        }
      } catch (error) {
        console.warn('Error revoking refresh token:', error)
      }
    }

    // Clean up calendar data before deleting credentials
    console.log('Cleaning up calendar data for user:', user.id)
    
    // Stop and delete webhooks
    const { data: webhooks, error: webhookError } = await supabase
      .from('calendar_webhooks')
      .select('*')
      .eq('user_id', user.id)
    
    if (webhookError) {
      console.error('Error fetching webhooks:', webhookError)
    } else if (webhooks && webhooks.length > 0) {
      // Mark webhooks as inactive (we can't stop them without credentials)
      const { error: updateError } = await supabase
        .from('calendar_webhooks')
        .update({ is_active: false })
        .eq('user_id', user.id)
      
      if (updateError) {
        console.error('Error updating webhooks:', updateError)
      } else {
        console.log(`Marked ${webhooks.length} webhooks as inactive`)
      }
    }
    
    // Delete all meetings for this user
    const { data: meetings, error: meetingsError } = await supabase
      .from('meetings')
      .select('id')
      .eq('user_id', user.id)
    
    if (meetingsError) {
      console.error('Error fetching meetings:', meetingsError)
    } else if (meetings && meetings.length > 0) {
      const { error: deleteMeetingsError } = await supabase
        .from('meetings')
        .delete()
        .eq('user_id', user.id)
      
      if (deleteMeetingsError) {
        console.error('Error deleting meetings:', deleteMeetingsError)
      } else {
        console.log(`Deleted ${meetings.length} meetings`)
      }
    }
    
    // Delete sync logs for this user
    const { data: syncLogs, error: syncLogsError } = await supabase
      .from('calendar_sync_logs')
      .select('id')
      .eq('user_id', user.id)
    
    if (syncLogsError) {
      console.error('Error fetching sync logs:', syncLogsError)
    } else if (syncLogs && syncLogs.length > 0) {
      const { error: deleteSyncLogsError } = await supabase
        .from('calendar_sync_logs')
        .delete()
        .eq('user_id', user.id)
      
      if (deleteSyncLogsError) {
        console.error('Error deleting sync logs:', deleteSyncLogsError)
      } else {
        console.log(`Deleted ${syncLogs.length} sync logs`)
      }
    }
    
    // Delete webhooks completely
    const { error: deleteWebhooksError } = await supabase
      .from('calendar_webhooks')
      .delete()
      .eq('user_id', user.id)
    
    if (deleteWebhooksError) {
      console.error('Error deleting webhooks:', deleteWebhooksError)
    } else {
      console.log('Deleted all webhooks')
    }

    // Delete credentials from database
    const { error: deleteError } = await supabase
      .from('google_credentials')
      .delete()
      .eq('user_id', user.id)

    if (deleteError) {
      console.error('Database error deleting credentials:', deleteError)
      throw new Error('Failed to delete credentials from database')
    }

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Successfully disconnected from Google',
        email: credentials.google_email
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    )

  } catch (error) {
    console.error('Edge function error:', error)
    return new Response(
      JSON.stringify({
        error: error.message || 'Internal server error'
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400,
      }
    )
  }
}) 