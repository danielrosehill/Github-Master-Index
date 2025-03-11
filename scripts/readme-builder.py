import os
from datetime import datetime
import math
import json
import glob

# Get the project root directory (parent of scripts directory)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def generate_project_type_badges():
    """Generate badges for project types in a single-row layout."""
    project_types = [
        "Created CLIs", "Created GUIs", "Documentation", "Experiments",
        "Forks", "Ideas", "Indexes", "Lists", "Templates", "Streamlit Apps",
        "Data", "Wrappers"
    ]
    
    badges = []
    
    for display_name in project_types:
        file_name = display_name.lower().replace(" ", "-")
        badge = f'[![{display_name}](https://img.shields.io/badge/{display_name.replace(" ", "_")}-0D47A1?style=for-the-badge&logo=github)](sections/{file_name}.md)'
        badges.append(f'- {badge}')
    
    return '\n'.join(badges)

def generate_repository_statistics():
    """Generate statistics about the repositories."""
    # Count total repositories
    all_repos = set()
    category_counts = {}
    
    # Count repositories in each category
    categories_dir = os.path.join(project_root, 'lists', 'categories')
    for category_file in glob.glob(os.path.join(categories_dir, '*.txt')):
        category_name = os.path.basename(category_file)[:-4]  # Remove .txt extension
        with open(category_file, 'r') as f:
            repos = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            category_counts[category_name] = len(repos)
            all_repos.update(repos)
    
    # Sort categories by count (descending)
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Generate statistics section
    stats = [
        f"## Repository Statistics\n",
        f"**Total Repositories:** {len(all_repos)}\n",
        f"**Top Categories:**"
    ]
    
    # Add top 5 categories
    for category, count in sorted_categories[:5]:
        display_name = category.replace('-', ' ').title()
        stats.append(f"- {display_name}: {count} repositories")
    
    return '\n'.join(stats)

def generate_readme():
    """Generate a simplified README with links to timeline and section indexes."""
    
    # Get list of section files and filter out the ones that are now in types
    sections_dir = os.path.join(project_root, 'sections')
    type_categories = {
        'created-clis.md', 'created-guis.md', 'documentation.md', 
        'experiments.md', 'forks.md', 'ideas.md', 'indexes.md', 'lists.md', 
        'templates.md', 'streamlit-apps.md', 'data.md', 'wrappers.md'
    }
    section_files = sorted([f[:-3] for f in os.listdir(sections_dir) 
                          if f.endswith('.md') and f not in type_categories])
    
    # Generate section badges in a single-row layout
    section_badges = []
    
    for section in section_files:
        display_name = section.replace('-', ' ').title()
        badge = f'[![{display_name}](https://img.shields.io/badge/{display_name.replace(" ", "_")}-2ea44f?style=for-the-badge&logo=github)](sections/{section}.md)'
        section_badges.append(f'- {badge}')

    # Get current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Generate project type badges
    project_type_list = generate_project_type_badges()
    
    # Generate repository statistics
    repo_stats = generate_repository_statistics()

    # Generate README content
    readme_content = f"""# Daniel Rosehill Github Repository Index

![Banner](banners/index.png)

*Last updated: {timestamp}*

This is an automatically generated index of my public GitHub repositories.

{repo_stats}

## Repository Views

This index provides multiple ways to explore my GitHub repositories:

## View Timeline
[![View Timeline](https://img.shields.io/badge/Timeline-4285F4?style=for-the-badge&logo=github&logoColor=white)](timeline.md)

The timeline provides a chronological view of all repositories, showing when each project was created and its current status. This is useful for seeing how my work and interests have evolved over time.

## By Type
Browse repositories by their project type:

{project_type_list}

## By Category
Browse repositories organized by their primary function or topic:

{chr(10).join(section_badges)}

---

## Data Access & API

This repository provides multiple ways to access the data programmatically:

### Data Exports
Direct file downloads:
- [Repository Index (JSON)](data/exports/repo-index.json)
- [Repository Index (CSV)](data/exports/repo-index.csv)

### API Endpoints
When accessed through GitHub Pages:
```
# Complete repository data in JSON format
https://danielrosehill.github.io/Github-Timeline/data/exports/repo-index.json

# Category-specific repository lists
https://danielrosehill.github.io/Github-Timeline/lists/categories/{{category-name}}.txt
```

### Documentation
For detailed API documentation and usage examples:
- [Interactive API Documentation](https://danielrosehill.github.io/Github-Timeline/)
- [API Usage Examples](examples/api-usage.md)

The data is automatically updated whenever the repository is updated."""

    # Write README to file
    readme_path = os.path.join(project_root, 'README.md')
    with open(readme_path, 'w') as f:
        f.write(readme_content)

if __name__ == '__main__':
    generate_readme()