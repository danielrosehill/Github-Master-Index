#!/usr/bin/env python3
"""
Time-Based Repository Index Updater - Incremental Updates
Only creates/updates pages for months that don't exist or have new data
"""

import json
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set

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


class TimeIndexUpdater:
    def __init__(self):
        self.repos_by_month = defaultdict(list)
        self.existing_pages = set()

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

    def scan_existing_pages(self) -> Set[tuple]:
        """Scan for existing month pages and return set of (year, month) tuples"""
        print("\nScanning for existing time-based pages...")

        existing = set()

        if not TIME_SECTIONS_DIR.exists():
            print("No time sections directory found - will create all pages")
            return existing

        # Scan year directories
        for year_dir in TIME_SECTIONS_DIR.iterdir():
            if not year_dir.is_dir() or not year_dir.name.isdigit():
                continue

            year = int(year_dir.name)

            # Scan month files
            for month_file in year_dir.glob("*.md"):
                if month_file.name == "README.md":
                    continue

                # Parse filename: 01_25.md -> (2025, 1)
                try:
                    month_str, year_short = month_file.stem.split('_')
                    month = int(month_str)
                    existing.add((year, month))
                except (ValueError, StopIteration):
                    print(f"Warning: Could not parse {month_file.name}")
                    continue

        print(f"Found {len(existing)} existing month pages")
        return existing

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

        return file_path

    def update_year_index(self, year: int):
        """Update or create an index page for a year"""
        year_dir = TIME_SECTIONS_DIR / str(year)
        index_path = year_dir / "README.md"

        # Get all months for this year
        months = [month for y, month in self.repos_by_month.keys() if y == year]
        months.sort(reverse=True)

        content = f"# {year} Repository Index\n\n"
        content += f"Repositories created in {year}, organized by month.\n\n"
        content += "## Months\n\n"

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

    def update_main_time_index(self):
        """Update the main time-based index page"""
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

    def update_pages(self):
        """Update only new or modified pages"""
        print("\nUpdating time-based index pages...")
        print("="*60)

        # Get existing pages
        existing = self.scan_existing_pages()

        # Find new pages needed
        all_months = set(self.repos_by_month.keys())
        new_months = all_months - existing
        existing_months = all_months & existing

        print(f"\nPages to create: {len(new_months)}")
        print(f"Pages to update: {len(existing_months)}")

        created = 0
        updated = 0
        years_touched = set()

        # Create new month pages
        if new_months:
            print("\nCreating new month pages:")
            for year, month in sorted(new_months):
                repos = self.repos_by_month[(year, month)]
                file_path = self.create_month_page(year, month, repos)
                print(f"  Created: {file_path.relative_to(REPO_ROOT)} ({len(repos)} repos)")
                created += 1
                years_touched.add(year)

        # Update existing month pages
        if existing_months:
            print("\nUpdating existing month pages:")
            for year, month in sorted(existing_months):
                repos = self.repos_by_month[(year, month)]
                file_path = self.create_month_page(year, month, repos)
                print(f"  Updated: {file_path.relative_to(REPO_ROOT)} ({len(repos)} repos)")
                updated += 1
                years_touched.add(year)

        # Update year indexes for affected years
        if years_touched:
            print("\nUpdating year indexes:")
            for year in sorted(years_touched):
                self.update_year_index(year)
                print(f"  Updated: sections/by-time/{year}/README.md")

        # Update main index
        print("\nUpdating main time index:")
        self.update_main_time_index()
        print(f"  Updated: sections/by-time/README.md")

        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"New pages created: {created}")
        print(f"Existing pages updated: {updated}")
        print(f"Year indexes updated: {len(years_touched)}")
        print(f"Total repositories indexed: {sum(len(repos) for repos in self.repos_by_month.values())}")


def main():
    print("Time-Based Repository Index Updater - Incremental Mode")
    print("="*60)
    print()

    updater = TimeIndexUpdater()

    # Load repository data
    repos = updater.load_repo_data()
    if not repos:
        print("No repositories to process. Exiting.")
        return

    # Organize by month
    updater.organize_repos_by_month(repos)

    # Update pages (only new/changed)
    updater.update_pages()

    print("\n✓ Time-based index update complete!")


if __name__ == "__main__":
    main()
