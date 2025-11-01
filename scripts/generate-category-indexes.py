#!/usr/bin/env python3
"""
Generate index.md files for each category in the sections/by-topic directory.
Each index.md will contain a category overview with subtopics organized by headers.
"""

import os
from pathlib import Path


def get_display_name(filename):
    """Convert filename to display name (remove extension, capitalize)."""
    name = filename.replace('.md', '').replace('-', ' ').replace('_', ' ')
    return name.title()


def get_subdirectory_name(dirname):
    """Convert directory name to display name."""
    return dirname.replace('-', ' ').replace('_', ' ').title()


def generate_index_for_category(category_path):
    """Generate index.md for a specific category."""
    category_name = get_subdirectory_name(category_path.name)

    # Get all subdirectories and files
    subdirs = sorted([d for d in category_path.iterdir() if d.is_dir()])
    md_files = sorted([f for f in category_path.iterdir() if f.is_file() and f.suffix == '.md' and f.name != 'index.md'])

    # Build the index content
    lines = [
        f"# {category_name}",
        "",
        f"This section contains repositories related to {category_name.lower()}.",
        ""
    ]

    # Add subdirectories as sections
    for subdir in subdirs:
        section_name = get_subdirectory_name(subdir.name)
        lines.append(f"## {section_name}")
        lines.append("")

        # Add description placeholder
        lines.append(f"{section_name} related repositories.")
        lines.append("")

        # List all md files in this subdirectory
        subdir_files = sorted([f for f in subdir.iterdir() if f.is_file() and f.suffix == '.md'])
        for md_file in subdir_files:
            display_name = get_display_name(md_file.name)
            relative_path = f"{subdir.name}/{md_file.name}"
            lines.append(f"- [{display_name}]({relative_path})")

        lines.append("")

    # If there are direct .md files (no subdirectories), list them under "Topics"
    if md_files:
        lines.append("## Topics")
        lines.append("")
        for md_file in md_files:
            display_name = get_display_name(md_file.name)
            lines.append(f"- [{display_name}]({md_file.name})")
        lines.append("")

    # Write the index.md file
    index_path = category_path / 'index.md'
    with open(index_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f"✓ Created {index_path}")


def main():
    """Generate index.md files for all categories."""
    base_path = Path(__file__).parent.parent / 'sections' / 'by-topic'

    if not base_path.exists():
        print(f"Error: {base_path} does not exist")
        return

    # Get all category directories
    categories = sorted([d for d in base_path.iterdir() if d.is_dir()])

    print(f"Generating index.md files for {len(categories)} categories...\n")

    for category in categories:
        generate_index_for_category(category)

    print(f"\n✓ Successfully generated {len(categories)} index.md files")


if __name__ == '__main__':
    main()
