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

def build_readme(schema_path, output_path):
    """Build complete README from schema"""
    schema = load_hierarchy_schema(schema_path)

    # Header section
    readme_content = [
        "# Daniel Rosehill Github Repository Index\n",
        "![Banner](banners/index.png)\n",
        f"\n*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n",
        "\nThis is an automatically generated index of my public GitHub repositories.\n",
        "\n## Table of Contents\n",
        "- [Repository Views](#repository-views)",
        "- [Browse by Topic](#browse-by-topic)",
        "- [Browse by Time](#browse-by-time)",
        "- [Repository Statistics](#repository-statistics)",
        "- [Data Access & API](#data-access--api)\n",
        "\n## Repository Views\n",
        "This index provides multiple ways to explore my GitHub repositories:\n",
        "\n### Timeline View\n",
        "[![View Timeline](https://img.shields.io/badge/Timeline-4285F4?style=for-the-badge&logo=github&logoColor=white)](timeline.md)\n",
        "\nThe timeline provides a chronological view of all repositories, showing when each project was created and its current status.\n",
        "\n### All Categories\n",
        "[![All Categories](https://img.shields.io/badge/All_Categories-FF5722?style=for-the-badge&logo=github&logoColor=white)](sections/all-categories.md)\n",
        "\nView all categories in a single page.\n",
        "\n### Browse by Time\n",
        "[![Browse by Time](https://img.shields.io/badge/Browse_by_Time-9C27B0?style=for-the-badge&logo=github&logoColor=white)](sections/by-time/README.md)\n",
        "\nExplore repositories organized by year and month of creation.\n",
    ]

    # Add hierarchical browse by topic section
    readme_content.append("\n## Browse by Topic\n")
    readme_content.append("Explore repositories organized by topic and subtopic:\n")

    # Build hierarchy from schema
    if 'sections' in schema:
        hierarchy_content = build_hierarchy_section(schema['sections'])
        readme_content.append(hierarchy_content)

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
