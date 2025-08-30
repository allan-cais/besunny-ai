#!/usr/bin/env python3
"""
Script to fix property name mismatches in the codebase.
Fixes 'access_token' vs 'accessToken' inconsistencies that cause 401 errors.
"""

import os
import re
import glob
from pathlib import Path

def fix_property_names_in_file(file_path):
    """Fix property name mismatches in a single file."""
    print(f"Processing: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix credentials.access_token -> credentials.accessToken
        content = re.sub(
            r'(\bcredentials\.)access_token(\b)',
            r'\1accessToken\2',
            content
        )
        
        # Fix refreshedCredentials.access_token -> refreshedCredentials.accessToken
        content = re.sub(
            r'(\brefreshedCredentials\.)access_token(\b)',
            r'\1accessToken\2',
            content
        )
        
        # Fix any other .access_token -> .accessToken (but be careful)
        content = re.sub(
            r'(\b\w+\.)access_token(\b)',
            r'\1accessToken\2',
            content
        )
        
        # Fix expires_at -> expiresAt
        content = re.sub(
            r'(\b\w+\.)expires_at(\b)',
            r'\1expiresAt\2',
            content
        )
        
        # Fix refresh_token -> refreshToken
        content = re.sub(
            r'(\b\w+\.)refresh_token(\b)',
            r'\1refreshToken\2',
            content
        )
        
        # Fix has_refresh_token -> hasRefreshToken
        content = re.sub(
            r'(\b\w+\.)has_refresh_token(\b)',
            r'\1hasRefreshToken\2',
            content
        )
        
        # Fix google_email -> googleEmail
        content = re.sub(
            r'(\b\w+\.)google_email(\b)',
            r'\1googleEmail\2',
            content
        )
        
        # Check if any changes were made
        if content != original_content:
            # Count the changes
            changes = 0
            for pattern in [
                r'credentials\.access_token',
                r'refreshedCredentials\.access_token',
                r'\w+\.access_token',
                r'\w+\.expires_at',
                r'\w+\.refresh_token',
                r'\w+\.has_refresh_token',
                r'\w+\.google_email'
            ]:
                changes += len(re.findall(pattern, original_content))
            
            print(f"  ✅ Fixed {changes} property name mismatches")
            
            # Backup the original file
            backup_path = f"{file_path}.backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            print(f"  📁 Backup created: {backup_path}")
            
            # Write the fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  💾 File updated: {file_path}")
            
            return True
        else:
            print(f"  ⏭️  No changes needed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error processing file: {e}")
        return False

def find_files_to_fix():
    """Find all files that might need property name fixes."""
    patterns = [
        "frontend/src/**/*.ts",
        "frontend/src/**/*.tsx",
        "frontend/src/**/*.js",
        "frontend/src/**/*.jsx",
        "backend/**/*.py",
        "**/*.ts",
        "**/*.tsx",
        "**/*.js",
        "**/*.jsx"
    ]
    
    files = set()
    for pattern in patterns:
        files.update(glob.glob(pattern, recursive=True))
    
    # Filter out node_modules, dist, build, etc.
    files = {f for f in files if not any(exclude in f for exclude in [
        'node_modules', 'dist', 'build', '.git', '.next', '.nuxt'
    ])}
    
    return sorted(files)

def main():
    """Main function to run the property name fix script."""
    print("🔧 Property Name Fix Script")
    print("=" * 50)
    
    # Find files to process
    files = find_files_to_fix()
    print(f"Found {len(files)} files to check")
    print()
    
    # Process each file
    total_fixed = 0
    total_files = 0
    
    for file_path in files:
        if os.path.isfile(file_path):
            total_files += 1
            if fix_property_names_in_file(file_path):
                total_fixed += 1
            print()
    
    # Summary
    print("=" * 50)
    print(f"📊 Summary:")
    print(f"  Total files processed: {total_files}")
    print(f"  Files with fixes: {total_fixed}")
    print(f"  Files unchanged: {total_files - total_fixed}")
    
    if total_fixed > 0:
        print(f"\n✅ Successfully fixed property name mismatches in {total_fixed} files!")
        print(f"💡 All original files have been backed up with .backup extension")
        print(f"🚀 Deploy these changes to fix the Google Calendar 401 errors!")
    else:
        print(f"\n⏭️  No property name mismatches found in the codebase")

if __name__ == "__main__":
    main()
