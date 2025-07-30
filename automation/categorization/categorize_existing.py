#!/usr/bin/env python3
"""
Script to categorize repositories using only existing categories.
This script will not create any new categories and will only assign repositories
to categories that already exist in the system.
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
    """Main function to categorize repositories using only existing categories"""
    parser = argparse.ArgumentParser(description="Categorize repositories using only existing categories")
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
    
    # Initialize the categorizer with existing-only mode
    categorizer = ExistingOnlyCategorizer()
    categorizer.request_delay = args.delay  # Set custom delay between API calls
    
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
    print(f"IMPORTANT: Only using existing categories - no new categories will be created")
    
    if not args.apply:
        print("\nWARNING: Running without --apply will only show suggestions without making changes.")
        print("To apply the changes, run with the --apply flag.")
    
    # Track overall statistics
    total_suggestions = 0
    
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


class ExistingOnlyCategorizer(LLMCategorizer):
    """
    A modified version of the LLMCategorizer that only uses existing categories
    and does not create new ones.
    """
    
    def _generate_categorization_prompt(self, repo_name, description, readme_content, existing_categories, entity_names=None):
        """Generate a prompt for the LLM to categorize a repository using only existing categories"""
        
        # Create tech terminology context section
        tech_context_str = "\n".join([f"- {term}: {definition}" for term, definition in self.tech_context.items()])
        
        # Format entity names if available
        entity_names_str = ""
        if entity_names and len(entity_names) > 0:
            entity_names_str = "Potential entity names detected:\n" + "\n".join([f"- {entity}" for entity in entity_names])
        
        # Group similar categories to help the model understand relationships
        similar_categories = self._group_similar_categories(existing_categories)
        similar_categories_str = ""
        if similar_categories:
            similar_categories_str = "Similar Category Groups (use the most appropriate one):\n"
            for i, group in enumerate(similar_categories):
                similar_categories_str += f"Group {i+1}: {', '.join(group)}\n"
        
        prompt = f"""
You are an expert at categorizing GitHub repositories, especially in the fields of AI, LLMs, programming tools, and developer utilities. I need you to analyze this repository and suggest appropriate categories.

IMPORTANT CONTEXT - Technical Terminology:
{tech_context_str}

Repository Name: {repo_name}
Description: {description or "No description available"}

README Content:
{readme_content or "No README content available"}

{entity_names_str}

AVAILABLE CATEGORIES (you MUST ONLY use these existing categories):
{', '.join(existing_categories)}

{similar_categories_str}

Please suggest categories for this repository. You MUST ONLY use categories from the AVAILABLE CATEGORIES list above.

IMPORTANT INSTRUCTIONS:
1. Focus on the TECHNICAL PURPOSE of the repository, not literal interpretations of terms
2. For example, if a repo is named "AI-Cookbook", it's about AI code examples, NOT cooking
3. You may ONLY use categories from the AVAILABLE CATEGORIES list - DO NOT suggest new categories
4. Be precise and specific - avoid overly general categories
5. Consider the actual function and domain of the repository
6. If you're unsure about a category, DON'T suggest it - only include high-confidence matches
7. A repository can belong to MULTIPLE categories - don't limit your suggestions if multiple categories apply
8. If none of the existing categories fit well, choose the closest matches or leave it uncategorized
9. DO NOT create new categories under any circumstances

For each suggested category, provide:
1. The category name (must be from the AVAILABLE CATEGORIES list)
2. A confidence score (0-100)
3. A brief explanation of why this category fits

Format your response as a JSON object with this structure:
{{
  "categories": [
    {{
      "name": "category-name",
      "confidence": 95,
      "explanation": "Brief explanation"
    }},
    ...
  ]
}}

