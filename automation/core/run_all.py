import importlib.util
import sys
import os
import time
import subprocess
import json
from datetime import datetime
from pathlib import Path

def import_from_file(file_path):
    spec = importlib.util.spec_from_file_location("module", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["module"] = module
    spec.loader.exec_module(module)
    return module

def run_git_commands():
    """
    Run git commands to add, commit, and push changes.
    Returns True if successful, False otherwise.
    """
    try:
        print("\n8. Pushing changes to Git repository...")
        
        # Add all changes
        print("   Running 'git add .'...")
        subprocess.run(["git", "add", "."], check=True)
        
        # Commit changes with timestamp
        commit_message = f"Updated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        print(f"   Running 'git commit -m \"{commit_message}\"'...")
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Push changes
        print("   Running 'git push'...")
        subprocess.run(["git", "push"], check=True)
        
        print("   Git operations completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   Error during Git operations: {e}")
        return False
    except Exception as e:
        print(f"   Unexpected error during Git operations: {e}")
        return False

def run_all(incremental=False, push_to_git=False, use_llm=True, apply_llm_changes=True, skip_git=False):
    """
    Run the complete GitHub Repository Index generation process.
    
    Args:
        incremental (bool): If True, only update if data is older than threshold
        push_to_git (bool): If True, push changes to Git repository after running
        use_llm (bool): If True, use LLM for repository categorization (default: True)
        apply_llm_changes (bool): If True, apply LLM category suggestions automatically (default: True)
        skip_git (bool): If True, skip git operations entirely
    """
    start_time = datetime.now()
    print(f"🚀 Starting GitHub Repository Index generation... (Mode: {'Incremental' if incremental else 'Full'})")
    print(f"   AI Categorization: {'Enabled' if use_llm else 'Disabled'}")
    print(f"   Git Push: {'Enabled' if push_to_git and not skip_git else 'Disabled'}")
    print(f"   Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if we should run based on last update time
    if incremental and should_skip_update():
        print("⏭️  Skipping update - data is recent (less than 12 hours old)")
        return
    
    try:
        # Step 1: Fetch latest repository data from GitHub
        print("\n📡 Step 1: Fetching latest repository data from GitHub...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(os.path.dirname(script_dir))
        repo_fetcher_path = os.path.join(repo_root, "scripts", "repo-fetcher.py")
        repo_fetcher = import_from_file(repo_fetcher_path)
        repo_fetcher.fetch_repos(incremental)
        
        # Step 2: Generate comprehensive JSON and CSV exports
        print("\n📊 Step 2: Generating repository index files...")
        json_creator_path = os.path.join(repo_root, "scripts", "json-creator.py")
        json_creator = import_from_file(json_creator_path)
        timeline_data = json_creator.generate_timeline_json()
        if timeline_data:
            json_creator.save_timeline_json(timeline_data)
            print(f"   ✅ Generated repo-index.json with {len(timeline_data)} repositories")
            
            # Generate CSV from the same data
            print("   📄 Generating repo-index.csv...")
            csv_creator_path = os.path.join(repo_root, "scripts", "csv-creator.py")
            csv_creator = import_from_file(csv_creator_path)
            csv_creator.save_timeline_csv(timeline_data)
            print("   ✅ Generated repo-index.csv")
        else:
            print("   ❌ Failed to generate timeline data")
            return

        # Step 3: AI-powered repository categorization (now standard)
        if use_llm:
            print("\n🤖 Step 3: Running AI-powered repository categorization...")
            
            # Check for API key
            if not os.getenv("OPENAI_API_KEY"):
                print("   ⚠️  Warning: OPENAI_API_KEY not found. Skipping AI categorization.")
                print("   💡 Set OPENAI_API_KEY environment variable to enable AI categorization.")
            else:
                try:
                    # Use the enhanced categorize_all script
                    print("   🔍 Analyzing repositories for categorization...")
                    result = subprocess.run([
                        "python", "categorize_all.py", 
                        "--apply", 
                        "--batch-size", "10",
                        "--delay", "2",
                        "--consolidate"
                    ], capture_output=True, text=True, cwd=os.getcwd())
                    
                    if result.returncode == 0:
                        print("   ✅ AI categorization completed successfully")
                        # Extract some stats from the output
                        output_lines = result.stdout.split('\n')
                        for line in output_lines:
                            if "Loaded" in line and "repositories" in line:
                                print(f"   📈 {line.strip()}")
                            elif "Processing" in line and "repositories" in line:
                                print(f"   🔄 {line.strip()}")
                            elif "Categorization complete" in line:
                                print(f"   🎯 {line.strip()}")
                    else:
                        print(f"   ⚠️  AI categorization had issues (exit code: {result.returncode})")
                        print(f"   📝 Error output: {result.stderr[:200]}..." if result.stderr else "")
                        # Continue with the process even if categorization fails
                        
                except Exception as e:
                    print(f"   ❌ Error during AI categorization: {e}")
                    print("   🔄 Continuing with remaining steps...")
        else:
            print("\n⏭️  Step 3: Skipping AI categorization (disabled)")

        # Step 4: Generate repository status and activity data
        print("\n📊 Step 4: Generating repository status data...")
        status_badges_path = os.path.join(repo_root, "scripts", "status_badges.py")
        status_badges = import_from_file(status_badges_path)
        status_badges.generate_status_badges()
        print("   ✅ Repository status data generated")

        # Step 5: Generate chronological timeline
        print("\n📅 Step 5: Generating chronological timeline...")
        timeline_generator_path = os.path.join(repo_root, "scripts", "timeline_generator.py")
        timeline_generator = import_from_file(timeline_generator_path)
        timeline_generator.generate_timeline()
        print("   ✅ Timeline generated")

        # Step 6: Generate category markdown files
        print("\n📝 Step 6: Generating category markdown files...")
        markdown_generator_path = os.path.join(repo_root, "scripts", "markdown_generator.py")
        markdown_generator = import_from_file(markdown_generator_path)
        markdown_generator.generate_markdown_files('data/exports/repo-index.json', 'lists/categories')
        print("   ✅ Category markdown files generated")
        
        # Step 7: Enhance section files with additional metadata
        print("\n✨ Step 7: Enhancing section files with status badges and language info...")
        section_enhancer_path = os.path.join(repo_root, "scripts", "section_enhancer.py")
        section_enhancer = import_from_file(section_enhancer_path)
        section_enhancer.enhance_section_files()
        print("   ✅ Section files enhanced")
        
        # Step 8: Generate the main README.md
        print("\n📖 Step 8: Generating main README.md...")
        readme_builder_path = os.path.join(repo_root, "scripts", "readme-builder.py")
        readme_builder = import_from_file(readme_builder_path)
        readme_builder.generate_readme()
        print("   ✅ README.md generated")
        
        # Update the last run timestamp
        update_timestamp()
        
        # Step 9: Git operations (if requested)
        if push_to_git and not skip_git:
            success = run_git_commands()
            if not success:
                print("   ⚠️  Git operations failed, but data generation was successful")
        elif skip_git:
            print("\n⏭️  Step 9: Skipping git operations (disabled)")
        else:
            print("\n⏭️  Step 9: Skipping git push (not requested)")
        
        # Final summary
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"\n🎉 All operations completed successfully!")
        print(f"   ⏱️  Total duration: {duration}")
        print(f"   📊 Final repository count: {len(timeline_data) if timeline_data else 'Unknown'}")
        print(f"   🕐 Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        print("   📝 Check logs for more details")
        raise

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

def show_help():
    """Display help information"""
    print("GitHub Repository Index Generator")
    print("=" * 40)
    print("")
    print("Usage: python run_all.py [OPTIONS]")
    print("")
    print("Options:")
    print("  --help, -h           Show this help message")
    print("  --incremental        Only update if data is older than 12 hours")
    print("  --push, --git        Push changes to Git repository after completion")
    print("  --no-ai              Disable AI-powered categorization")
    print("  --no-git             Skip all git operations")
    print("  --dry-run            Show what would be done without making changes")
    print("")
    print("Examples:")
    print("  python run_all.py                    # Full update with AI, no git push")
    print("  python run_all.py --push             # Full update with AI and git push")
    print("  python run_all.py --incremental      # Only update if data is old")
    print("  python run_all.py --no-ai --push     # Update without AI categorization")
    print("  python run_all.py --dry-run          # Preview what would be done")
    print("")
    print("Default behavior:")
    print("  - AI categorization: ENABLED")
    print("  - Git push: DISABLED (use --push to enable)")
    print("  - Update mode: FULL (use --incremental for conditional updates)")

if __name__ == "__main__":
    # Parse command line arguments
    if "--help" in sys.argv or "-h" in sys.argv:
        show_help()
        sys.exit(0)
    
    incremental = "--incremental" in sys.argv
    push_to_git = "--push" in sys.argv or "--git" in sys.argv
    use_llm = "--no-ai" not in sys.argv  # AI is enabled by default now
    apply_llm_changes = use_llm  # If using LLM, apply changes by default
    skip_git = "--no-git" in sys.argv
    dry_run = "--dry-run" in sys.argv
    
    if dry_run:
        print("🔍 DRY RUN MODE - Showing what would be done:")
        print(f"   Incremental mode: {'Yes' if incremental else 'No'}")
        print(f"   AI categorization: {'Yes' if use_llm else 'No'}")
        print(f"   Git operations: {'Yes' if push_to_git and not skip_git else 'No'}")
        print(f"   Skip git entirely: {'Yes' if skip_git else 'No'}")
        print("")
        print("Steps that would be executed:")
        print("  1. Fetch repository data from GitHub")
        print("  2. Generate JSON and CSV exports")
        if use_llm:
            print("  3. Run AI-powered categorization")
        else:
            print("  3. Skip AI categorization")
        print("  4. Generate repository status data")
        print("  5. Generate chronological timeline")
        print("  6. Generate category markdown files")
        print("  7. Enhance section files")
        print("  8. Generate main README.md")
        if push_to_git and not skip_git:
            print("  9. Commit and push to Git")
        else:
            print("  9. Skip git operations")
        print("")
        print("To execute, run without --dry-run")
        sys.exit(0)
    
    # Override git push behavior if skip_git is set
    if skip_git:
        push_to_git = False
    
    run_all(incremental, push_to_git, use_llm, apply_llm_changes, skip_git)