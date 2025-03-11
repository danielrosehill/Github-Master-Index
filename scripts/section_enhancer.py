import os
import json
import glob
from datetime import datetime

# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def enhance_section_files():
    """
    Enhance section markdown files with status badges and language information.
    """
    # Load status data if available
    status_data = {}
    status_path = os.path.join(project_root, 'data', 'exports', 'repo-status.json')
    
    if os.path.exists(status_path):
        try:
            with open(status_path, 'r') as f:
                status_data = json.load(f)
        except json.JSONDecodeError:
            print("Error parsing status data.")
    
    # Process each section file
    sections_dir = os.path.join(project_root, 'sections')
    for section_file in glob.glob(os.path.join(sections_dir, '*.md')):
        enhance_section_file(section_file, status_data)
    
    print(f"Enhanced section files with status badges and language information.")

def enhance_section_file(section_file, status_data):
    """
    Enhance a single section file with status badges and language information.
    """
    with open(section_file, 'r') as f:
        content = f.read()
    
    # Split content into lines
    lines = content.split('\n')
    enhanced_lines = []
    
    # Process each line
    for line in lines:
        if line.startswith('## ['):
            # This is a repository line
            repo_name = line.split('](')[0][3:]  # Extract repo name from markdown link
            
            # Get status and language if available
            repo_info = status_data.get(repo_name, {})
            status = repo_info.get('status', 'unknown')
            language = repo_info.get('language', 'Unknown')
            
            # Create status badge
            if status == 'active':
                status_badge = '![Active](https://img.shields.io/badge/Status-Active-success)'
            elif status == 'archived':
                status_badge = '![Archived](https://img.shields.io/badge/Status-Archived-lightgrey)'
            elif status == 'inactive':
                status_badge = '![Inactive](https://img.shields.io/badge/Status-Inactive-yellow)'
            elif status == 'stale':
                status_badge = '![Stale](https://img.shields.io/badge/Status-Stale-orange)'
            else:
                status_badge = ''
            
            # Create language badge if available
            lang_badge = f'![{language}](https://img.shields.io/badge/Language-{language}-blue)' if language and language != 'Unknown' else ''
            
            # Add badges to line
            badges = ' '.join(filter(None, [status_badge, lang_badge]))
            if badges:
                enhanced_line = f"{line} {badges}"
            else:
                enhanced_line = line
            
            enhanced_lines.append(enhanced_line)
        else:
            # Keep other lines unchanged
            enhanced_lines.append(line)
    
    # Write enhanced content back to file
    with open(section_file, 'w') as f:
        f.write('\n'.join(enhanced_lines))

if __name__ == "__main__":
    enhance_section_files()
