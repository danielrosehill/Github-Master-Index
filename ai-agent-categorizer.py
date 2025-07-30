#!/usr/bin/env python3
"""
Enhanced AI Agent for Automated Repository Categorization and Index Management

This script provides an intelligent agent that:
1. Fetches updated repository data from GitHub
2. Categorizes repositories using LLM analysis
3. Updates index repositories automatically
4. Maintains the master index structure
5. Generates reports and analytics

Usage:
    python ai-agent-categorizer.py --full-update
    python ai-agent-categorizer.py --categorize-only
    python ai-agent-categorizer.py --update-indexes-only
"""

import os
import json
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

# Import existing categorizer
from scripts.llm_categorizer import LLMCategorizer

@dataclass
class RepositoryInfo:
    """Enhanced repository information structure"""
    name: str
    description: str
    url: str
    created_at: str
    updated_at: str
    language: str
    topics: List[str]
    stars: int
    forks: int
    is_fork: bool
    size: int
    readme_content: Optional[str] = None
    suggested_categories: List[str] = None
    confidence_scores: Dict[str, float] = None

class EnhancedAIAgent:
    """Enhanced AI Agent for repository management and categorization"""
    
    def __init__(self, config_path: str = None):
        """Initialize the AI agent with configuration"""
        load_dotenv()
        
        self.base_path = Path(__file__).parent
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.categorizer = LLMCategorizer()
        self.github_token = os.getenv("GITHUB_PAT")
        self.github_username = self._get_github_username()
        
        # Create necessary directories
        self._ensure_directories()
        
        # Load existing data
        self.existing_repos = self._load_existing_repositories()
        self.index_repositories = self._load_index_repositories()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            "categorization": {
                "min_confidence": 80,
                "batch_size": 10,
                "request_delay": 2,
                "max_retries": 3
            },
            "github": {
                "fetch_readme": True,
                "include_forks": False,
                "max_repos": None
            },
            "index_management": {
                "auto_create_indexes": True,
                "consolidate_categories": True,
                "update_statistics": True
            },
            "reporting": {
                "generate_reports": True,
                "send_notifications": False,
                "report_format": "json"
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                # Merge with defaults
                default_config.update(user_config)
        
        return default_config
    
    def _ensure_directories(self):
        """Create necessary directories"""
        dirs = [
            self.base_path / "reports" / "ai-agent",
            self.base_path / "data" / "ai-agent",
            self.base_path / "logs",
            self.base_path / "private" / "ai-workspace" / "for-daniel"
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _get_github_username(self) -> str:
        """Get GitHub username from existing data or environment"""
        try:
            with open(self.base_path / "data" / "exports" / "repo-index.json", "r") as f:
                data = json.load(f)
                if data and len(data) > 0:
                    url = data[0].get("url", "")
                    import re
                    match = re.search(r"github\.com/([^/]+)/", url)
                    if match:
                        return match.group(1)
        except Exception as e:
            print(f"Warning: Could not determine GitHub username: {e}")
        
        return os.getenv("GITHUB_USERNAME", "danielrosehill")
    
    def _load_existing_repositories(self) -> Dict[str, RepositoryInfo]:
        """Load existing repository data"""
        existing = {}
        try:
            json_path = self.base_path / "data" / "exports" / "repo-index.json"
            if json_path.exists():
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    for repo in data:
                        repo_info = RepositoryInfo(
                            name=repo.get('name', ''),
                            description=repo.get('description', ''),
                            url=repo.get('url', ''),
                            created_at=repo.get('created_at', ''),
                            updated_at=repo.get('updated_at', ''),
                            language=repo.get('language', ''),
                            topics=repo.get('topics', []),
                            stars=repo.get('stargazers_count', 0),
                            forks=repo.get('forks_count', 0),
                            is_fork=repo.get('fork', False),
                            size=repo.get('size', 0)
                        )
                        existing[repo_info.name] = repo_info
        except Exception as e:
            print(f"Warning: Could not load existing repositories: {e}")
        
        return existing
    
    def _load_index_repositories(self) -> Dict[str, Dict]:
        """Load information about index repositories"""
        index_repos = {}
        
        # Define known index repositories
        known_indexes = {
            "Master-Index": {
                "type": "primary",
                "category": "meta",
                "description": "Index of all other index repositories"
            },
            "AI-Generated-Projects-Index": {
                "type": "primary", 
                "category": "ai",
                "description": "Central hub for AI-related projects"
            },
            "My-Prompt-Libraries": {
                "type": "primary",
                "category": "prompts",
                "description": "Collection of prompt libraries by theme"
            },
            "N8N-Workflows-Index": {
                "type": "specialized",
                "category": "automation",
                "description": "N8N automation workflows"
            },
            "System-Prompt-Library": {
                "type": "specialized",
                "category": "ai-tools",
                "description": "System prompts for AI applications"
            }
        }
        
        return known_indexes
    
    def fetch_github_repositories(self, force_refresh: bool = False) -> List[RepositoryInfo]:
        """Fetch repository data from GitHub API"""
        print("Fetching repository data from GitHub...")
        
        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        repositories = []
        page = 1
        per_page = 100
        
        while True:
            url = f"https://api.github.com/users/{self.github_username}/repos"
            params = {
                "page": page,
                "per_page": per_page,
                "sort": "updated",
                "direction": "desc"
            }
            
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                repos = response.json()
                if not repos:
                    break
                
                for repo in repos:
                    # Skip forks if configured
                    if repo.get('fork', False) and not self.config["github"]["include_forks"]:
                        continue
                    
                    repo_info = RepositoryInfo(
                        name=repo['name'],
                        description=repo.get('description', '') or '',
                        url=repo['html_url'],
                        created_at=repo['created_at'],
                        updated_at=repo['updated_at'],
                        language=repo.get('language', '') or '',
                        topics=repo.get('topics', []),
                        stars=repo.get('stargazers_count', 0),
                        forks=repo.get('forks_count', 0),
                        is_fork=repo.get('fork', False),
                        size=repo.get('size', 0)
                    )
                    
                    # Fetch README if configured
                    if self.config["github"]["fetch_readme"]:
                        repo_info.readme_content = self._fetch_readme(repo_info.name)
                    
                    repositories.append(repo_info)
                
                page += 1
                
                # Rate limiting
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching repositories: {e}")
                break
        
        print(f"Fetched {len(repositories)} repositories from GitHub")
        return repositories
    
    def _fetch_readme(self, repo_name: str) -> Optional[str]:
        """Fetch README content for a repository"""
        if not self.github_token:
            return None
        
        headers = {"Authorization": f"token {self.github_token}"}
        url = f"https://api.github.com/repos/{self.github_username}/{repo_name}/readme"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                import base64
                content = response.json().get('content', '')
                return base64.b64decode(content).decode('utf-8')
        except Exception as e:
            print(f"Warning: Could not fetch README for {repo_name}: {e}")
        
        return None
    
    def categorize_repositories(self, repositories: List[RepositoryInfo], 
                              force_recategorize: bool = False) -> Dict[str, List[str]]:
        """Categorize repositories using the LLM categorizer"""
        print("Starting repository categorization...")
        
        # Filter repositories that need categorization
        to_categorize = []
        for repo in repositories:
            if force_recategorize or not repo.suggested_categories:
                to_categorize.append({
                    'name': repo.name,
                    'description': repo.description,
                    'language': repo.language,
                    'topics': repo.topics,
                    'readme_content': repo.readme_content
                })
        
        if not to_categorize:
            print("No repositories need categorization")
            return {}
        
        print(f"Categorizing {len(to_categorize)} repositories...")
        
        # Use existing categorizer
        results = self.categorizer.batch_categorize(
            to_categorize,
            min_confidence=self.config["categorization"]["min_confidence"],
            apply_changes=True
        )
        
        # Consolidate categories if configured
        if self.config["index_management"]["consolidate_categories"]:
            print("Consolidating similar categories...")
            self.categorizer.consolidate_similar_categories()
        
        return results
    
    def update_index_repositories(self, categorization_results: Dict[str, List[str]]):
        """Update index repositories based on categorization results"""
        print("Updating index repositories...")
        
        # Update statistics
        if self.config["index_management"]["update_statistics"]:
            self._update_repository_statistics()
        
        # Update the main README if needed
        self._update_main_readme()
        
        print("Index repositories updated successfully")
    
    def _update_repository_statistics(self):
        """Update repository statistics in the main README"""
        try:
            readme_path = self.base_path / "README.md"
            if not readme_path.exists():
                return
            
            # Count repositories by category
            category_counts = {}
            sections_dir = self.base_path / "sections"
            
            if sections_dir.exists():
                for category_file in sections_dir.glob("*.md"):
                    category_name = category_file.stem.replace('-', ' ').title()
                    
                    # Count repositories in this category
                    with open(category_file, 'r') as f:
                        content = f.read()
                        # Count repository links
                        repo_count = content.count('[![View Repo]')
                        if repo_count > 0:
                            category_counts[category_name] = repo_count
            
            # Update README with new statistics
            with open(readme_path, 'r') as f:
                content = f.read()
            
            # Find and update total repositories count
            total_repos = sum(category_counts.values())
            content = re.sub(
                r'\*\*Total Repositories:\*\* \d+',
                f'**Total Repositories:** {total_repos}',
                content
            )
            
            # Update top categories
            top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            top_categories_text = "\n".join([
                f"- {category}: {count} repositories"
                for category, count in top_categories
            ])
            
            # Replace top categories section
            import re
            pattern = r'(\*\*Top Categories:\*\*\n)(.*?)(\n\n---)'
            replacement = f'\\1{top_categories_text}\\3'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            with open(readme_path, 'w') as f:
                f.write(content)
            
            print(f"Updated statistics: {total_repos} total repositories")
            
        except Exception as e:
            print(f"Warning: Could not update statistics: {e}")
    
    def _update_main_readme(self):
        """Update the main README with current timestamp"""
        try:
            readme_path = self.base_path / "README.md"
            if readme_path.exists():
                with open(readme_path, 'r') as f:
                    content = f.read()
                
                # Update timestamp
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                content = re.sub(
                    r'\*Last updated: [^*]+\*',
                    f'*Last updated: {current_time}*',
                    content
                )
                
                with open(readme_path, 'w') as f:
                    f.write(content)
                
        except Exception as e:
            print(f"Warning: Could not update main README: {e}")
    
    def generate_report(self, repositories: List[RepositoryInfo], 
                       categorization_results: Dict[str, List[str]]) -> Dict:
        """Generate a comprehensive report of the update process"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_repositories": len(repositories),
                "categorized_repositories": len(categorization_results),
                "new_repositories": len([r for r in repositories if r.name not in self.existing_repos]),
                "updated_repositories": 0  # Could be calculated based on update timestamps
            },
            "categorization_results": categorization_results,
            "repository_statistics": {
                "by_language": {},
                "by_category": {},
                "by_creation_date": {}
            },
            "index_repositories": self.index_repositories,
            "recommendations": []
        }
        
        # Calculate language statistics
        language_counts = {}
        for repo in repositories:
            if repo.language:
                language_counts[repo.language] = language_counts.get(repo.language, 0) + 1
        report["repository_statistics"]["by_language"] = language_counts
        
        # Generate recommendations
        recommendations = []
        
        # Check for repositories without descriptions
        no_description = [r.name for r in repositories if not r.description]
        if no_description:
            recommendations.append({
                "type": "missing_descriptions",
                "priority": "medium",
                "message": f"{len(no_description)} repositories lack descriptions",
                "repositories": no_description[:10]  # Show first 10
            })
        
        # Check for uncategorized repositories
        uncategorized = [r.name for r in repositories if r.name not in categorization_results]
        if uncategorized:
            recommendations.append({
                "type": "uncategorized",
                "priority": "high", 
                "message": f"{len(uncategorized)} repositories remain uncategorized",
                "repositories": uncategorized[:10]
            })
        
        report["recommendations"] = recommendations
        
        # Save report
        if self.config["reporting"]["generate_reports"]:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = self.base_path / "reports" / "ai-agent" / f"update_report_{timestamp}.json"
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"Report saved to {report_path}")
        
        return report
    
    def run_full_update(self, force_refresh: bool = False, force_recategorize: bool = False):
        """Run a complete update cycle"""
        print("Starting full repository update cycle...")
        start_time = datetime.now()
        
        try:
            # Step 1: Fetch repository data
            repositories = self.fetch_github_repositories(force_refresh)
            
            # Step 2: Categorize repositories
            categorization_results = self.categorize_repositories(repositories, force_recategorize)
            
            # Step 3: Update index repositories
            self.update_index_repositories(categorization_results)
            
            # Step 4: Generate report
            report = self.generate_report(repositories, categorization_results)
            
            # Step 5: Save updated repository data
            self._save_repository_data(repositories)
            
            duration = datetime.now() - start_time
            print(f"\nFull update completed successfully in {duration}")
            print(f"Processed {len(repositories)} repositories")
            print(f"Categorized {len(categorization_results)} repositories")
            
            return report
            
        except Exception as e:
            print(f"Error during full update: {e}")
            raise
    
    def _save_repository_data(self, repositories: List[RepositoryInfo]):
        """Save repository data to JSON file"""
        data = [asdict(repo) for repo in repositories]
        
        json_path = self.base_path / "data" / "exports" / "repo-index.json"
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Saved repository data to {json_path}")

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="Enhanced AI Agent for Repository Management")
    
    parser.add_argument("--full-update", action="store_true",
                       help="Run complete update cycle")
    parser.add_argument("--categorize-only", action="store_true",
                       help="Only run categorization")
    parser.add_argument("--update-indexes-only", action="store_true",
                       help="Only update index repositories")
    parser.add_argument("--force-refresh", action="store_true",
                       help="Force refresh of repository data from GitHub")
    parser.add_argument("--force-recategorize", action="store_true",
                       help="Force recategorization of all repositories")
    parser.add_argument("--config", type=str,
                       help="Path to configuration file")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without making changes")
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = EnhancedAIAgent(config_path=args.config)
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
        return
    
    try:
        if args.full_update or not any([args.categorize_only, args.update_indexes_only]):
            # Run full update by default
            report = agent.run_full_update(
                force_refresh=args.force_refresh,
                force_recategorize=args.force_recategorize
            )
            
        elif args.categorize_only:
            repositories = agent.fetch_github_repositories(args.force_refresh)
            categorization_results = agent.categorize_repositories(
                repositories, args.force_recategorize
            )
            print(f"Categorized {len(categorization_results)} repositories")
            
        elif args.update_indexes_only:
            agent.update_index_repositories({})
            print("Index repositories updated")
        
        print("\nAI Agent completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
