#!/usr/bin/env python3
"""
Simplified GitHub Repository Index Generator
Focuses on basic repository data fetching and export generation without AI categorization.
"""

import importlib.util
import sys
import os
import time
import subprocess
from datetime import datetime

def import_from_file(file_path):
    """Import a Python module from a file path"""
    spec = importlib.util.spec_from_file_location("module", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["module"] = module
    spec.loader.exec_module(module)
    return module

def run_git_commands():
    """Run git commands to add, commit, and push changes"""
    try:
        print("\n📤 Pushing changes to Git repository...")
        
        # Add all changes
        subprocess.run(["git", "add", "."], check=True)
        
        # Commit changes with timestamp
        commit_message = f"Updated repository index {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Push changes
        subprocess.run(["git", "push"], check=True)
        
        print("   ✅ Git operations completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error during Git operations: {e}")
        return False

def update_timestamp():
    """Update the timestamp file with the current time"""
    os.makedirs("data", exist_ok=True)
    with open("data/.last_update", 'w') as f:
        f.write(str(time.time()))

def run_basic_update(push_to_git=False):
    """
    Run a simplified repository index update with basic functionality only.
    
    Args:
        push_to_git (bool): If True, push changes to Git repository after running
    """
    start_time = datetime.now()
    print(f"🚀 Starting basic GitHub Repository Index update...")
    print(f"   Git Push: {'Enabled' if push_to_git else 'Disabled'}")
    print(f"   Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Fetch latest repository data from GitHub
        print("\n📡 Step 1: Fetching latest repository data from GitHub...")
        repo_fetcher_path = os.path.join("scripts", "repo-fetcher.py")
        repo_fetcher = import_from_file(repo_fetcher_path)
        repo_fetcher.fetch_repos(False)  # Always do full fetch for simplicity
        print("   ✅ Repository data fetched")
        
        # Step 2: Generate JSON export
        print("\n📊 Step 2: Generating repository index files...")
        json_creator_path = os.path.join("scripts", "json-creator.py")
        json_creator = import_from_file(json_creator_path)
        timeline_data = json_creator.generate_timeline_json()
        if timeline_data:
            json_creator.save_timeline_json(timeline_data)
            print(f"   ✅ Generated repo-index.json with {len(timeline_data)} repositories")
            
            # Generate CSV from the same data
            csv_creator_path = os.path.join("scripts", "csv-creator.py")
            csv_creator = import_from_file(csv_creator_path)
            csv_creator.save_timeline_csv(timeline_data)
            print("   ✅ Generated repo-index.csv")
        else:
            print("   ❌ Failed to generate timeline data")
            return
        
        # Step 3: Generate repository status data
        print("\n📊 Step 3: Generating repository status data...")
        status_badges_path = os.path.join("scripts", "status_badges.py")
        status_badges = import_from_file(status_badges_path)
        status_badges.generate_status_badges()
        print("   ✅ Repository status data generated")
        
        # Step 4: Generate chronological timeline
        print("\n📅 Step 4: Generating chronological timeline...")
        timeline_generator_path = os.path.join("scripts", "timeline_generator.py")
        timeline_generator = import_from_file(timeline_generator_path)
        timeline_generator.generate_timeline()
        print("   ✅ Timeline generated")
        
        # Update timestamp
        update_timestamp()
        
        # Step 5: Git operations (if requested)
        if push_to_git:
            success = run_git_commands()
            if not success:
                print("   ⚠️  Git operations failed, but data generation was successful")
        else:
            print("\n⏭️  Step 5: Skipping git push (not requested)")
        
        # Final summary
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"\n🎉 Basic update completed successfully!")
        print(f"   ⏱️  Total duration: {duration}")
        print(f"   📊 Repository count: {len(timeline_data) if timeline_data else 'Unknown'}")
        print(f"   🕐 Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        raise

def show_help():
    """Display help information"""
    print("Simplified GitHub Repository Index Generator")
    print("=" * 45)
    print("")
    print("Usage: python run_all.py [OPTIONS]")
    print("")
    print("Options:")
    print("  --help, -h           Show this help message")
    print("  --push, --git        Push changes to Git repository after completion")
    print("  --dry-run            Show what would be done without making changes")
    print("")
    print("Examples:")
    print("  python run_all.py                    # Basic update, no git push")
    print("  python run_all.py --push             # Basic update with git push")
    print("  python run_all.py --dry-run          # Preview what would be done")
    print("")
    print("What this script does:")
    print("  1. Fetches repository data from GitHub")
    print("  2. Generates JSON and CSV exports")
    print("  3. Generates repository status data")
    print("  4. Generates chronological timeline")
    print("  5. Optionally pushes to Git")

if __name__ == "__main__":
    # Parse command line arguments
    if "--help" in sys.argv or "-h" in sys.argv:
        show_help()
        sys.exit(0)
    
    push_to_git = "--push" in sys.argv or "--git" in sys.argv
    dry_run = "--dry-run" in sys.argv
    
    if dry_run:
        print("🔍 DRY RUN MODE - Showing what would be done:")
        print(f"   Git operations: {'Yes' if push_to_git else 'No'}")
        print("")
        print("Steps that would be executed:")
        print("  1. Fetch repository data from GitHub")
        print("  2. Generate JSON and CSV exports")
        print("  3. Generate repository status data")
        print("  4. Generate chronological timeline")
        if push_to_git:
            print("  5. Commit and push to Git")
        else:
            print("  5. Skip git operations")
        print("")
        print("To execute, run without --dry-run")
        sys.exit(0)
    
    run_basic_update(push_to_git)
