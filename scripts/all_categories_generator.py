#!/usr/bin/env python3
"""
All Categories Generator

This script generates a comprehensive 'all-categories.md' page that lists all categories
and the repositories within each category in a single page.
"""

import json
import os
import glob
from pathlib import Path

def generate_all_categories_page():
    """
    Generates a markdown page that lists all categories and their repositories.
    """
    # Get project root directory
    project_root = Path(__file__).parent.parent
    
    # Paths
    repo_index_file = project_root / "data" / "exports" / "repo-index.json"
    categories_dir = project_root / "lists" / "categories"
    output_file = project_root / "sections" / "all-categories.md"
    
    # Load repository data from JSON
    with open(repo_index_file, 'r') as f:
        repo_data = json.load(f)
    
    # Create a dictionary to map repo names to their full data
    repo_dict = {repo['name']: repo for repo in repo_data}
    
    # Get all category files and sort them alphabetically
    category_files = sorted(glob.glob(str(categories_dir / "*.txt")))
    
    # Initialize markdown content
    content = ["# All Categories\n"]
    content.append("This page provides a comprehensive view of all repository categories and the repositories within each category.\n")
    content.append("## Table of Contents\n")
    
    # Generate table of contents
    for category_file in category_files:
        category_name = Path(category_file).stem
        display_name = category_name.replace('-', ' ').title()
        content.append(f"- [{display_name}](#{category_name})")
    
    content.append("\n---\n")
    
    # Generate content for each category
    for category_file in category_files:
        category_name = Path(category_file).stem
        display_name = category_name.replace('-', ' ').title()
        
        # Add category header with anchor
        content.append(f"## {display_name} <a name='{category_name}'></a>\n")
        
        # Read repositories in this category
        with open(category_file, 'r') as f:
            repo_names = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        # Count repositories in this category
        content.append(f"**Total repositories in this category:** {len(repo_names)}\n")
        
        # Add repositories table header
        content.append("| Repository | Description |")
        content.append("| --- | --- |")
        
        # Sort repositories alphabetically
        repo_names.sort(key=lambda x: x.lower())
        
        # Add each repository to the table
        for repo_name in repo_names:
            if repo_name in repo_dict:
                repo = repo_dict[repo_name]
                repo_url = repo.get("url", "")
                description = repo.get("description", "No description available")
                
                # Add repository to table
                content.append(f"| [{repo_name}]({repo_url}) | {description} |")
            else:
                # Repository not found in repo_data, add with limited info
                content.append(f"| {repo_name} | *Repository data not available* |")
        
        # Add spacing between categories
        content.append("\n")
    
    # Add navigation footer
    content.append("---\n")
    content.append("[← Back to Repository Index](../README.md)")
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write("\n".join(content))
    
    print(f"All categories page generated successfully at {output_file}")

if __name__ == "__main__":
    generate_all_categories_page()
