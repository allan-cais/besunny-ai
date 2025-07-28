// Script to check documents in the database and create unclassified ones for testing
import { createClient } from '@supabase/supabase-js';
import { config } from 'dotenv';
import crypto from 'crypto';

// Load environment variables
config();

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('Missing required environment variables');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseServiceKey);

async function checkDocuments() {
  console.log('🔍 Checking documents in database...');

  // Get all documents
  const { data: allDocs, error: allDocsError } = await supabase
    .from('documents')
    .select('id, project_id, title, type, created_at')
    .order('created_at', { ascending: false });

  if (allDocsError) {
    console.error('Error fetching documents:', allDocsError);
    return;
  }

  console.log(`📊 Total documents in database: ${allDocs.length}`);

  // Analyze project_id distribution
  const projectIdCounts = allDocs.reduce((acc, doc) => {
    const key = doc.project_id || 'null';
    if (!acc[key]) {
      acc[key] = { count: 0, titles: [] };
    }
    acc[key].count++;
    acc[key].titles.push(doc.title);
    return acc;
  }, {});

  console.log('📈 Project ID distribution:');
  Object.entries(projectIdCounts).forEach(([projectId, data]) => {
    console.log(`  ${projectId}: ${data.count} documents`);
    console.log(`    Sample titles: ${data.titles.slice(0, 3).join(', ')}`);
  });

  // Check for unclassified documents
  const unclassified = allDocs.filter(doc => !doc.project_id);
  console.log(`\n🔍 Unclassified documents (no project_id): ${unclassified.length}`);
  
  if (unclassified.length > 0) {
    console.log('Unclassified document titles:');
    unclassified.forEach(doc => {
      console.log(`  - ${doc.title} (${doc.type})`);
    });
  } else {
    console.log('No unclassified documents found. Creating some for testing...');
    
    // Create some unclassified documents for testing
    const testUnclassifiedDocs = [
      {
        id: crypto.randomUUID(),
        type: 'email',
        title: 'Test Unclassified Email',
        summary: 'This is a test unclassified email for testing the /data page functionality.',
        source: 'email',
        author: 'test@example.com',
        created_at: new Date().toISOString(),
        status: 'active'
        // No project_id - intentionally unclassified
      },
      {
        id: crypto.randomUUID(),
        type: 'document',
        title: 'Test Unclassified Document',
        summary: 'This is a test unclassified document for testing the /data page functionality.',
        source: 'google_drive',
        author: 'Test User',
        created_at: new Date().toISOString(),
        status: 'active'
        // No project_id - intentionally unclassified
      }
    ];

    const { data: insertedDocs, error: insertError } = await supabase
      .from('documents')
      .insert(testUnclassifiedDocs)
      .select('id, title, project_id');

    if (insertError) {
      console.error('Error creating test unclassified documents:', insertError);
    } else {
      console.log('✅ Created test unclassified documents:', insertedDocs);
    }
  }
}

checkDocuments().catch(console.error); 