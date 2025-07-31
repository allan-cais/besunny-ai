import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from '@supabase/supabase-js';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface SetUsernameRequest {
  username: string;
}

interface SetUsernameResponse {
  success: boolean;
  message: string;
  username?: string;
  email_address?: string;
}

function validateUsername(username: string): { valid: boolean; error?: string } {
  if (!username) {
    return { valid: false, error: 'Username is required' };
  }
  
  if (username.length < 3) {
    return { valid: false, error: 'Username must be at least 3 characters long' };
  }
  
  if (username.length > 30) {
    return { valid: false, error: 'Username must be no more than 30 characters long' };
  }
  
  // Only allow alphanumeric characters
  if (!/^[a-zA-Z0-9]+$/.test(username)) {
    return { valid: false, error: 'Username can only contain letters and numbers' };
  }
  
  // Don't allow usernames that start with a number
  if (/^[0-9]/.test(username)) {
    return { valid: false, error: 'Username cannot start with a number' };
  }
  
  return { valid: true };
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    // Validate request method
    if (req.method !== 'POST') {
      throw new Error('Method not allowed');
    }

    // Get and validate authorization header
    const authHeader = req.headers.get('Authorization');
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      throw new Error('Missing or invalid authorization header');
    }

    // Initialize Supabase client with service role key
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
    
    if (!supabaseUrl || !supabaseServiceKey) {
      throw new Error('Server configuration error');
    }

    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Verify the JWT token and get user
    const token = authHeader.replace('Bearer ', '');
    const { data: { user }, error: authError } = await supabase.auth.getUser(token);
    
    if (authError || !user) {
      throw new Error('Invalid or expired token');
    }

    // Parse request body
    const { username }: SetUsernameRequest = await req.json();
    
    if (!username) {
      throw new Error('Username is required');
    }

    // Validate username format
    const validation = validateUsername(username);
    if (!validation.valid) {
      throw new Error(validation.error);
    }

    // Check if user already has a username
    const { data: existingUser, error: userError } = await supabase
      .from('users')
      .select('username')
      .eq('id', user.id)
      .single();

    if (userError) {
      throw new Error('Failed to fetch user data');
    }

    if (existingUser?.username) {
      throw new Error('Username has already been set and cannot be changed');
    }

    // Set the username using the database function
    const { data: success, error: setError } = await supabase
      .rpc('set_user_username', {
        user_uuid: user.id,
        new_username: username
      });

    if (setError) {
      throw new Error(`Failed to set username: ${setError.message}`);
    }

    if (!success) {
      throw new Error('Username is already taken');
    }

    // Construct the virtual email address
    const virtualEmailAddress = `ai+${username}@besunny.ai`;

    const response: SetUsernameResponse = {
      success: true,
      message: 'Username set successfully',
      username: username,
      email_address: virtualEmailAddress
    };

    return new Response(
      JSON.stringify(response),
      {
        status: 200,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );

  } catch (error) {
    console.error('Set username error:', error);
    
    const errorResponse: SetUsernameResponse = {
      success: false,
      message: error.message || 'Failed to set username'
    };

    return new Response(
      JSON.stringify(errorResponse),
      {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );
  }
}); 