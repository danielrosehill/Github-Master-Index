#!/usr/bin/env python3
"""
Script to consolidate similar categories in the repository index.
This script merges similar categories to avoid fragmentation.
"""

import argparse
from scripts.llm_categorizer import LLMCategorizer

def main():
    """Main function to consolidate categories"""
    parser = argparse.ArgumentParser(description="Consolidate similar categories")
    parser.add_argument("--dry-run", action="store_true", 
                        help="Show what would be done without making changes")
    parser.add_argument("--force", action="store_true",
                        help="Force consolidation without confirmation")
    args = parser.parse_args()
    
    # Initialize the categorizer
    categorizer = LLMCategorizer()
    
    # Get similar categories
    print("Analyzing categories for potential consolidation...")
    
    if args.dry_run:
        print("\nDRY RUN MODE - No changes will be made")
        
        # Get all category files
        categories_dir = categorizer.base_path / "lists" / "categories"
        category_files = list(categories_dir.glob("*.txt"))
        
        # Map of category names to their file paths
        category_map = {cat_file.stem: cat_file for cat_file in category_files}
        
        # Count repositories in each category
        category_counts = {}
        for category, file_path in category_map.items():
            with open(file_path, "r") as f:
                repos = [line.strip() for line in f if line.strip()]
                category_counts[category] = len(repos)
        
        # Define similar category pairs to merge
        similar_pairs = [
            # Programming languages and their tools
            ("python", "python-tools"),
            ("javascript", "javascript-tools"),
            ("typescript", "typescript-tools"),
            ("go", "go-tools"),
            ("rust", "rust-tools"),
            
            # UI/GUI related
            ("ui", "user-interface"),
            ("gui", "gui-tools"),
            ("gui", "gui-utilities"),
            
            # AI related
            ("ai", "ai-tools"),
            ("ai-tools", "ai-utilities"),
            ("machine-learning", "ml"),
            
            # Utilities and tools
            ("utilities", "tools"),
            ("utility", "utilities"),
            
            # Web related
            ("web", "web-tools"),
            ("web-development", "web-dev"),
            
            # Data related
            ("data", "data-tools"),
            ("data-processing", "data-tools"),
            
            # Development related
            ("dev-tools", "development-tools"),
            ("developer-tools", "development-tools"),
        ]
        
        # Check each pair
        potential_merges = []
        for primary, secondary in similar_pairs:
            # Skip if either category doesn't exist
            if primary not in category_map or secondary not in category_map:
                continue
                
            # Determine which category has more repositories
            primary_count = category_counts.get(primary, 0)
            secondary_count = category_counts.get(secondary, 0)
            
            # The category with more repos becomes the target
            if primary_count >= secondary_count:
                source = secondary
                target = primary
            else:
                source = primary
                target = secondary
                
            # Add to potential merges
            potential_merges.append((source, target, category_counts.get(source, 0), category_counts.get(target, 0)))
        
        if potential_merges:
            print("\nPotential category merges:")
            for source, target, source_count, target_count in potential_merges:
                print(f"- '{source}' ({source_count} repos) -> '{target}' ({target_count} repos)")
        else:
            print("\nNo similar categories found to consolidate.")
        
        return 0
    
    # Confirm before proceeding
    if not args.force:
        confirm = input("\nReady to consolidate similar categories. Proceed? (y/n): ").lower()
        if confirm != 'y':
            print("Operation cancelled by user.")
            return 0
    
    # Perform consolidation
    categorizer.consolidate_similar_categories()
    
    return 0

if __name__ == "__main__":
    exit(main())
