import os
from datetime import datetime
import math

# Get the project root directory (parent of scripts directory)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def generate_project_type_badges():
    """Generate badges for project types in a markdown table."""
    project_types = [
        "Created CLIs", "Created GUIs", "Documentation", "Experiments",
        "Forks", "Ideas", "Indexes", "Lists", "Templates", "Streamlit Apps",
        "Data", "Wrappers"
    ]
    
    table = ['| Type | Type |', '|----------|----------|']
    rows = math.ceil(len(project_types) / 2)
    
    for i in range(0, rows):
        row = []
        # First column
        display_name = project_types[i]
        file_name = display_name.lower().replace(" ", "-")
        badge = f'[![{display_name}](https://img.shields.io/badge/{display_name.replace(" ", "_")}-0D47A1?style=for-the-badge&logo=github)](sections/{file_name}.md)'
        row.append(badge)
        
        # Second column
        second_idx = i + rows
        if second_idx < len(project_types):
            display_name = project_types[second_idx]
            file_name = display_name.lower().replace(" ", "-")
            badge = f'[![{display_name}](https://img.shields.io/badge/{display_name.replace(" ", "_")}-0D47A1?style=for-the-badge&logo=github)](sections/{file_name}.md)'
            row.append(badge)
        else:
            row.append('')
            
        table.append(f'| {row[0]} | {row[1]} |')
    
    return '\n'.join(table)

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
    
    # Generate section badges in a proper markdown table
    # 2 columns for better readability
    section_table = ['| Category | Category |', '|----------|----------|']  # Restored header for proper table formatting
    
    # Calculate rows needed for 2 columns
    rows = math.ceil(len(section_files) / 2)
    
    for i in range(0, rows):
        row = []
        # First column
        display_name = section_files[i].replace('-', ' ').title()
        badge = f'[![{display_name}](https://img.shields.io/badge/{display_name.replace(" ", "_")}-2ea44f?style=for-the-badge&logo=github)](sections/{section_files[i]}.md)'
        row.append(badge)
        
        # Second column
        second_idx = i + rows
        if second_idx < len(section_files):
            display_name = section_files[second_idx].replace('-', ' ').title()
            badge = f'[![{display_name}](https://img.shields.io/badge/{display_name.replace(" ", "_")}-2ea44f?style=for-the-badge&logo=github)](sections/{section_files[second_idx]}.md)'
            row.append(badge)
        else:
            row.append('')  # Empty cell for last row if odd number
            
        section_table.append(f'| {row[0]} | {row[1]} |')

    # Get current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Generate project type badges
    project_type_table = generate_project_type_badges()

    # Generate README content
    readme_content = f"""# Daniel Rosehill Github Repository Index

![Banner](banners/index.png)

*Last updated: {timestamp}*

This is an automatically generated index of my public GitHub repositories.

## Repository Views

This index provides two ways to explore my GitHub repositories:

### 1. Chronological Timeline
[![View Timeline](https://img.shields.io/badge/Timeline-blue?style=for-the-badge&logo=github)](timeline.md)

The timeline provides a chronological view of all repositories, showing when each project was created and its current status. This is useful for seeing how my work and interests have evolved over time.

### 2. Projects By Type
Browse repositories by their type:

{project_type_table}

### 3. Category Index
The category index organizes repositories by their primary function or topic. Each category below contains a curated list of related projects:

{chr(10).join(section_table)}

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