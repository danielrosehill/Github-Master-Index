#!/usr/bin/env python3
"""
New Repository Notifier

This script checks for new repositories since the last update and can:
1. Display them in the terminal
2. Send a notification
3. Prepare them for easy categorization

Run this after an automated update to quickly identify new repos that need categorization.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

def load_repo_data():
    """Load repository data from JSON export"""
    json_path = Path(__file__).parent.parent / "data" / "exports" / "repo-index.json"
    if not json_path.exists():
        print("Repository data not found. Run repo-fetcher.py first.")
        return None
        
    with open(json_path, 'r') as f:
        return json.load(f)

def get_uncategorized_repos():
    """Get repositories that don't have any category assigned"""
    base_path = Path(__file__).parent.parent
    repo_data = load_repo_data()
    if not repo_data:
        return []
        
    # Get all repo names
    all_repos = [repo['name'] for repo in repo_data]
    
    # Get categorized repos
    categorized = set()
    categories_dir = base_path / "lists" / "categories"
    
    for category_file in categories_dir.glob("*.txt"):
        if category_file.name == "forks.txt":
            continue  # Skip forks as it's automatically assigned
            
        with open(category_file, 'r') as f:
            for line in f:
                repo = line.strip()
                if repo:
                    categorized.add(repo)
    
    # Find uncategorized repos
    uncategorized = [repo for repo in all_repos if repo not in categorized]
    
    # Sort by creation date if available
    if repo_data:
        repo_dict = {repo['name']: repo for repo in repo_data}
        uncategorized.sort(
            key=lambda r: datetime.strptime(repo_dict[r]['created_at'], '%Y-%m-%dT%H:%M:%SZ') 
            if r in repo_dict else datetime.now(),
            reverse=True
        )
    
    return uncategorized

def get_new_repos():
    """Get newly added repositories from incremental update"""
    new_repos_file = Path(__file__).parent.parent / "data" / "incremental" / "new_repos.txt"
    if not new_repos_file.exists():
        return []
        
    new_repos = []
    with open(new_repos_file, 'r') as f:
        for line in f:
            # Extract repo name from line (format: "repo-name (created: 2023-01-01)")
            if '(' in line:
                repo = line.split('(')[0].strip()
                new_repos.append(repo)
            else:
                new_repos.append(line.strip())
                
    return new_repos

def suggest_categories(repos):
    """Suggest categories for the given repositories"""
    # Import auto-categorizer
    sys.path.append(str(Path(__file__).parent.parent))
    from scripts.auto_categorizer import AutoCategorizer
    
    categorizer = AutoCategorizer()
    repo_data = load_repo_data()
    if not repo_data:
        return {}
        
    # Create a lookup for repo data
    repo_dict = {repo['name']: repo for repo in repo_data}
    
    # Get suggestions for each repo
    suggestions = {}
    for repo in repos:
        if repo in repo_dict:
            description = repo_dict[repo].get('description', '')
            suggestions[repo] = categorizer.suggest_categories(repo, description)
        else:
            suggestions[repo] = categorizer.suggest_categories(repo)
            
    return suggestions

def main():
    """Main function"""
    print("New Repository Notifier")
    print("======================\n")
    
    # Check for new repos from incremental update
    new_repos = get_new_repos()
    if new_repos:
        print(f"Found {len(new_repos)} new repositories since last update:")
        for i, repo in enumerate(new_repos, 1):
            print(f"{i}. {repo}")
        print()
        
        # Suggest categories for new repos
        suggestions = suggest_categories(new_repos)
        print("Suggested categories:")
        for repo, cats in suggestions.items():
            if cats:
                print(f"{repo}: {', '.join(cats)}")
            else:
                print(f"{repo}: No suggestions")
        print()
    else:
        print("No new repositories found since last update.\n")
    
    # Check for uncategorized repos
    uncategorized = get_uncategorized_repos()
    if uncategorized:
        print(f"Found {len(uncategorized)} uncategorized repositories:")
        for i, repo in enumerate(uncategorized[:10], 1):
            print(f"{i}. {repo}")
            
        if len(uncategorized) > 10:
            print(f"... and {len(uncategorized) - 10} more")
        print()
        
        print("Run the category manager to categorize these repositories:")
        print("python management/category_manager_qt.py")
    else:
        print("All repositories are categorized!")
    
if __name__ == "__main__":
    main()