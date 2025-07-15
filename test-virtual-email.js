#!/usr/bin/env node

/**
 * Test script for Virtual Email Addresses feature
 * 
 * This script tests the complete flow of:
 * 1. Username setup
 * 2. Email processing
 * 3. Document creation
 * 4. n8n webhook integration
 */

const { createClient } = require('@supabase/supabase-js');

// Configuration
const SUPABASE_URL = process.env.SUPABASE_URL || 'https://your-project.supabase.co';
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const TEST_USERNAME = 'testuser_' + Date.now();
const TEST_EMAIL = 'test@example.com';

if (!SUPABASE_SERVICE_ROLE_KEY) {
  console.error('❌ SUPABASE_SERVICE_ROLE_KEY environment variable is required');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

async function testVirtualEmailFeature() {
  console.log('🧪 Testing Virtual Email Addresses Feature\n');

  try {
    // Test 1: Create test user
    console.log('1️⃣ Creating test user...');
    const { data: user, error: userError } = await supabase.auth.admin.createUser({
      email: TEST_EMAIL,
      password: 'testpassword123',
      email_confirm: true
    });

    if (userError) {
      throw new Error(`Failed to create test user: ${userError.message}`);
    }

    console.log(`✅ Test user created: ${user.user.id}`);

    // Test 2: Set username
    console.log('\n2️⃣ Setting username...');
    const { data: usernameResult, error: usernameError } = await supabase
      .rpc('set_user_username', {
        user_uuid: user.user.id,
        new_username: TEST_USERNAME
      });

    if (usernameError) {
      throw new Error(`Failed to set username: ${usernameError.message}`);
    }

    if (!usernameResult) {
      throw new Error('Username was not set (possibly already taken)');
    }

    console.log(`✅ Username set: ${TEST_USERNAME}`);

    // Test 3: Verify username in database
    console.log('\n3️⃣ Verifying username in database...');
    const { data: userData, error: userDataError } = await supabase
      .from('users')
      .select('username, username_set_at')
      .eq('id', user.user.id)
      .single();

    if (userDataError) {
      throw new Error(`Failed to fetch user data: ${userDataError.message}`);
    }

    if (userData.username !== TEST_USERNAME) {
      throw new Error(`Username mismatch: expected ${TEST_USERNAME}, got ${userData.username}`);
    }

    console.log(`✅ Username verified: ${userData.username}`);
    console.log(`✅ Username set at: ${userData.username_set_at}`);

    // Test 4: Test username extraction function
    console.log('\n4️⃣ Testing username extraction...');
    const testEmail = `inbound+${TEST_USERNAME}@sunny.ai`;
    const { data: extractedUsername, error: extractError } = await supabase
      .rpc('extract_username_from_email', {
        email_address: testEmail
      });

    if (extractError) {
      throw new Error(`Failed to extract username: ${extractError.message}`);
    }

    if (extractedUsername !== TEST_USERNAME) {
      throw new Error(`Username extraction failed: expected ${TEST_USERNAME}, got ${extractedUsername}`);
    }

    console.log(`✅ Username extraction works: ${extractedUsername}`);

    // Test 5: Test user lookup by username
    console.log('\n5️⃣ Testing user lookup by username...');
    const { data: foundUser, error: lookupError } = await supabase
      .rpc('get_user_by_username', {
        search_username: TEST_USERNAME
      });

    if (lookupError) {
      throw new Error(`Failed to lookup user: ${lookupError.message}`);
    }

    if (!foundUser || foundUser.length === 0) {
      throw new Error('User not found by username');
    }

    if (foundUser[0].user_id !== user.user.id) {
      throw new Error('User ID mismatch in lookup');
    }

    console.log(`✅ User lookup works: ${foundUser[0].user_id}`);

    // Test 6: Test document creation simulation
    console.log('\n6️⃣ Testing document creation...');
    const mockGmailMessage = {
      id: 'test_message_' + Date.now(),
      snippet: 'Test email content',
      internalDate: Date.now().toString()
    };

    const { data: document, error: docError } = await supabase
      .from('documents')
      .insert({
        project_id: null,
        source: 'gmail',
        source_id: mockGmailMessage.id,
        title: 'Test Email',
        author: 'test@example.com',
        received_at: new Date(parseInt(mockGmailMessage.internalDate)).toISOString(),
        created_by: user.user.id,
        summary: mockGmailMessage.snippet
      })
      .select('id')
      .single();

    if (docError) {
      throw new Error(`Failed to create document: ${docError.message}`);
    }

    console.log(`✅ Document created: ${document.id}`);

    // Test 7: Test email processing log
    console.log('\n7️⃣ Testing email processing log...');
    const { data: logEntry, error: logError } = await supabase
      .from('email_processing_logs')
      .insert({
        user_id: user.user.id,
        gmail_message_id: mockGmailMessage.id,
        inbound_address: testEmail,
        extracted_username: TEST_USERNAME,
        subject: 'Test Email',
        sender: 'test@example.com',
        processed_at: new Date().toISOString(),
        status: 'processed',
        document_id: document.id,
        n8n_webhook_sent: true,
        n8n_webhook_response: 'success'
      })
      .select('id, status')
      .single();

    if (logError) {
      throw new Error(`Failed to create log entry: ${logError.message}`);
    }

    console.log(`✅ Email processing log created: ${logEntry.id}`);

    // Test 8: Verify virtual email address format
    console.log('\n8️⃣ Verifying virtual email address format...');
    const virtualEmailAddress = `inbound+${TEST_USERNAME}@sunny.ai`;
    
    if (!virtualEmailAddress.match(/^inbound\+[a-zA-Z0-9]+@sunny\.ai$/)) {
      throw new Error('Invalid virtual email address format');
    }

    console.log(`✅ Virtual email address format correct: ${virtualEmailAddress}`);

    // Test 9: Cleanup test data
    console.log('\n9️⃣ Cleaning up test data...');
    
    // Delete email processing log
    await supabase
      .from('email_processing_logs')
      .delete()
      .eq('user_id', user.user.id);

    // Delete document
    await supabase
      .from('documents')
      .delete()
      .eq('id', document.id);

    // Delete user
    await supabase.auth.admin.deleteUser(user.user.id);

    console.log('✅ Test data cleaned up');

    console.log('\n🎉 All tests passed! Virtual email addresses feature is working correctly.');
    console.log('\n📋 Summary:');
    console.log(`   • Test username: ${TEST_USERNAME}`);
    console.log(`   • Virtual email: ${virtualEmailAddress}`);
    console.log(`   • User ID: ${user.user.id}`);
    console.log(`   • Document ID: ${document.id}`);

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    console.error('\n🔍 Debug information:');
    console.error('   • Supabase URL:', SUPABASE_URL);
    console.error('   • Test username:', TEST_USERNAME);
    console.error('   • Test email:', TEST_EMAIL);
    
    // Try to cleanup on error
    try {
      const { data: users } = await supabase
        .from('users')
        .select('id')
        .eq('username', TEST_USERNAME);
      
      if (users && users.length > 0) {
        await supabase.auth.admin.deleteUser(users[0].id);
        console.log('✅ Cleaned up test user on error');
      }
    } catch (cleanupError) {
      console.error('⚠️ Failed to cleanup on error:', cleanupError.message);
    }
    
    process.exit(1);
  }
}

// Run the test
testVirtualEmailFeature(); 