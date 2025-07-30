#!/usr/bin/env python3
"""
Wrapper script for backward compatibility.
The main run_all.py script has been moved to automation/core/run_all.py
"""

import sys
import os
import subprocess

# Add the automation/core directory to the path
automation_core_path = os.path.join(os.path.dirname(__file__), 'automation', 'core')
sys.path.insert(0, automation_core_path)

# Import and run the main script
try:
    # Import the moved script as a module
    import importlib.util
    spec = importlib.util.spec_from_file_location("run_all", os.path.join(automation_core_path, 'run_all.py'))
    run_all_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run_all_module)
    
    # Import the functions we need
    run_all = run_all_module.run_all
    show_help = run_all_module.show_help
    
    # Execute the main function if this script is run directly
    if __name__ == "__main__":
        # Parse command line arguments (same as original)
        if "--help" in sys.argv or "-h" in sys.argv:
            show_help()
            sys.exit(0)
        
        incremental = "--incremental" in sys.argv
        push_to_git = "--push" in sys.argv or "--git" in sys.argv
        use_llm = "--no-ai" not in sys.argv
        apply_llm_changes = use_llm
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

except ImportError as e:
    print(f"Error importing from automation/core/run_all.py: {e}")
    print("Falling back to direct execution...")
    
    # Fallback: execute the moved script directly
    script_path = os.path.join(automation_core_path, 'run_all.py')
    if os.path.exists(script_path):
        subprocess.run([sys.executable, script_path] + sys.argv[1:])
    else:
        print(f"Error: Could not find {script_path}")
        sys.exit(1)
