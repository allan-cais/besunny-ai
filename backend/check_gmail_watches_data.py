#!/usr/bin/env python3
"""
Check gmail_watches table data
This script will help identify why the 406 error is occurring
"""

import asyncio
from dotenv import load_dotenv
load_dotenv()

async def check_gmail_watches_data():
    """Check what's in the gmail_watches table."""
    print("🔍 Checking gmail_watches table data...")
    
    try:
        from app.core.supabase_config import get_supabase_client
        
        # Get Supabase client
        supabase = get_supabase_client()
        if not supabase:
            print("❌ Failed to get Supabase client")
            return
        
        print("✅ Supabase client connected")
        
        # Check if gmail_watches table has any data
        print("\n1️⃣ Checking gmail_watches table data...")
        try:
            result = supabase.table("gmail_watches").select("*").execute()
            total_records = len(result.data) if result.data else 0
            
            print(f"   Total records: {total_records}")
            
            if result.data:
                print("   Sample data:")
                for record in result.data[:3]:
                    print(f"     - ID: {record.get('id', 'N/A')[:8] if record.get('id') else 'N/A'}...")
                    print(f"       Email: {record.get('user_email', 'N/A')}")
                    print(f"       Active: {record.get('is_active', 'N/A')}")
                    print(f"       Expiration: {record.get('expiration', 'N/A')}")
                    print()
            else:
                print("   ❌ No records found in gmail_watches table")
                
        except Exception as e:
            print(f"   ❌ Error accessing gmail_watches: {e}")
        
        # Check if there are any records for the specific email
        print("\n2️⃣ Checking for specific email...")
        try:
            test_email = "allan@customaistudio.io"
            result = supabase.table("gmail_watches") \
                .select("*") \
                .eq("user_email", test_email) \
                .execute()
            
            if result.data:
                print(f"   ✅ Found {len(result.data)} records for {test_email}")
                for record in result.data:
                    print(f"     - ID: {record.get('id', 'N/A')}")
                    print(f"       Active: {record.get('is_active', 'N/A')}")
                    print(f"       Expiration: {record.get('expiration', 'N/A')}")
            else:
                print(f"   ❌ No records found for {test_email}")
                
        except Exception as e:
            print(f"   ❌ Error checking specific email: {e}")
        
        # Check if the user has Google credentials
        print("\n3️⃣ Checking Google credentials...")
        try:
            # This would require user authentication, but let's check if table exists
            result = supabase.table("google_credentials").select("id").limit(1).execute()
            print(f"   ✅ google_credentials table accessible")
            
            # Count total records
            count_result = supabase.table("google_credentials").select("id", count="exact").execute()
            total_creds = count_result.count if hasattr(count_result, 'count') else 'Unknown'
            print(f"   Total credentials: {total_creds}")
            
        except Exception as e:
            print(f"   ❌ Error accessing google_credentials: {e}")
        
        # Test the exact query that's failing
        print("\n4️⃣ Testing the exact failing query...")
        try:
            # Simulate the exact query from the frontend
            result = supabase.table("gmail_watches") \
                .select("id, is_active, expiration, history_id") \
                .eq("user_email", "allan@customaistudio.io") \
                .eq("is_active", True) \
                .execute()
            
            print(f"   ✅ Query successful: {len(result.data)} records returned")
            if result.data:
                for record in result.data:
                    print(f"     - {record}")
            else:
                print("   ℹ️  No active gmail watches found for this user")
                
        except Exception as e:
            print(f"   ❌ Query failed: {e}")
            print(f"      Error type: {type(e).__name__}")
            print(f"      Error details: {str(e)}")
        
        print("\n🔍 Check complete!")
        
    except Exception as e:
        print(f"\n❌ Check failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_gmail_watches_data())