IMPORTANT: 
- Return ONLY the JSON object, no other text
- Use ONLY categories from the AVAILABLE CATEGORIES list
- There is NO LIMIT on how many categories a repository can belong to - assign all relevant ones
- If no categories fit well, return an empty "categories" array
"""
        return prompt
    
    def batch_categorize(self, repos_data, min_confidence=80, apply_changes=False):
        """
        Categorize a batch of repositories using only existing categories.
        
        Args:
            repos_data (list): List of repository dictionaries with 'name' and 'description'
            min_confidence (int): Minimum confidence score to accept a category suggestion
            apply_changes (bool): Whether to apply the changes to category files
            
        Returns:
            dict: Dictionary mapping repository names to suggested categories
        """
        results = {}
        
        # Process each repository
        for i, repo in enumerate(repos_data):
            repo_name = repo.get('name', '')
            description = repo.get('description', '')
            
            print(f"Categorizing repository {i+1}/{len(repos_data)}: {repo_name}")
            
            # Categorize the repository
            suggestions = self.categorize_repository(repo_name, description, min_confidence)
            if not suggestions:
                print(f"No suggestions generated for {repo_name}")
                continue
                
            # Filter suggestions by confidence
            accepted_categories = []
            
            # Process existing categories
            for category in suggestions.get('categories', []):
                if category.get('confidence', 0) >= min_confidence:
                    accepted_categories.append({
                        'name': category['name'],
                        'confidence': category['confidence'],
                        'explanation': category.get('explanation', ''),
                        'is_new': False,
                        'is_entity': category.get('is_entity', False)
                    })
            
            results[repo_name] = accepted_categories
            
            # Add delay to avoid rate limiting
            time.sleep(self.request_delay)
        
        # Apply changes if requested
        if apply_changes:
            self._apply_category_changes_existing_only(results)
            
        return results
    
    def _apply_category_changes_existing_only(self, categorization_results):
        """
        Apply the categorization results to the category files, using only existing categories.
        
        Args:
            categorization_results (dict): Dictionary mapping repo names to category lists
        """
        print("Applying category changes...")
        
        # Create directories if they don't exist
        categories_dir = self.base_path / "lists" / "categories"
        categories_dir.mkdir(parents=True, exist_ok=True)
        
        # Track changes for reporting
        changes_made = []
        
        # Update category assignments
        for repo_name, categories in categorization_results.items():
            # Get category names only
            category_names = [cat['name'] for cat in categories]
            
            # Skip if no categories suggested
            if not category_names:
                continue
                
            # Update each category file
            for category in category_names:
                category_file = categories_dir / f"{category}.txt"
                
                # Skip if category file doesn't exist (only use existing categories)
                if not category_file.exists():
                    print(f"Warning: Category file {category}.txt does not exist. Skipping.")
                    continue
                
                # Read existing entries
                existing_entries = []
                with open(category_file, "r") as f:
                    existing_entries = [line.strip() for line in f if line.strip()]
                
                # Add the repository if not already present
                if repo_name not in existing_entries:
                    print(f"Adding {repo_name} to category {category}")
                    with open(category_file, "a") as f:
                        f.write(f"{repo_name}\n")
                    changes_made.append(f"Added {repo_name} to category {category}")
        
        # Print summary of changes
        if changes_made:
            print("\nSummary of changes made:")
            for change in changes_made:
                print(f"- {change}")
        else:
            print("No changes were made - all repositories were already correctly categorized.")
        
        # Create a report of the changes
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_dir = self.base_path / "reports"
        report_dir.mkdir(exist_ok=True, parents=True)
        report_file = report_dir / f"categorization_report_existing_only_{timestamp}.json"
        
        with open(report_file, "w") as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "changes_made": changes_made,
                "categorization_results": {
                    repo: [
                        {
                            "name": cat["name"],
                            "confidence": cat["confidence"],
                            "explanation": cat["explanation"],
                            "is_new": cat.get("is_new", False),
                            "is_entity": cat.get("is_entity", False)
                        } 
                        for cat in cats
                    ]
                    for repo, cats in categorization_results.items()
                }
            }, f, indent=2)
            
        print(f"Categorization report saved to {report_file}")


if __name__ == "__main__":
    exit(main())
