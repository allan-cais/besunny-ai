#!/usr/bin/env python3
"""
Script to run the database migration for adding missing fields to google_credentials table.
This script should be run from the backend directory with proper environment variables set.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

async def run_migration():
    """Run the migration to add missing fields to google_credentials table."""
    try:
        from app.core.supabase_config import get_supabase_service_client
        
        print("🔍 Connecting to Supabase...")
        supabase = get_supabase_service_client()
        
        if not supabase:
            print("❌ Failed to get Supabase service client")
            return False
        
        print("✅ Connected to Supabase")
        
        # Migration SQL
        migration_sql = """
        -- Add missing fields to google_credentials table
        ALTER TABLE google_credentials 
        ADD COLUMN IF NOT EXISTS expires_in INTEGER,
        ADD COLUMN IF NOT EXISTS token_uri TEXT,
        ADD COLUMN IF NOT EXISTS client_id TEXT,
        ADD COLUMN IF NOT EXISTS client_secret TEXT,
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now();
        
        -- Add comment explaining the new fields
        COMMENT ON COLUMN google_credentials.expires_in IS 'Token expiration time in seconds';
        COMMENT ON COLUMN google_credentials.token_uri IS 'Google OAuth token endpoint URI';
        COMMENT ON COLUMN google_credentials.client_id IS 'Google OAuth client ID';
        COMMENT ON COLUMN google_credentials.client_secret IS 'Google OAuth client secret';
        COMMENT ON COLUMN google_credentials.updated_at IS 'Last update timestamp';
        
        -- Create index on updated_at for efficient queries
        CREATE INDEX IF NOT EXISTS idx_google_credentials_updated_at ON google_credentials(updated_at);
        
        -- Update existing records to set updated_at to created_at if it's null
        UPDATE google_credentials 
        SET updated_at = created_at 
        WHERE updated_at IS NULL;
        """
        
        print("🔍 Running migration...")
        
        # Execute the migration
        result = supabase.rpc('exec_sql', {'sql': migration_sql}).execute()
        
        print("✅ Migration completed successfully!")
        print(f"Result: {result}")
        
        # Verify the migration by checking table structure
        print("🔍 Verifying table structure...")
        table_info = supabase.table('google_credentials').select('*').limit(1).execute()
        
        if table_info.data is not None:
            print("✅ Table structure verified")
            print(f"Columns: {list(table_info.data[0].keys()) if table_info.data else 'No data'}")
        else:
            print("⚠️  Could not verify table structure")
        
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
    success = asyncio.run(run_migration())
    
    if success:
        print("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("💥 Migration failed!")
        sys.exit(1)
