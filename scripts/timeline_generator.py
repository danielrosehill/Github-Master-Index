import json
from datetime import datetime
import os

def generate_timeline():
    # Read the JSON data
    with open('data/exports/repo-index.json', 'r', encoding='utf-8') as f:
        repos = json.load(f)
    
    # Load repository annotations
    repo_annotations = load_repo_annotations()

    # Group repositories by year, month and date
    timeline = {}
    for repo in repos:
        created_at = datetime.strptime(repo['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        year = created_at.year
        month = created_at.strftime('%B')  # Full month name
        date_key = created_at.strftime('%-d %b')  # e.g., "22 Feb"
        
        if year not in timeline:
            timeline[year] = {}
        if month not in timeline[year]:
            timeline[year][month] = {}
        if date_key not in timeline[year][month]:
            timeline[year][month][date_key] = []
            
        timeline[year][month][date_key].append(repo)

    # Generate markdown content
    markdown_content = "# GitHub Repository Timeline\n\n"
    
    # Generate TOC
    markdown_content += "## Table of Contents\n\n"
    
    # Add TOC entries in reverse chronological order
    for year in sorted(timeline.keys(), reverse=True):
        markdown_content += f"- [{year}](#{year})\n"
        for month in sorted(timeline[year].keys(), reverse=True, 
                          key=lambda x: datetime.strptime(x, '%B').month):
            # Create a TOC-friendly anchor
            month_anchor = f"{year}-{month.lower()}"
            markdown_content += f"  - [{month} {year}](#{month_anchor})\n"
    
    markdown_content += "\n---\n\n"
    
    # Process years in reverse chronological order
    for year in sorted(timeline.keys(), reverse=True):
        markdown_content += f"# {year}\n\n"
        
        # Process months in reverse chronological order
        for month in sorted(timeline[year].keys(), reverse=True, 
                          key=lambda x: datetime.strptime(x, '%B').month):
            # Create a TOC-friendly anchor
            month_anchor = f"{year}-{month.lower()}"
            markdown_content += f"# {month} {year} <a id='{month_anchor}'></a>\n\n"
            
            # Process dates in reverse chronological order for each month
            for date in sorted(timeline[year][month].keys(), reverse=True, 
                             key=lambda x: datetime.strptime(x, '%d %b')):
                markdown_content += f"## {date}\n\n"
                
                # Add repositories for this date
                for i, repo in enumerate(timeline[year][month][date]):
                    name = repo['pretty_name']
                    desc = repo['description']
                    url = repo['url']
                    is_fork = repo['is_fork']
                    repo_name = repo['name']
                    
                    markdown_content += f"**{name}**\n\n"
                    
                    # Add badges for annotations
                    badges = []
                    
                    # Status indicators (with emoji)
                    if repo_name in repo_annotations.get('archived', []):
                        badges.append("🗄️ **Archived**")
                    elif repo_name in repo_annotations.get('abandoned', []):
                        badges.append("⚠️ **Abandoned**")
                    elif repo_name in repo_annotations.get('abandoned_for_now', []):
                        badges.append("⏸️ **Abandoned For Now**")
                    
                    # Badge annotations
                    if repo_name in repo_annotations.get('ai_generated', []):
                        badges.append("![AI Generated](https://img.shields.io/badge/AI_Generated-5A67D8?style=flat-square)")
                    if repo_name in repo_annotations.get('work_in_progress', []):
                        badges.append("![Work in Progress](https://img.shields.io/badge/WIP-FCD34D?style=flat-square)")
                    if repo_name in repo_annotations.get('one_time_project', []):
                        badges.append("![One-Time Project](https://img.shields.io/badge/One_Time-10B981?style=flat-square)")
                    
                    # Display badges if any
                    if badges:
                        markdown_content += " ".join(badges) + "\n\n"
                    
                    markdown_content += f"{desc}\n\n"
                    if is_fork:
                        markdown_content += "🔱 *This is a fork*\n\n"
                    markdown_content += f"[![GitHub Repository]"
                    markdown_content += f"(https://img.shields.io/badge/GitHub-Repository-blue)]"
                    markdown_content += f"({url})\n\n"
                    
                    # Add horizontal line between repositories, but not after the last one in a date group
                    if i < len(timeline[year][month][date]) - 1:
                        markdown_content += "---\n\n"

    # Save the timeline
    with open('timeline.md', 'w', encoding='utf-8') as f:
        f.write(markdown_content)

def load_repo_annotations():
    """Load repository annotations from data/repo_annotations.json"""
    annotations = {
        "ai_generated": [],
        "work_in_progress": [],
        "one_time_project": [],
        "abandoned_for_now": [],
        "abandoned": [],
        "archived": []
    }
    
    try:
        annotations_file = 'data/repo_annotations.json'
        if os.path.exists(annotations_file):
            with open(annotations_file, 'r') as f:
                data = json.load(f)
                if "annotations" in data:
                    annotations = data["annotations"]
    except Exception as e:
        print(f"Error loading repository annotations: {str(e)}")
        
    return annotations

if __name__ == "__main__":
    generate_timeline()