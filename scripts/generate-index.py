#!/usr/bin/env python3
"""
Repository Index Generator
Generates index.md with all repositories sorted by update date (newest to oldest)
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# Configuration
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
REPO_DATA_DIR = REPO_ROOT / "repo-data"
INDEX_FILE = REPO_ROOT / "index.md"
GITHUB_USER = "danielrosehill"


class IndexGenerator:
    def __init__(self):
        self.repos = []

    def pull_github_repos(self) -> List[Dict]:
        """Pull repository list from GitHub using gh CLI"""
        print(f"Pulling all public repositories for {GITHUB_USER}...")

        cmd = [
            "gh", "repo", "list", GITHUB_USER,
            "--limit", "1000",
            "--json", "name,description,url,updatedAt,createdAt,isPrivate,repositoryTopics,stargazerCount,forkCount",
            "--public"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            repos = json.loads(result.stdout)
            print(f"Successfully pulled {len(repos)} repositories")

            # Save to timestamped file
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            output_file = REPO_DATA_DIR / f"all-repos-{timestamp}.json"
            REPO_DATA_DIR.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w') as f:
                json.dump(repos, f, indent=2)

            # Create symlink to latest
            latest_link = REPO_DATA_DIR / "latest.json"
            if latest_link.exists() or latest_link.is_symlink():
                latest_link.unlink()
            latest_link.symlink_to(output_file.name)

            print(f"Repository data saved to: {output_file}")
            return repos

        except subprocess.CalledProcessError as e:
            print(f"Error pulling repositories: {e}")
            print(f"stderr: {e.stderr}")
            return []

    def load_latest_data(self) -> List[Dict]:
        """Load the latest repository data from disk"""
        latest_file = REPO_DATA_DIR / "latest.json"

        if not latest_file.exists():
            print("No cached repository data found. Pulling from GitHub...")
            return self.pull_github_repos()

        print(f"Loading repository data from {latest_file}")
        with open(latest_file, 'r') as f:
            return json.load(f)

    def format_date(self, iso_date: str) -> str:
        """Format ISO date to readable format"""
        dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
        return dt.strftime("%B %d, %Y")

    def generate_index(self, repos: List[Dict]) -> str:
        """Generate the index.md content"""
        # Sort by updatedAt (newest first)
        sorted_repos = sorted(repos, key=lambda x: x['updatedAt'], reverse=True)

        # Build markdown content
        content = f"# GitHub Repository Index\n\n"
        content += f"**Total Repositories:** {len(repos)}  \n"
        content += f"**Last Updated:** {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}  \n"
        content += f"**GitHub User:** [{GITHUB_USER}](https://github.com/{GITHUB_USER})\n\n"
        content += "---\n\n"
        content += "## Repositories (Newest to Oldest)\n\n"

        for repo in sorted_repos:
            name = repo['name']
            description = repo.get('description') or '*No description provided*'
            url = repo['url']
            updated = self.format_date(repo['updatedAt'])
            created = self.format_date(repo['createdAt'])
            stars = repo.get('stargazerCount', 0)
            forks = repo.get('forkCount', 0)

            # Get topics
            topics = repo.get('repositoryTopics', []) or []
            topic_names = [topic.get('topic', '') for topic in topics if isinstance(topic, dict)]

            # Format title
            title = name.replace('-', ' ').replace('_', ' ').title()

            content += f"### [{title}]({url})\n\n"
            content += f"{description}\n\n"
            content += f"**Updated:** {updated} | **Created:** {created}  \n"

            if stars > 0 or forks > 0:
                content += f"⭐ {stars} stars | 🔀 {forks} forks  \n"

            if topic_names:
                topics_str = " ".join([f"`{topic}`" for topic in topic_names])
                content += f"**Topics:** {topics_str}  \n"

            content += f"\n---\n\n"

        return content

    def save_index(self, content: str):
        """Save the index to index.md"""
        with open(INDEX_FILE, 'w') as f:
            f.write(content)
        print(f"\nIndex generated successfully: {INDEX_FILE}")

    def run(self, refresh: bool = False):
        """Main execution flow"""
        print("GitHub Repository Index Generator")
        print("=" * 60)

        # Load or pull repository data
        if refresh:
            repos = self.pull_github_repos()
        else:
            repos = self.load_latest_data()

        if not repos:
            print("No repository data available. Exiting.")
            return

        # Generate index
        print(f"\nGenerating index for {len(repos)} repositories...")
        content = self.generate_index(repos)

        # Save to file
        self.save_index(content)

        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Total repositories indexed: {len(repos)}")
        print(f"Index file: {INDEX_FILE}")
        print(f"Data source: {REPO_DATA_DIR / 'latest.json'}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Generate repository index')
    parser.add_argument('--refresh', action='store_true',
                       help='Pull fresh data from GitHub instead of using cached data')

    args = parser.parse_args()

    generator = IndexGenerator()
    generator.run(refresh=args.refresh)


if __name__ == "__main__":
    main()
