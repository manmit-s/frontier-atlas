#!/usr/bin/env python3
"""
Storage Diagnostic Tool
Measures local project footprint and validates compliance with the < 1 GB hard limit.
"""
from pathlib import Path
import sys

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.config.settings import settings
from src.utils.cleanup import get_storage_breakdown

def main():
    breakdown = get_storage_breakdown()
    print("=" * 60)
    print("         LOCAL PROJECT DISK USAGE REPORT")
    print("=" * 60)
    print(f"Project Directory    : {settings.BASE_DIR}")
    print(f"Total Project Size   : {breakdown['project_total_mb']} MB")
    print(f"Database Directory   : {breakdown['data_dir_mb']} MB")
    print(f"Temp Storage         : {breakdown['temp_storage_mb']} MB")
    print(f"Cache Storage        : {breakdown['cache_storage_mb']} MB")
    print(f"System Free Space    : {breakdown['system_free_gb']} GB")
    print("-" * 60)
    print("Top 5 Largest Files in Project:")
    for rel_path, size_mb in breakdown["largest_files"]:
        print(f"  - {rel_path:<40}: {size_mb:.2f} MB")
    print("-" * 60)
    
    limit = settings.MAX_PROJECT_FOOTPRINT_MB
    is_compliant = breakdown["project_total_mb"] <= limit
    status = "PASSED (< 1 GB HARD CEILING SATISFIED)" if is_compliant else "FAILED (EXCEEDS STORAGE LIMIT)"
    print(f"Compliance Check     : {status}")
    print("=" * 60)

if __name__ == "__main__":
    main()
