#!/usr/bin/env python3
"""
Build hierarchical README from hierarchy schema with badge links
"""

import json
from pathlib import Path
from datetime import datetime

def load_hierarchy_schema(schema_path):
    """Load the hierarchy schema JSON"""
    with open(schema_path, 'r') as f:
        return json.load(f)

def format_title_for_badge(title):
    """Format title for badge display (replace spaces with underscores)"""
    return title.replace(' ', '_')

def format_section_name(name):
    """Format section name for display"""
    return name.replace('-', ' ').title()

def build_hierarchy_section(sections, base_path="sections/by-topic"):
    """Build the hierarchical README content with badges and category index links"""
    content = []

    for section_key, section_data in sorted(sections.items()):
        section_name = section_data.get('name', format_section_name(section_key))

        # Main section header (##)
        content.append(f"\n## {section_name}\n")

        if 'description' in section_data:
            content.append(f"*{section_data['description']}*\n")

        # Add link to category index
        category_index_path = f"{base_path}/{section_key}/index.md"
        content.append(f"\n**[View Complete {section_name} Index]({category_index_path})**\n")

        # Check if section has subsections
        if 'subsections' in section_data:
            for subsection_key, subsection_data in sorted(section_data['subsections'].items()):
                subsection_name = subsection_data.get('name', format_section_name(subsection_key))

                # Subsection header (####)
                content.append(f"\n#### {subsection_name}\n")

                if 'description' in subsection_data:
                    content.append(f"*{subsection_data['description']}*\n")

                # Add badges for files in subsection
                if 'files' in subsection_data:
                    content.append("\n")
                    for file_name in sorted(subsection_data['files'].keys()):
                        file_title = file_name.replace('.md', '').replace('-', ' ').title()
                        badge_title = format_title_for_badge(file_title)
                        file_path = f"{base_path}/{section_key}/{subsection_key}/{file_name}"

                        badge = f"[![{file_title}](https://img.shields.io/badge/{badge_title}-2ea44f?style=for-the-badge&logo=github)]({file_path})"
                        content.append(f"{badge}<br>")
                    content.append("\n")

        # If section has direct files (no subsections)
        elif 'files' in section_data:
            content.append("\n")
            for file_name in sorted(section_data['files'].keys()):
                file_title = file_name.replace('.md', '').replace('-', ' ').title()
                badge_title = format_title_for_badge(file_title)
                file_path = f"{base_path}/{section_key}/{file_name}"

                badge = f"[![{file_title}](https://img.shields.io/badge/{badge_title}-2ea44f?style=for-the-badge&logo=github)]({file_path})"
                content.append(f"{badge}<br>")
            content.append("\n")

    return '\n'.join(content)

def build_category_summary(sections, base_path="sections/by-topic"):
    """Build a concise category summary with just main category links"""
    content = []

    for section_key, section_data in sorted(sections.items()):
        section_name = section_data.get('name', format_section_name(section_key))
        description = section_data.get('description', '')
        category_index_path = f"{base_path}/{section_key}/index.md"

        content.append(f"| [{section_name}]({category_index_path}) | {description} |")

    return '\n'.join(content)

def build_readme(schema_path, output_path):
    """Build complete README from schema"""
    schema = load_hierarchy_schema(schema_path)

    # Header section - simplified without table of contents
    readme_content = [
        "# Daniel Rosehill Github Repository Index\n",
        "![Banner](banners/index.png)\n",
        f"\n*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n",
        "\nThis is an automatically generated index of my public GitHub repositories.\n",
        "\n---\n",
        "\n## Index of Indexes\n",
        "I maintain several specialized indexes for different project categories. View the complete list:\n",
        "\n[![Index of Indexes](https://img.shields.io/badge/View_Index_of_Indexes-FF6B6B?style=for-the-badge&logo=github&logoColor=white)](https://github.com/danielrosehill/Index-Of-Indices)\n",
        "\n---\n",
        "\n## Repository Views\n",
        "This index provides multiple ways to explore my GitHub repositories:\n",
        "\n| View | Description |",
        "| ---- | ----------- |",
        "| [![Full Index](https://img.shields.io/badge/Full_Index-4285F4?style=flat-square&logo=github&logoColor=white)](index.md) | All repositories sorted by update date |",
        "| [![Browse by Time](https://img.shields.io/badge/By_Time-9C27B0?style=flat-square&logo=github&logoColor=white)](sections/by-time/README.md) | Explore by year and month of creation |\n",
        "\n---\n",
        "\n## Browse by Topic\n",
        "Explore repositories organized by topic:\n",
        "\n| Category | Description |",
        "| -------- | ----------- |",
    ]

    # Build concise category summary table
    if 'sections' in schema:
        category_table = build_category_summary(schema['sections'])
        readme_content.append(category_table)

    # Footer sections
    readme_content.extend([
        "\n## Repository Statistics\n",
        "**Total Repositories:** [Count updated dynamically]\n",
        "\n**Top Categories:**\n",
        "[Statistics updated dynamically]\n",
        "\n---\n",
        "\n## Data Access & API\n",
        "This repository provides multiple ways to access the data programmatically:\n",
        "\n### Data Exports\n",
        "Direct file downloads:",
        "- [Repository Index (JSON)](data/exports/repo-index.json)",
        "- [Repository Index (CSV)](data/exports/repo-index.csv)\n",
        "\n### API Endpoints\n",
        "When accessed through GitHub Pages:",
        "```",
        "# Complete repository data in JSON format",
        "https://danielrosehill.github.io/Github-Timeline/data/exports/repo-index.json\n",
        "# Category-specific repository lists",
        "https://danielrosehill.github.io/Github-Timeline/lists/categories/{category-name}.txt",
        "```\n",
        "\n### Documentation\n",
        "For detailed API documentation and usage examples:",
        "- [Interactive API Documentation](https://danielrosehill.github.io/Github-Timeline/)",
        "- [API Usage Examples](examples/api-usage.md)\n",
        "\nThe data is automatically updated whenever the repository is updated.\n"
    ])

    # Write README
    with open(output_path, 'w') as f:
        f.write('\n'.join(readme_content))

    print(f"✓ README built successfully: {output_path}")

if __name__ == "__main__":
    # Paths
    base_dir = Path(__file__).parent.parent
    schema_path = base_dir / "scripts" / "hierarchy-schema.json"
    output_path = base_dir / "README.md"

    print("Building hierarchical README...")
    print(f"Schema: {schema_path}")
    print(f"Output: {output_path}")

    build_readme(schema_path, output_path)
