import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from '@supabase/supabase-js';
import OpenAI from 'openai';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface ProjectOnboardingRequest {
  project_id: string;
  user_id: string;
  summary: {
    project_name: string;
    overview: string;
    keywords: string[];
    deliverables: string;
    contacts: {
      internal_lead: string;
      agency_lead: string;
      client_lead: string;
    };
    shoot_date: string;
    location: string;
    references: string;
  };
}

interface ProjectMetadata {
  id: string;
  created_by: string;
  name: string;
  description: string;
  status: string;
  notes: string;
  normalized_tags: string[];
  categories: string[];
  reference_keywords: string[];
  entity_patterns: any;
  classification_signals: any;
  pinecone_document_count: number;
  last_classification_at: string | null;
  classification_feedback: any;
  created_at: string;
  updated_at: string;
}

interface ProjectOnboardingResponse {
  success: boolean;
  message: string;
  metadata?: ProjectMetadata;
  error?: string;
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
    const { project_id, user_id, summary }: ProjectOnboardingRequest = await req.json();
    
    if (!project_id || !user_id || !summary) {
      throw new Error('Missing required fields: project_id, user_id, summary');
    }

    // Initialize OpenAI client
    const openaiApiKey = Deno.env.get('OPENAI_API_KEY');
    if (!openaiApiKey) {
      throw new Error('OpenAI API key not configured');
    }

    const openai = new OpenAI({
      apiKey: openaiApiKey,
    });

    // Prepare the prompt for OpenAI
    const prompt = `You are an intelligent assistant helping structure project metadata from user-submitted onboarding summaries. The goal is to output a complete and consistent metadata object for the new project. This data will be saved to a database and used by downstream AI classification agents for matching new documents to the correct project.

**CRITICAL: You must return ONLY a valid JSON object with the exact structure specified below. Do not include any explanatory text, markdown, or other formatting.**

**Input Data:**
Project ID: ${project_id}
User ID: ${user_id}
Project Name: ${summary.project_name}
Overview: ${summary.overview}
Keywords: ${summary.keywords.join(', ')}
Deliverables: ${summary.deliverables}
Internal Lead: ${summary.contacts.internal_lead}
Agency Lead: ${summary.contacts.agency_lead}
Client Lead: ${summary.contacts.client_lead}
Shoot Date: ${summary.shoot_date}
Location: ${summary.location}
References: ${summary.references}

**Required Output Format (return ONLY this JSON structure):**
{
  "id": "${project_id}",
  "created_by": "${user_id}",
  "name": "[extract from project_name]",
  "description": "[combine overview and deliverables into a comprehensive project description]",
  "status": "in_progress",
  "notes": "[comprehensive project overview combining overview, deliverables, dates, location, and contacts - this should be the main project summary]",
  "normalized_tags": [
    "[convert keywords to snake_case, lowercased]"
  ],
  "categories": [
    "[infer high-level categories like 'Video Production', 'Marketing', etc.]"
  ],
  "reference_keywords": [
    "[extract key terms from deliverables and content]"
  ],
  "entity_patterns": {
    "people": {
      "[internal_lead]": { "role": "internal_lead" },
      "[agency_lead]": { "role": "agency_lead" },
      "[client_lead]": { "role": "client_lead" }
    },
    "locations": ["[extract location components]"],
    "domains": [],
    "project_codes": []
  },
  "classification_signals": {
    "temporal_relevance": {
      "active_period": ["[start_date]", "[end_date]"]
    },
    "content_types": ["[extract from deliverables]"],
    "confidence_thresholds": {
      "email": { "subject_match": 0.7, "content_match": 0.6 },
      "gdrive": { "filename_match": 0.8, "content_match": 0.6 }
    }
  },
  "pinecone_document_count": 0,
  "last_classification_at": null,
  "classification_feedback": null,
  "created_at": "[current_timestamp]",
  "updated_at": "[current_timestamp]"
}

**Instructions:**
1. Convert keywords to snake_case for normalized_tags (these are for classification)
2. Extract key terms from deliverables ONLY for reference_keywords (these are the actual deliverables)
3. Parse location into components for entity_patterns.locations
4. Infer categories based on project type and deliverables
5. Create comprehensive notes combining all relevant information
6. Set temporal_relevance based on shoot dates
7. Extract content_types from deliverables
8. Use exact UUIDs provided for id and created_by
9. Return ONLY the JSON object, no other text`;

    // Call OpenAI API
    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content: "You are a JSON-only assistant. You must return ONLY valid JSON objects with no additional text, markdown, or formatting. Never include explanations, comments, or any text outside the JSON structure."
        },
        {
          role: "user",
          content: prompt
        }
      ],
      temperature: 0.1,
      max_tokens: 2000,
    });

    const aiResponse = completion.choices[0]?.message?.content;
    if (!aiResponse) {
      throw new Error('No response from OpenAI');
    }

    // Parse the AI response
    let metadata: ProjectMetadata;
    try {
      // Extract JSON from the response (in case there's extra text)
      const jsonMatch = aiResponse.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new Error('No JSON found in AI response');
      }
      
      metadata = JSON.parse(jsonMatch[0]);
    } catch (parseError) {
      console.error('Failed to parse AI response:', aiResponse);
      throw new Error('Invalid JSON response from AI');
    }

    // Validate required fields
    if (!metadata.id || !metadata.name) {
      throw new Error('AI response missing required fields');
    }

    // Update the project in the database with the AI-generated metadata
    const { error: updateError } = await supabase
      .from('projects')
      .update({
        name: metadata.name,
        description: metadata.description,
        status: metadata.status || 'in_progress',
        notes: metadata.notes,
        normalized_tags: metadata.normalized_tags,
        categories: metadata.categories,
        reference_keywords: metadata.reference_keywords,
        entity_patterns: metadata.entity_patterns,
        classification_signals: metadata.classification_signals,
        pinecone_document_count: metadata.pinecone_document_count || 0,
        last_classification_at: metadata.last_classification_at,
        classification_feedback: metadata.classification_feedback,
        updated_at: new Date().toISOString()
      })
      .eq('id', project_id);

    if (updateError) {
      console.error('Database update error:', updateError);
      throw new Error('Failed to update project metadata');
    }

    // Also insert into project_metadata table if it exists
    try {
      const { error: metadataError } = await supabase
        .from('project_metadata')
        .upsert({
          project_id: project_id,
          normalized_tags: metadata.normalized_tags,
          categories: metadata.categories,
          reference_keywords: metadata.reference_keywords,
          notes: metadata.notes
        });

      if (metadataError) {
        console.warn('Project metadata table insert failed:', metadataError);
        // Don't throw error - this table might not exist in all environments
      }
    } catch (metadataError) {
      console.warn('Project metadata table not available:', metadataError);
    }

    const response: ProjectOnboardingResponse = {
      success: true,
      message: 'Project metadata processed successfully',
      metadata: {
        ...metadata,
        id: project_id,
        created_by: user_id,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
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
    console.error('Project onboarding AI error:', error);
    
    const errorResponse: ProjectOnboardingResponse = {
      success: false,
      message: error.message || 'Failed to process project onboarding',
      error: error.message
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