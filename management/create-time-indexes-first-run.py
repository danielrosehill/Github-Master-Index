#!/usr/bin/env python3
"""
Time-Based Repository Index Generator - First Run
Creates all historical time-based index pages from repository data
"""

import json
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

# Configuration
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
TIME_SECTIONS_DIR = REPO_ROOT / "sections" / "by-time"
# Find the most recent repo data file
import glob
repo_data_files = glob.glob(str(REPO_ROOT / "repo-data" / "all-repos-*.json"))
REPO_DATA_FILE = Path(max(repo_data_files)) if repo_data_files else REPO_ROOT / "repo-data" / "all-repos.json"

# Month abbreviations
MONTH_ABBREV = {
    1: 'jan', 2: 'feb', 3: 'mar', 4: 'apr', 5: 'may', 6: 'jun',
    7: 'jul', 8: 'aug', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dec'
}

MONTH_FULL = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
    7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'
}


class TimeIndexGenerator:
    def __init__(self):
        self.repos_by_month = defaultdict(list)

    def load_repo_data(self) -> List[Dict]:
        """Load repository data from JSON file"""
        print(f"Loading repository data from {REPO_DATA_FILE}")

        if not REPO_DATA_FILE.exists():
            print(f"Error: Repository data file not found at {REPO_DATA_FILE}")
            return []

        with open(REPO_DATA_FILE, 'r') as f:
            repos = json.load(f)

        print(f"Loaded {len(repos)} repositories")
        return repos

    def parse_update_date(self, date_string: str) -> tuple:
        """Parse ISO date string and return (year, month, datetime object)"""
        # Format: "2025-10-22T16:49:48Z"
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.year, dt.month, dt

    def organize_repos_by_month(self, repos: List[Dict]):
        """Organize repositories by their creation month"""
        print("\nOrganizing repositories by creation month...")

        for repo in repos:
            created_at = repo.get('createdAt')
            if not created_at:
                continue

            year, month, dt = self.parse_update_date(created_at)
            key = (year, month)

            self.repos_by_month[key].append({
                'name': repo['name'],
                'description': repo.get('description', 'No description provided'),
                'url': repo['url'],
                'created_at': dt,
                'topics': repo.get('repositoryTopics', []) or []
            })

        # Sort repos within each month by creation date (newest first)
        for key in self.repos_by_month:
            self.repos_by_month[key].sort(key=lambda x: x['created_at'], reverse=True)

        print(f"Organized into {len(self.repos_by_month)} unique month/year combinations")

    def format_repo_entry(self, repo: Dict) -> str:
        """Format a repository as a markdown entry"""
        name = repo['name']
        description = repo['description']
        url = repo['url']
        created = repo['created_at'].strftime('%Y-%m-%d')

        # Convert repo name to title case with spaces
        title = name.replace('-', ' ').replace('_', ' ').title()

        entry = f"\n## {title}\n\n"
        entry += f"[![View Repo](https://img.shields.io/badge/view-repo-green)]({url})\n\n"
        entry += f"**Created:** {created}\n\n"
        entry += f"{description}\n"

        # Add topics if available
        if repo['topics']:
            topics = [t.get('name', '') for t in repo['topics'] if isinstance(t, dict)]
            if topics:
                topic_badges = ' '.join([f"`{t}`" for t in topics])
                entry += f"\n**Topics:** {topic_badges}\n"

        return entry

    def create_month_page(self, year: int, month: int, repos: List[Dict]) -> Path:
        """Create a markdown page for a specific month"""
        month_num = f"{month:02d}"  # Zero-padded month number
        year_short = str(year)[2:]  # Last 2 digits of year
        filename = f"{month_num}_{year_short}.md"

        # Create year directory if it doesn't exist
        year_dir = TIME_SECTIONS_DIR / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)

        file_path = year_dir / filename

        # Create page content
        month_name = MONTH_FULL[month]
        content = f"# Repositories Created in {month_name} {year}\n\n"
        content += f"This page lists all repositories that were created in {month_name} {year}.\n\n"
        content += f"**Total Repositories:** {len(repos)}\n\n"
        content += "---\n"

        # Add repository entries
        for repo in repos:
            content += self.format_repo_entry(repo)
            content += "\n---\n"

        # Add navigation footer
        content += f"\n\n## Navigation\n\n"
        content += f"- [Back to All Categories](../../all-categories.md)\n"
        content += f"- [Back to Topic Index](../by-topic/)\n"
        content += f"- [Back to {year} Overview](./)\n"

        # Write file
        with open(file_path, 'w') as f:
            f.write(content)

        print(f"Created: {file_path.relative_to(REPO_ROOT)} ({len(repos)} repos)")
        return file_path

    def create_year_index(self, year: int, months: List[int]):
        """Create an index page for a year"""
        year_dir = TIME_SECTIONS_DIR / str(year)
        index_path = year_dir / "README.md"

        content = f"# {year} Repository Index\n\n"
        content += f"Repositories created in {year}, organized by month.\n\n"
        content += "## Months\n\n"

        # Sort months in reverse order (newest first)
        months.sort(reverse=True)

        for month in months:
            month_num = f"{month:02d}"
            year_short = str(year)[2:]
            month_name = MONTH_FULL[month]
            filename = f"{month_num}_{year_short}.md"
            repo_count = len(self.repos_by_month[(year, month)])

            content += f"- [{month_name} {year}](./{filename}) ({month_num}_{year_short}.md) - {repo_count} repositories\n"

        # Add navigation
        content += f"\n\n## Navigation\n\n"
        content += f"- [Back to All Categories](../all-categories.md)\n"
        content += f"- [Back to Topic Index](../by-topic/)\n"
        content += f"- [Back to Time Index](./)\n"

        with open(index_path, 'w') as f:
            f.write(content)

        print(f"Created year index: {index_path.relative_to(REPO_ROOT)}")

    def create_main_time_index(self):
        """Create the main time-based index page"""
        index_path = TIME_SECTIONS_DIR / "README.md"

        # Get all years and sort
        years = sorted(set(year for year, month in self.repos_by_month.keys()), reverse=True)

        content = "# Repositories by Time\n\n"
        content += "Browse repositories organized by their creation date.\n\n"
        content += "## Years\n\n"

        for year in years:
            year_months = [month for y, month in self.repos_by_month.keys() if y == year]
            total_repos = sum(len(self.repos_by_month[(year, month)]) for month in year_months)
            content += f"- [{year}](./{year}/) - {total_repos} repositories across {len(year_months)} months\n"

        # Add navigation
        content += f"\n\n## Navigation\n\n"
        content += f"- [Back to All Categories](../all-categories.md)\n"
        content += f"- [Topic Index](../by-topic/)\n"

        with open(index_path, 'w') as f:
            f.write(content)

        print(f"\nCreated main time index: {index_path.relative_to(REPO_ROOT)}")

    def generate_all_pages(self):
        """Generate all time-based index pages"""
        print("\nGenerating time-based index pages...")
        print("="*60)

        # Track years for creating year indexes
        years_months = defaultdict(list)

        # Create individual month pages
        for (year, month), repos in sorted(self.repos_by_month.items()):
            self.create_month_page(year, month, repos)
            years_months[year].append(month)

        print("\n" + "="*60)
        print("Creating year index pages...")
        print("="*60)

        # Create year indexes
        for year, months in years_months.items():
            self.create_year_index(year, months)

        # Create main time index
        print("\n" + "="*60)
        self.create_main_time_index()

        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total months: {len(self.repos_by_month)}")
        print(f"Total years: {len(years_months)}")
        print(f"Total repositories indexed: {sum(len(repos) for repos in self.repos_by_month.values())}")


def main():
    print("Time-Based Repository Index Generator - First Run")
    print("="*60)
    print()

    generator = TimeIndexGenerator()

    # Load repository data
    repos = generator.load_repo_data()
    if not repos:
        print("No repositories to process. Exiting.")
        return

    # Organize by month
    generator.organize_repos_by_month(repos)

    # Generate all pages
    generator.generate_all_pages()

    print("\n✓ Time-based index generation complete!")


if __name__ == "__main__":
    main()
