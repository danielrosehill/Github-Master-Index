#!/usr/bin/env python3
"""
GitHub Repository Indexer
Pulls public repositories and identifies unindexed ones for categorization
"""

import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Configuration
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
SECTIONS_DIR = REPO_ROOT / "sections" / "by-topic"
REPO_DATA_DIR = REPO_ROOT / "repo-data"
HIERARCHY_FILE = SCRIPT_DIR / "hierarchy-schema.json"
GITHUB_USER = "danielrosehill"


class RepositoryIndexer:
    def __init__(self):
        self.hierarchy = self.load_hierarchy()
        self.indexed_repos = set()
        self.section_map = {}  # Maps section files to their paths

    def load_hierarchy(self) -> Dict:
        """Load the hierarchy schema"""
        with open(HIERARCHY_FILE, 'r') as f:
            return json.load(f)

    def pull_github_repos(self) -> List[Dict]:
        """Pull repository list from GitHub using gh CLI"""
        print(f"Pulling all public repositories for {GITHUB_USER}...")

        cmd = [
            "gh", "repo", "list", GITHUB_USER,
            "--limit", "1000",
            "--json", "name,description,url,updatedAt,isPrivate,repositoryTopics",
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

    def scan_existing_indexes(self) -> Set[str]:
        """Scan all markdown files to find already indexed repositories"""
        indexed = set()

        for md_file in SECTIONS_DIR.rglob("*.md"):
            try:
                with open(md_file, 'r') as f:
                    content = f.read()

                # Extract repo names from GitHub URLs
                # Matches: https://github.com/danielrosehill/Repo-Name
                pattern = rf'https://github\.com/{GITHUB_USER}/([a-zA-Z0-9_-]+)'
                matches = re.findall(pattern, content)
                indexed.update(matches)

                # Store which file contains which repos
                for repo in matches:
                    if repo not in self.section_map:
                        self.section_map[repo] = []
                    self.section_map[repo].append(str(md_file.relative_to(REPO_ROOT)))

            except Exception as e:
                print(f"Error reading {md_file}: {e}")

        print(f"Found {len(indexed)} already indexed repositories")
        return indexed

    def calculate_match_score(self, repo: Dict, section_keywords: List[str]) -> float:
        """Calculate how well a repository matches a section based on keywords"""
        score = 0.0

        # Combine repo name, description, and topics for matching
        topics = repo.get('repositoryTopics', []) or []
        topic_text = " ".join([topic.get('topic', '') for topic in topics if isinstance(topic, dict)])

        repo_text = " ".join([
            repo['name'].lower(),
            repo.get('description', '').lower() if repo.get('description') else '',
            topic_text.lower()
        ])

        # Count keyword matches
        for keyword in section_keywords:
            if keyword.lower() in repo_text:
                # Weight matches in name higher than description
                if keyword.lower() in repo['name'].lower():
                    score += 3.0
                else:
                    score += 1.0

        return score

    def find_best_section_file(self, repo: Dict) -> Tuple[str, float, str]:
        """Find the best matching section file for a repository"""
        best_match = None
        best_score = 0.0
        best_path = None

        def check_section(section_path: str, section_data: Dict, parent_keywords: List[str] = None):
            nonlocal best_match, best_score, best_path

            # Get keywords for this section
            keywords = section_data.get('keywords', [])
            if parent_keywords:
                keywords = parent_keywords + keywords

            # Check subsections
            if 'subsections' in section_data:
                for subsection_name, subsection_data in section_data['subsections'].items():
                    subsection_path = f"{section_path}/{subsection_name}"
                    check_section(subsection_path, subsection_data, keywords)

            # Check specific files if they exist
            if 'files' in section_data:
                for filename, file_keywords in section_data['files'].items():
                    all_keywords = keywords + file_keywords
                    score = self.calculate_match_score(repo, all_keywords)

                    if score > best_score:
                        best_score = score
                        best_match = filename
                        best_path = f"{section_path}/{filename}"

        # Check all top-level sections
        for section_name, section_data in self.hierarchy['sections'].items():
            check_section(f"sections/by-topic/{section_name}", section_data)

        return best_match, best_score, best_path

    def format_repo_entry(self, repo: Dict) -> str:
        """Format a repository as a markdown entry"""
        name = repo['name']
        description = repo.get('description', 'No description provided')
        url = repo['url']

        # Convert repo name to title case with spaces
        title = name.replace('-', ' ').replace('_', ' ').title()

        entry = f"\n## {title} [![View Repo](https://img.shields.io/badge/view-repo-green)]({url})\n"
        entry += f"{description}\n"

        return entry

    def add_repo_to_section(self, repo: Dict, section_file_path: str) -> bool:
        """Add a repository entry to a section file"""
        try:
            file_path = REPO_ROOT / section_file_path

            # Read existing content
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
            else:
                # Create new file with header
                section_name = file_path.stem.replace('-', ' ').title()
                content = f"# {section_name} Repositories\n"

            # Check if repo already exists
            if repo['name'] in content:
                print(f"  Repository {repo['name']} already in {section_file_path}")
                return False

            # Add repo entry
            entry = self.format_repo_entry(repo)
            content += entry

            # Write back
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"  Error adding repo to {section_file_path}: {e}")
            return False

    def process_unindexed_repos(self, repos: List[Dict], indexed: Set[str]) -> Dict:
        """Process unindexed repositories and categorize them"""
        unindexed = [repo for repo in repos if repo['name'] not in indexed]

        print(f"\nFound {len(unindexed)} unindexed repositories")

        results = {
            'total_unindexed': len(unindexed),
            'categorized': [],
            'low_confidence': [],
            'added': 0
        }

        for repo in unindexed:
            filename, score, path = self.find_best_section_file(repo)

            result_entry = {
                'repo': repo['name'],
                'description': repo.get('description', ''),
                'best_match': filename,
                'path': path,
                'score': score,
                'url': repo['url']
            }

            if score >= 2.0:  # High confidence threshold
                results['categorized'].append(result_entry)
                print(f"\n{repo['name']}:")
                print(f"  Best match: {path} (score: {score:.1f})")

                # Add to section file
                if path and self.add_repo_to_section(repo, path):
                    results['added'] += 1
                    print(f"  ✓ Added to {path}")

            else:  # Low confidence
                results['low_confidence'].append(result_entry)

        return results

    def save_report(self, results: Dict):
        """Save a report of the indexing process"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_file = SCRIPT_DIR / f"indexing-report-{timestamp}.json"

        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n\nReport saved to: {report_file}")

        # Print summary
        print("\n" + "="*60)
        print("INDEXING SUMMARY")
        print("="*60)
        print(f"Total unindexed repositories: {results['total_unindexed']}")
        print(f"Automatically categorized: {len(results['categorized'])}")
        print(f"Successfully added to sections: {results['added']}")
        print(f"Low confidence (need manual review): {len(results['low_confidence'])}")

        if results['low_confidence']:
            print("\n" + "-"*60)
            print("LOW CONFIDENCE MATCHES (manual review needed):")
            print("-"*60)
            for item in results['low_confidence']:
                print(f"\n{item['repo']}")
                print(f"  Description: {item['description'][:80]}...")
                print(f"  Best guess: {item['path']} (score: {item['score']:.1f})")
                print(f"  URL: {item['url']}")


def main():
    print("GitHub Repository Indexer")
    print("="*60)

    indexer = RepositoryIndexer()

    # Step 1: Pull latest repository list from GitHub
    repos = indexer.pull_github_repos()
    if not repos:
        print("Failed to pull repositories. Exiting.")
        return

    # Step 2: Scan existing indexes
    indexed = indexer.scan_existing_indexes()

    # Step 3: Process unindexed repositories
    results = indexer.process_unindexed_repos(repos, indexed)

    # Step 4: Save report
    indexer.save_report(results)


if __name__ == "__main__":
    main()
