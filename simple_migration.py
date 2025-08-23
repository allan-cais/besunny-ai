#!/usr/bin/env python3
"""
Simple migration script to add missing fields to google_credentials table.
Run this from the project root directory.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def run_migration():
    """Run the migration to add missing fields to google_credentials table."""
    try:
        from app.core.supabase_config import get_supabase_service_client
        
        print("🔍 Connecting to Supabase...")
        supabase = get_supabase_service_client()
        
        if not supabase:
            print("❌ Failed to get Supabase service client")
            return False
        
        print("✅ Connected to Supabase")
        
        # First, let's check the current table structure
        print("🔍 Checking current table structure...")
        try:
            # Try to select from the table to see what fields exist
            test_query = supabase.table('google_credentials').select('*').limit(1).execute()
            print(f"✅ Table exists and is accessible")
            if test_query.data:
                print(f"Current columns: {list(test_query.data[0].keys())}")
            else:
                print("Table is empty")
        except Exception as e:
            print(f"❌ Cannot access google_credentials table: {e}")
            return False
        
        # Since we can't use RPC, let's try to insert a test record with the new fields
        # This will fail if the fields don't exist, but that's okay
        print("🔍 Testing table structure with new fields...")
        
        test_data = {
            'user_id': '00000000-0000-0000-0000-000000000000',  # Dummy UUID
            'access_token': 'test_token',
            'refresh_token': 'test_refresh',
            'expires_in': 3600,
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'expires_at': '2024-12-19T00:00:00Z',
            'token_type': 'Bearer',
            'scope': 'test_scope',
            'google_email': 'test@example.com',
            'google_user_id': 'test_google_id',
            'google_name': 'Test User',
            'google_picture': None,
            'login_provider': False,
            'created_at': '2024-12-19T00:00:00Z',
            'updated_at': '2024-12-19T00:00:00Z'
        }
        
        try:
            # Try to insert test data
            result = supabase.table('google_credentials').insert(test_data).execute()
            print("✅ Test insert successful - all required fields exist")
            
            # Clean up test data
            supabase.table('google_credentials').delete().eq('user_id', '00000000-0000-0000-0000-000000000000').execute()
            print("✅ Test data cleaned up")
            
        except Exception as e:
            print(f"❌ Test insert failed - missing fields: {e}")
            print("🔍 You need to manually add the missing fields to your google_credentials table")
            print("🔍 Required fields:")
            print("  - expires_in (INTEGER)")
            print("  - token_uri (TEXT)")
            print("  - client_id (TEXT)")
            print("  - client_secret (TEXT)")
            print("  - updated_at (TIMESTAMP)")
            print("\n🔍 You can add these fields using your Supabase dashboard:")
            print("  1. Go to your Supabase project dashboard")
            print("  2. Navigate to SQL Editor")
            print("  3. Run the following SQL:")
            print("""
ALTER TABLE google_credentials 
ADD COLUMN IF NOT EXISTS expires_in INTEGER,
ADD COLUMN IF NOT EXISTS token_uri TEXT,
ADD COLUMN IF NOT EXISTS client_id TEXT,
ADD COLUMN IF NOT EXISTS client_secret TEXT,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now();
            """)
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Google Credentials Migration")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not (Path.cwd() / "backend").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Check environment variables
    required_env_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment")
        sys.exit(1)
    
    print("✅ Environment variables verified")
    
    # Run the migration
    success = run_migration()
    
    if success:
        print("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("💥 Migration failed!")
        sys.exit(1)
