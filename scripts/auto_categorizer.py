import json
import os
from pathlib import Path

class AutoCategorizer:
    """
    Automatically suggests categories for repositories based on their metadata.
    """
    
    def __init__(self):
        # Keyword mappings for category suggestions
        self.keyword_mappings = {
            'cli': 'created-clis',
            'gui': 'created-guis',
            'assistant': 'assistants',
            'backup': 'backups',
            'llm': 'llm',
            'gpt': 'llm',
            'ai': 'llm',
            'rag': 'context-rag',
            'retrieval': 'context-rag',
            'obsidian': 'obsidian',
            'template': 'templates',
            'streamlit': 'streamlit-apps',
            'israel': 'israel',
            'linux': 'linux',
            'opensuse': 'opensuse',
            'voice': 'voice',
            'documentation': 'documentation',
            'docs': 'documentation',
            'index': 'indexes',
            'experiment': 'experiments',
            'demo': 'demos',
            'utility': 'utilities',
            'wrapper': 'wrappers',
            'home-assistant': 'home-assistant',
            'homeassistant': 'home-assistant',
            'ha': 'home-assistant',
            'emission': 'emissions',
            'scaffold': 'scaffolders',
            'prompt': 'prompt-libraries'
        }
        
        # Load existing category assignments for learning
        self.existing_assignments = self._load_existing_assignments()
        
    def _load_existing_assignments(self):
        """
        Load existing category assignments to learn from previous categorizations.
        """
        assignments = {}
        base_path = Path(__file__).parent.parent
        categories_dir = base_path / "lists" / "categories"
        
        if not categories_dir.exists():
            return assignments
            
        for file_path in categories_dir.glob("*.txt"):
            category = file_path.stem
            try:
                with open(file_path, "r") as f:
                    repos = [line.strip() for line in f if line.strip()]
                    for repo in repos:
                        if repo not in assignments:
                            assignments[repo] = []
                        assignments[repo].append(category)
            except Exception:
                pass
                
        return assignments
        
    def suggest_categories(self, repo_name, description=None, learn_from_existing=True):
        """
        Suggest categories based on repository name and description.
        
        Args:
            repo_name (str): Name of the repository
            description (str, optional): Repository description
            learn_from_existing (bool): Whether to use existing assignments for suggestions
            
        Returns:
            list: List of suggested category names
        """
        suggestions = set()
        
        # Check for keywords in name and description
        for keyword, category in self.keyword_mappings.items():
            if keyword.lower() in repo_name.lower():
                suggestions.add(category)
            if description and keyword.lower() in description.lower():
                suggestions.add(category)
                
        # Check if this is a fork
        if repo_name in self.existing_assignments and 'forks' in self.existing_assignments[repo_name]:
            suggestions.add('forks')
            
        # Learn from similar repositories if enabled
        if learn_from_existing:
            similar_repos = self._find_similar_repos(repo_name, description)
            for similar_repo in similar_repos:
                if similar_repo in self.existing_assignments:
                    for category in self.existing_assignments[similar_repo]:
                        # Add with lower confidence (could add a confidence score in the future)
                        suggestions.add(category)
        
        return list(suggestions)
    
    def _find_similar_repos(self, repo_name, description=None):
        """
        Find repositories with similar names or descriptions.
        This is a simple implementation that could be enhanced with NLP techniques.
        
        Returns:
            list: List of similar repository names
        """
        similar_repos = []
        words = repo_name.lower().replace('-', ' ').split()
        
        for existing_repo in self.existing_assignments:
            existing_words = existing_repo.lower().replace('-', ' ').split()
            # Check for word overlap
            if any(word in existing_words for word in words):
                similar_repos.append(existing_repo)
                
        return similar_repos[:5]  # Limit to top 5 similar repos
        
    def batch_categorize(self, repos_data):
        """
        Generate category suggestions for a batch of repositories.
        
        Args:
            repos_data (list): List of repository dictionaries with 'name' and 'description'
            
        Returns:
            dict: Dictionary mapping repository names to suggested categories
        """
        suggestions = {}
        for repo in repos_data:
            name = repo.get('name', '')
            description = repo.get('description', '')
            suggestions[name] = self.suggest_categories(name, description)
            
        return suggestions

# For command-line usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python auto_categorizer.py <repo_name> [description]")
        sys.exit(1)
        
    repo_name = sys.argv[1]
    description = sys.argv[2] if len(sys.argv) > 2 else None
    
    categorizer = AutoCategorizer()
    suggestions = categorizer.suggest_categories(repo_name, description)
    
    print(f"Suggested categories for '{repo_name}':")
    for category in suggestions:
        print(f"- {category}")