// Script to sync mock data to the documents table
// This script will create document records for the mock data used in the frontend

import { createClient } from '@supabase/supabase-js';
import { config } from 'dotenv';
import crypto from 'crypto';

// Load environment variables
config();

// Initialize Supabase client
const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('Missing required environment variables: VITE_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseServiceKey);

// Mock data from the frontend
const mockDocuments = [
  {
    id: crypto.randomUUID(),
    project_id: '550e8400-e29b-41d4-a716-446655440000',
    type: 'email',
    title: 'Q1 Budget Review Meeting',
    summary: 'Hi team, please find attached the Q1 budget review document that we\'ll be discussing in tomorrow\'s meeting. I\'ve also included the agenda and previous quarter comparisons.',
    source: 'email',
    author: 'sarah@company.com',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    status: 'active'
  },
  {
    id: crypto.randomUUID(),
    project_id: '550e8400-e29b-41d4-a716-446655440000',
    type: 'spreadsheet',
    title: 'Q1 Budget Review.xlsx',
    summary: 'Comprehensive budget analysis for Q1 2025 including revenue projections, expense tracking, and variance analysis.',
    source: 'google_drive',
    author: 'Finance Team',
    created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    status: 'active'
  },
  {
    id: crypto.randomUUID(),
    project_id: '550e8400-e29b-41d4-a716-446655440000',
    type: 'document',
    title: 'Product Roadmap 2025',
    summary: 'This document outlines our product vision and planned feature releases for the next 12 months, including timelines and resource allocation.',
    source: 'google_drive',
    author: 'Product Team',
    created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    status: 'active'
  },
  {
    id: crypto.randomUUID(),
    type: 'email',
    title: 'Client Feedback on Beta Release',
    summary: 'The client has provided some valuable feedback on the beta release which we should incorporate before the final launch. Key points include UI improvements and performance optimizations.',
    source: 'email',
    author: 'client@example.com',
    created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    status: 'active'
    // No project_id - needs classification
  },
  {
    id: crypto.randomUUID(),
    project_id: '550e8400-e29b-41d4-a716-446655440000',
    type: 'folder',
    title: 'Marketing Campaign Assets',
    summary: 'Collection of images, copy, and design files for our upcoming social media campaign. Please review and provide feedback.',
    source: 'google_drive',
    author: 'Marketing Team',
    created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    status: 'active'
  },
  {
    id: crypto.randomUUID(),
    type: 'presentation',
    title: 'Board Meeting Presentation',
    summary: 'Quarterly board meeting presentation covering financial results, strategic initiatives, and upcoming milestones.',
    source: 'google_drive',
    author: 'Executive Team',
    created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    status: 'active'
    // No project_id - needs classification
  }
];

// Mock transcript data
const mockTranscripts = [
  {
    id: crypto.randomUUID(),
    project_id: '550e8400-e29b-41d4-a716-446655440000',
    type: 'meeting_transcript',
    title: 'Meeting Transcript: Q1 Budget Review Meeting',
    summary: 'Discussion covered Q1 budget performance, revenue projections for Q2, and strategic planning for the upcoming quarter. Key decisions made on resource allocation and new project funding.',
    source: 'attendee_bot',
    author: 'Meeting Attendee Bot',
    created_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    status: 'active'
  },
  {
    id: crypto.randomUUID(),
    project_id: '550e8400-e29b-41d4-a716-446655440000',
    type: 'meeting_transcript',
    title: 'Meeting Transcript: Product Strategy Session',
    summary: 'Deep dive into product roadmap planning, feature prioritization, and technical architecture decisions. Team discussed user feedback integration and development timeline adjustments.',
    source: 'attendee_bot',
    author: 'Meeting Attendee Bot',
    created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    status: 'active'
  }
];

async function syncMockData() {
  console.log('🚀 Starting mock data sync to documents table...');

  try {
    // First, check for existing users
    let { data: users, error: usersError } = await supabase
      .from('users')
      .select('id, email')
      .limit(1);

    if (usersError) {
      console.error('Error checking for users:', usersError);
      return;
    }

    let userId;
    if (!users || users.length === 0) {
      console.log('📝 Creating mock user...');
      const { data: newUser, error: createUserError } = await supabase
        .from('users')
        .insert({
          id: '550e8400-e29b-41d4-a716-446655440009',
          email: 'mock@example.com',
          name: 'Mock User',
          role: 'user'
        })
        .select('id')
        .single();

      if (createUserError) {
        console.error('Error creating mock user:', createUserError);
        return;
      }
      userId = newUser.id;
      console.log('✅ Mock user created');
    } else {
      userId = users[0].id;
      console.log(`✅ Using existing user: ${users[0].email}`);
    }

    // Check if we have a mock project
    let { data: projects, error: projectsError } = await supabase
      .from('projects')
      .select('id')
      .eq('id', '550e8400-e29b-41d4-a716-446655440000');

    if (projectsError) {
      console.error('Error checking for mock project:', projectsError);
      return;
    }

    // Create mock project if it doesn't exist
    if (!projects || projects.length === 0) {
      console.log('📝 Creating mock project...');
      const { error: createProjectError } = await supabase
        .from('projects')
        .insert({
          id: '550e8400-e29b-41d4-a716-446655440000',
          name: 'Summer',
          description: 'Mock project for demonstration',
          status: 'active',
          created_by: userId
        });

      if (createProjectError) {
        console.error('Error creating mock project:', createProjectError);
        return;
      }
      console.log('✅ Mock project created');
    }

    // Combine all mock data
    const allMockData = [...mockDocuments, ...mockTranscripts];

    // Check which documents already exist
    const existingIds = allMockData.map(doc => doc.id);
    const { data: existingDocs, error: checkError } = await supabase
      .from('documents')
      .select('id')
      .in('id', existingIds);

    if (checkError) {
      console.error('Error checking existing documents:', checkError);
      return;
    }

    const existingDocIds = existingDocs?.map(doc => doc.id) || [];
    const newDocs = allMockData.filter(doc => !existingDocIds.includes(doc.id));

    if (newDocs.length === 0) {
      console.log('✅ All mock documents already exist in the database');
      return;
    }

    console.log(`📝 Inserting ${newDocs.length} new mock documents...`);

    // Insert new documents
    const { data: insertedDocs, error: insertError } = await supabase
      .from('documents')
      .insert(newDocs)
      .select('id, title, type');

    if (insertError) {
      console.error('Error inserting mock documents:', insertError);
      return;
    }

    console.log('✅ Successfully inserted mock documents:');
    insertedDocs?.forEach(doc => {
      console.log(`  - ${doc.title} (${doc.type})`);
    });

    console.log('🎉 Mock data sync completed successfully!');

  } catch (error) {
    console.error('❌ Error during mock data sync:', error);
  }
}

// Run the sync
syncMockData().then(() => {
  console.log('🏁 Sync script finished');
  process.exit(0);
}).catch(error => {
  console.error('💥 Sync script failed:', error);
  process.exit(1);
}); 