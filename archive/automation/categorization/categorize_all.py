#!/usr/bin/env python3
"""
Script to categorize all repositories using the LLM categorizer.
This is a standalone script that can be run to categorize all repositories
without running the full update process.
"""

import os
import json
import argparse
import time
from pathlib import Path
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../scripts'))
from llm_categorizer import LLMCategorizer

def main():
    """Main function to categorize all repositories"""
    parser = argparse.ArgumentParser(description="Categorize all repositories using LLM")
    parser.add_argument("--min-confidence", type=int, default=80, 
                        help="Minimum confidence score (0-100)")
    parser.add_argument("--apply", action="store_true", 
                        help="Apply changes to category files")
    parser.add_argument("--batch-size", type=int, default=10,
                        help="Number of repositories to process in each batch")
    parser.add_argument("--start-from", type=str, default=None,
                        help="Start processing from this repository name")
    parser.add_argument("--delay", type=int, default=2,
                        help="Delay in seconds between API calls to avoid rate limiting")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without making API calls")
    parser.add_argument("--force", action="store_true",
                        help="Force categorization even for already categorized repositories")
    parser.add_argument("--max-repos", type=int, default=None,
                        help="Maximum number of repositories to process (useful for testing)")
    parser.add_argument("--resume-from-last", action="store_true",
                        help="Resume from the last processed repository based on logs")
    parser.add_argument("--consolidate", action="store_true",
                        help="Consolidate similar categories after categorization")
    parser.add_argument("--only-consolidate", action="store_true",
                        help="Only consolidate categories without categorizing repositories")
    parser.add_argument("--no-confirm", action="store_true", default=True,
                        help="Skip confirmation prompt (default: True)")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY") and not args.dry_run:
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set this in your .env file or environment.")
        return 1
    
    # Load repository data
    base_path = Path(__file__).parent
    json_path = base_path / "data" / "exports" / "repo-index.json"
    
    try:
        with open(json_path, "r") as f:
            repos_data = json.load(f)
    except Exception as e:
        print(f"Error loading repository data: {e}")
        return 1
    
    print(f"Loaded {len(repos_data)} repositories from {json_path}")
    
    # Initialize the categorizer
    categorizer = LLMCategorizer()
    categorizer.request_delay = args.delay  # Set custom delay between API calls
    
    # Only consolidate categories if requested
    if args.only_consolidate:
        print("\nOnly consolidating categories as requested...")
        categorizer = LLMCategorizer()
        categorizer.consolidate_similar_categories()
        return 0
    
    # Load current category assignments to check which repos are already categorized
    current_assignments = categorizer._load_current_assignments()
    
    # Try to resume from last run if requested
    if args.resume_from_last:
        # Create reports directory if it doesn't exist
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Get the latest report if resuming from last
        report_files = list(reports_dir.glob("categorization_report_*.json"))
        if not report_files:
            print("No previous reports found to resume from.")
            return 1
            
        latest_report = max(report_files, key=lambda f: f.stat().st_mtime)
        print(f"Resuming from last report: {latest_report}")
        
        with open(latest_report, "r") as f:
            report_data = json.load(f)
            
        # Get the last processed repository
        processed_repos = list(report_data["categorization_results"].keys())
        if not processed_repos:
            print("No processed repositories found in the last report.")
            return 1
            
        last_processed = processed_repos[-1]
        print(f"Last processed repository: {last_processed}")
        
        # Find the index of the last processed repository
        repo_names = [repo.get('name', '') for repo in repos_data]
        if last_processed in repo_names:
            last_index = repo_names.index(last_processed)
            if last_index < len(repos_data) - 1:
                repos_data = repos_data[last_index + 1:]
                print(f"Skipping {last_index + 1} already processed repositories")
        else:
            print(f"Warning: Last processed repository {last_processed} not found in repository list.")
    
    # Filter repositories if starting from a specific one
    if args.start_from:
        start_index = next((i for i, repo in enumerate(repos_data) 
                           if repo.get('name') == args.start_from), 0)
        if start_index > 0:
            print(f"Starting from repository {args.start_from} (index {start_index})")
            repos_data = repos_data[start_index:]
    
    # Filter out already categorized repositories unless --force is used
    if not args.force:
        uncategorized_repos = []
        for repo in repos_data:
            repo_name = repo.get('name', '')
            if repo_name not in current_assignments or not current_assignments[repo_name]:
                uncategorized_repos.append(repo)
        
        if len(uncategorized_repos) < len(repos_data):
            print(f"Filtered out {len(repos_data) - len(uncategorized_repos)} already categorized repositories.")
            print(f"Processing {len(uncategorized_repos)} uncategorized repositories.")
            repos_data = uncategorized_repos
    
    # Limit the number of repositories if max-repos is specified
    if args.max_repos and args.max_repos < len(repos_data):
        print(f"Limiting to {args.max_repos} repositories as requested")
        repos_data = repos_data[:args.max_repos]
    
    # Process repositories in batches
    total_repos = len(repos_data)
    
    if total_repos == 0:
        print("No repositories to process. All repositories may already be categorized.")
        print("Use --force to recategorize already categorized repositories.")
        return 0
        
    batch_size = min(args.batch_size, total_repos)
    num_batches = (total_repos + batch_size - 1) // batch_size  # Ceiling division
    
    # Dry run mode
    if args.dry_run:
        print("\nDRY RUN MODE - No actual API calls or changes will be made")
        print(f"Would process {total_repos} repositories in {num_batches} batches")
        print(f"Confidence threshold: {args.min_confidence}%")
        print(f"Apply changes: {args.apply}")
        print(f"First 5 repositories that would be processed:")
        for i, repo in enumerate(repos_data[:5]):
            print(f"  {i+1}. {repo.get('name', '')}")
        return 0
    
    # Skip confirmation and proceed directly
    print(f"\nProcessing {total_repos} repositories in {num_batches} batches")
    print(f"Confidence threshold: {args.min_confidence}%")
    print(f"Apply changes: {args.apply}")
    
    if not args.apply:
        print("\nWARNING: Running without --apply will only show suggestions without making changes.")
        print("To apply the changes, run with the --apply flag.")
    
    # Track overall statistics
    total_suggestions = 0
    total_changes = 0
    
    for batch_num in range(num_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total_repos)
        batch = repos_data[start_idx:end_idx]
        
        print(f"\nProcessing batch {batch_num + 1}/{num_batches} "
              f"(repositories {start_idx + 1}-{end_idx} of {total_repos})")
        
        # Process the batch
        results = categorizer.batch_categorize(
            batch,
            min_confidence=args.min_confidence,
            apply_changes=args.apply
        )
        
        # Count suggestions in this batch
        batch_suggestions = sum(len(cats) for cats in results.values())
        total_suggestions += batch_suggestions
        
        # Print batch summary
        print(f"Batch {batch_num + 1} complete: {batch_suggestions} suggestions for {len(batch)} repositories")
        
        # Consolidate categories after each batch if requested
        if args.consolidate and args.apply:
            print("\nConsolidating similar categories...")
            categorizer.consolidate_similar_categories()
    
    # Print overall summary
    print(f"\nCategorization complete: {total_suggestions} suggestions for {total_repos} repositories")
    
    # Final consolidation if requested
    if args.consolidate and args.apply:
        print("\nPerforming final consolidation of similar categories...")
        categorizer.consolidate_similar_categories()
    
    return 0

if __name__ == "__main__":
    exit(main())
