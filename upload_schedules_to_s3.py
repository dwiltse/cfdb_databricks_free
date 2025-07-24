#!/usr/bin/env python3
"""
Upload scraped 2025 schedule JSON files to S3 bucket for Databricks ingestion.
Uses AWS CLI to copy files to the external location path.
"""
import os
import subprocess
import json
from pathlib import Path

def upload_schedule_files():
    """Upload all 2025 schedule JSON files to S3"""
    
    # S3 destination path
    s3_path = "s3://ncaadata/2025_schedules/"
    
    # Local paths with schedule data
    schedule_dirs = [
        "cfdb_schedules_complete",
        "cfdb_schedules_webfetch"
    ]
    
    uploaded_files = []
    
    for dir_name in schedule_dirs:
        local_path = Path(dir_name)
        if not local_path.exists():
            print(f"Directory {dir_name} not found, skipping...")
            continue
            
        # Find all JSON files
        json_files = list(local_path.rglob("*.json"))
        
        for json_file in json_files:
            # Create S3 key preserving directory structure
            relative_path = json_file.relative_to(local_path)
            s3_key = f"{s3_path}{dir_name}/{relative_path}"
            
            try:
                # Use AWS CLI to copy file
                cmd = ["aws", "s3", "cp", str(json_file), s3_key]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                print(f"✓ Uploaded: {json_file} -> {s3_key}")
                uploaded_files.append(s3_key)
                
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to upload {json_file}: {e.stderr}")
            except Exception as e:
                print(f"✗ Error uploading {json_file}: {str(e)}")
    
    print(f"\nUpload complete! {len(uploaded_files)} files uploaded to S3.")
    return uploaded_files

def verify_files():
    """Verify what files exist locally before upload"""
    print("Local schedule files found:")
    
    schedule_dirs = ["cfdb_schedules_complete", "cfdb_schedules_webfetch"]
    
    for dir_name in schedule_dirs:
        local_path = Path(dir_name)
        if local_path.exists():
            json_files = list(local_path.rglob("*.json"))
            print(f"\n{dir_name}/:")
            for json_file in json_files:
                # Get file size
                size_mb = json_file.stat().st_size / (1024 * 1024)
                print(f"  {json_file.relative_to(local_path)} ({size_mb:.2f} MB)")
        else:
            print(f"\n{dir_name}/: Directory not found")

if __name__ == "__main__":
    print("=== CFDB 2025 Schedule Upload to S3 ===\n")
    
    # First verify what files we have
    verify_files()
    
    print("\n" + "="*50)
    print("\nProceeding with upload...")
    
    uploaded_files = upload_schedule_files()
    
    if uploaded_files:
        print(f"\nFiles available in Databricks external location:")
        print("s3://ncaadata/2025_schedules/")