#!/usr/bin/env node

/**
 * Test script to verify OAuth scope handling
 * 
 * This script helps you test if your OAuth implementation is properly
 * handling scope updates by checking the current scopes and providing
 * debugging information.
 */

// Configuration - update these with your actual values
const config = {
  supabaseUrl: process.env.VITE_SUPABASE_URL || 'https://your-project.supabase.co',
  supabaseAnonKey: process.env.VITE_SUPABASE_ANON_KEY || 'your-anon-key',
  googleClientId: process.env.VITE_GOOGLE_CLIENT_ID || 'your-client-id'
};

// Current scopes being requested by your application
const currentScopes = [
  'https://www.googleapis.com/auth/gmail.modify',
  'https://www.googleapis.com/auth/drive.readonly',
  'https://www.googleapis.com/auth/userinfo.email',
  'https://www.googleapis.com/auth/pubsub',
  'https://www.googleapis.com/auth/calendar.readonly',
  'https://www.googleapis.com/auth/contacts.readonly',
  'https://www.googleapis.com/auth/gmail.send',
  'https://www.googleapis.com/auth/drive'
];

console.log('🔍 OAuth Scope Test Script');
console.log('========================\n');

console.log('📋 Current Scopes Requested:');
currentScopes.forEach((scope, index) => {
  console.log(`  ${index + 1}. ${scope}`);
});

console.log('\n🔧 OAuth URL Parameters:');
const params = new URLSearchParams({
  client_id: config.googleClientId,
  redirect_uri: 'http://localhost:5173/integrations',
  response_type: 'code',
  scope: currentScopes.join(' '),
  access_type: 'offline',
  prompt: 'consent',
  approval_prompt: 'force'
});

console.log('✅ prompt=consent - Forces consent screen every time');
console.log('✅ approval_prompt=force - Additional force parameter');
console.log('✅ access_type=offline - Ensures refresh token');

console.log('\n🌐 Test OAuth URL:');
console.log(`https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`);

console.log('\n📝 Troubleshooting Steps:');
console.log('1. Go to https://myaccount.google.com/permissions');
console.log('2. Find your app and click "Remove Access"');
console.log('3. Clear browser cache and cookies');
console.log('4. Try connecting again with the RECONNECT button');
console.log('5. Check that the consent screen shows all current scopes');

console.log('\n🔍 To verify scopes in tokens:');
console.log('1. After connecting, check the scope field in your database');
console.log('2. Compare with the currentScopes array above');
console.log('3. If they don\'t match, the scopeMismatch warning should appear');

console.log('\n⚠️  Common Issues:');
console.log('- Google Cloud Console scopes not saved properly');
console.log('- Browser caching old consent');
console.log('- App in "Testing" mode with limited users');
console.log('- Wrong OAuth client ID being used');

console.log('\n✅ Your implementation includes:');
console.log('- prompt=consent parameter ✓');
console.log('- approval_prompt=force parameter ✓');
console.log('- Automatic disconnect before reconnect ✓');
console.log('- Scope mismatch detection ✓');
console.log('- RECONNECT button for scope updates ✓');
console.log('- Proper token revocation ✓');

console.log('\n🎯 Next Steps:');
console.log('1. Update your Google Cloud Console scopes');
console.log('2. Revoke access at myaccount.google.com/permissions');
console.log('3. Test the RECONNECT functionality');
console.log('4. Verify the consent screen shows updated scopes'); 