import importlib.util
import sys
import os
import time
from datetime import datetime

def import_from_file(file_path):
    spec = importlib.util.spec_from_file_location("module", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["module"] = module
    spec.loader.exec_module(module)
    return module

def run_all(incremental=False):
    """
    Run the complete GitHub Timeline generation process.
    
    Args:
        incremental (bool): If True, only update if data is older than threshold
    """
    print(f"Starting GitHub Timeline generation... (Mode: {'Incremental' if incremental else 'Full'})")
    
    # Check if we should run based on last update time
    if incremental and should_skip_update():
        print("Skipping update - data is recent")
        return
    
    print("\n1. Fetching repository list...")
    repo_fetcher = import_from_file("scripts/repo-fetcher.py")
    repo_fetcher.fetch_repos()
    
    print("\n2. Generating repo-index.json and repo-index.csv...")
    json_creator = import_from_file("scripts/json-creator.py")
    timeline_data = json_creator.generate_timeline_json()
    if timeline_data:
        json_creator.save_timeline_json(timeline_data)
        
        # Generate CSV from the same data
        print("   Generating repo-index.csv...")
        csv_creator = import_from_file("scripts/csv-creator.py")
        csv_creator.save_timeline_csv(timeline_data)

    print("\n3. Generating repository status data...")
    status_badges = import_from_file("scripts/status_badges.py")
    status_badges.generate_status_badges()

    print("\n4. Generating chronological timeline...")
    timeline_generator = import_from_file("scripts/timeline_generator.py")
    timeline_generator.generate_timeline()

    print("\n5. Generating category markdown files...")
    markdown_generator = import_from_file("scripts/markdown_generator.py")
    markdown_generator.generate_markdown_files('data/exports/repo-index.json', 'lists/categories')
    
    print("\n6. Enhancing section files with status badges and language info...")
    section_enhancer = import_from_file("scripts/section_enhancer.py")
    section_enhancer.enhance_section_files()
    
    print("\n7. Generating README.md...")
    readme_builder = import_from_file("scripts/readme-builder.py")
    readme_builder.generate_readme()
    
    # Update the last run timestamp
    update_timestamp()
    
    print("\nAll operations completed!")

def should_skip_update():
    """
    Determine if we should skip the update based on the last run time.
    Returns True if the last update was less than 12 hours ago.
    """
    timestamp_file = "data/.last_update"
    
    # If no timestamp file exists, we should run
    if not os.path.exists(timestamp_file):
        return False
        
    try:
        with open(timestamp_file, 'r') as f:
            last_update = float(f.read().strip())
            
        # Skip if less than 12 hours have passed
        hours_since_update = (time.time() - last_update) / 3600
        return hours_since_update < 12
    except Exception as e:
        print(f"Error checking update timestamp: {e}")
        return False

def update_timestamp():
    """Update the timestamp file with the current time"""
    os.makedirs("data", exist_ok=True)
    with open("data/.last_update", 'w') as f:
        f.write(str(time.time()))

if __name__ == "__main__":
    # Check if incremental flag is passed
    incremental = "--incremental" in sys.argv
    run_all(incremental)