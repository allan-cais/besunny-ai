#!/usr/bin/env python3
"""
Convert Google service account JSON key to base64 for Railway deployment.
This allows you to store the credentials as an environment variable instead of a file.
"""

import base64
import json
import sys
from pathlib import Path

def convert_key_to_base64(key_file_path: str) -> str:
    """Convert a JSON service account key file to base64."""
    try:
        # Read the JSON file
        with open(key_file_path, 'r') as f:
            key_data = f.read()
        
        # Validate it's valid JSON
        json.loads(key_data)
        
        # Convert to base64
        key_base64 = base64.b64encode(key_data.encode('utf-8')).decode('utf-8')
        
        return key_base64
        
    except FileNotFoundError:
        print(f"❌ Error: File '{key_file_path}' not found")
        return None
    except json.JSONDecodeError:
        print(f"❌ Error: File '{key_file_path}' is not valid JSON")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Main function."""
    print("🔑 Google Service Account Key Converter")
    print("=" * 40)
    
    # Default key file path
    default_key_path = "service-account-key.json"
    
    if len(sys.argv) > 1:
        key_file_path = sys.argv[1]
    else:
        key_file_path = input(f"Enter path to service account key file (default: {default_key_path}): ").strip()
        if not key_file_path:
            key_file_path = default_key_path
    
    # Check if file exists
    if not Path(key_file_path).exists():
        print(f"❌ File '{key_file_path}' not found!")
        print(f"Make sure you've downloaded the service account key and placed it in the backend directory.")
        return
    
    print(f"📁 Converting key file: {key_file_path}")
    
    # Convert to base64
    key_base64 = convert_key_to_base64(key_file_path)
    
    if key_base64:
        print("✅ Conversion successful!")
        print("\n📋 Add this to your Railway environment variables:")
        print("=" * 50)
        print(f"GOOGLE_SERVICE_ACCOUNT_KEY_BASE64={key_base64}")
        print("=" * 50)
        
        print("\n📝 Also add these other required variables:")
        print(f"GOOGLE_PROJECT_ID=your-project-id")
        print(f"WEBHOOK_BASE_URL=https://your-railway-app.railway.app")
        
        print("\n🔒 Security Note: Keep this base64 string secure and don't share it!")
        
        # Save to a file for easy copying
        output_file = "railway-env-vars.txt"
        with open(output_file, 'w') as f:
            f.write(f"GOOGLE_SERVICE_ACCOUNT_KEY_BASE64={key_base64}\n")
            f.write(f"GOOGLE_PROJECT_ID=your-project-id\n")
            f.write(f"WEBHOOK_BASE_URL=https://your-railway-app.railway.app\n")
        
        print(f"\n💾 Environment variables saved to: {output_file}")
        
    else:
        print("❌ Conversion failed. Please check the file and try again.")

if __name__ == "__main__":
    main()
