#!/usr/bin/env python3
import os
import re
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

class LLMCategorizer:
    """
    Uses an LLM to intelligently categorize GitHub repositories based on their
    name, description, and README content.
    """
    
    def __init__(self, api_key=None, model="gpt-3.5-turbo", temperature=0.3):
        """
        Initialize the LLM categorizer.
        
        Args:
            api_key (str): OpenAI API key. If None, will try to load from environment.
            model (str): The LLM model to use (default: gpt-3.5-turbo)
            temperature (float): Controls randomness in the model's output (0.0-1.0)
        """
        # Load environment variables
        load_dotenv()
        
        # Set up API key
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("Warning: No OpenAI API key found. Please set OPENAI_API_KEY environment variable.")
        
        # Model settings
        self.model = model
        self.temperature = temperature
        
        # Base path for the repository
        self.base_path = Path(__file__).parent.parent
        
        # Load existing category data
        self.existing_categories = self._load_existing_categories()
        self.category_assignments = self._load_current_assignments()
        
        # GitHub API settings
        self.github_token = os.getenv("GITHUB_PAT")
        self.github_username = self._get_github_username()
        
        # Rate limiting
        self.request_delay = 1  # seconds between API requests
        
        # Tech terminology context
        self.tech_context = self._load_tech_context()
        
    def _load_tech_context(self):
        """Load context about tech terminology to help the LLM understand tech jargon"""
        return {
            "cookbook": "In software development, a 'cookbook' typically refers to a collection of code examples, patterns, or solutions - not related to food or cooking",
            "recipe": "In software development, a 'recipe' typically refers to a specific solution or implementation pattern - not related to food",
            "wrapper": "In programming, a 'wrapper' is code that encapsulates or provides a simplified interface to another component",
            "agent": "In AI/software context, an 'agent' is a software entity that can perform tasks autonomously",
            "pipeline": "In software, a 'pipeline' refers to a sequence of data processing steps, not physical infrastructure",
            "context": "In LLMs, 'context' refers to the information provided to the model, not physical surroundings",
            "prompt": "In AI, a 'prompt' is input text given to an LLM to generate a response",
            "rag": "In AI, 'RAG' stands for Retrieval-Augmented Generation, not a cleaning cloth",
            "llm": "Large Language Model, like GPT or similar AI text generation models",
            "openwebui": "A web interface for interacting with LLMs, not related to web design generally",
            "open-webui": "Same as OpenWebUI - a web interface for interacting with LLMs",
            "owui": "Abbreviation for OpenWebUI, a web interface for interacting with LLMs"
        }
        
    def _get_github_username(self):
        """Get the GitHub username from the repository data or environment"""
        try:
            # Try to get username from existing data
            with open(self.base_path / "data" / "exports" / "repo-index.json", "r") as f:
                data = json.load(f)
                if data and len(data) > 0:
                    # Extract username from the first repo URL
                    url = data[0].get("url", "")
                    match = re.search(r"github\.com/([^/]+)/", url)
                    if match:
                        return match.group(1)
        except Exception as e:
            print(f"Warning: Could not determine GitHub username from repo data: {e}")
        
        # Fall back to environment variable
        return os.getenv("GITHUB_USERNAME")
    
    def _load_existing_categories(self):
        """Load all existing category names"""
        categories = []
        categories_dir = self.base_path / "lists" / "categories"
        
        if not categories_dir.exists():
            return categories
            
        for file_path in categories_dir.glob("*.txt"):
            categories.append(file_path.stem)
                
        return categories
    
    def _load_current_assignments(self):
        """Load current category assignments for all repositories"""
        assignments = {}
        categories_dir = self.base_path / "lists" / "categories"
        
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
            except Exception as e:
                print(f"Error loading category {category}: {e}")
                
        return assignments
    
    def _fetch_repo_readme(self, repo_name):
        """Fetch the README content for a repository"""
        if not self.github_token or not self.github_username:
            print("Warning: GitHub token or username not available. Cannot fetch README.")
            return ""
            
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        url = f"https://api.github.com/repos/{self.github_username}/{repo_name}/readme"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                # GitHub returns the README content as base64 encoded
                import base64
                content = response.json().get("content", "")
                if content:
                    decoded_content = base64.b64decode(content).decode("utf-8")
                    # Truncate if too long to avoid token limits
                    if len(decoded_content) > 2000:
                        return decoded_content[:2000] + "..."
                    return decoded_content
            else:
                print(f"Warning: Failed to fetch README for {repo_name}: {response.status_code}")
        except Exception as e:
            print(f"Error fetching README for {repo_name}: {e}")
            
        return ""
    
    def _call_openai_api(self, prompt, max_retries=3):
        """Call the OpenAI API with the given prompt"""
        if not self.api_key:
            print("Error: No OpenAI API key available")
            return None
            
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                else:
                    print(f"Warning: API call failed (attempt {attempt+1}/{max_retries}): {response.status_code}")
                    if response.status_code == 429:  # Rate limit
                        wait_time = min(2 ** attempt, 60)  # Exponential backoff
                        print(f"Rate limited. Waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        print(f"API error: {response.text}")
                        break
            except Exception as e:
                print(f"Error calling OpenAI API (attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(2)
                
        return None
    
    def _extract_entity_names(self, repo_name, description, readme_content):
        """
        Extract potential entity names from repository data.
        
        Args:
            repo_name (str): Name of the repository
            description (str): Repository description
            readme_content (str): README content
            
        Returns:
            list: List of potential entity names
        """
        entities = []
        
        # Common patterns for entity names in repo names
        patterns = [
            r'([A-Z][a-z]+(?:[A-Z][a-z]+)+)',  # CamelCase words (e.g., OpenWebUI)
            r'([a-z]+-[a-z]+-[a-z]+)',         # kebab-case words with at least 2 hyphens
            r'([a-z]+_[a-z]+_[a-z]+)'          # snake_case words with at least 2 underscores
        ]
        
        # Extract from repo name
        for pattern in patterns:
            matches = re.findall(pattern, repo_name)
            for match in matches:
                if len(match) > 5:  # Ignore very short matches
                    entities.append(match.lower().replace('_', '-').replace(' ', '-'))
        
        # Check for specific entity names in repo name
        entity_keywords = ['openwebui', 'langchain', 'llama', 'gpt', 'gemini', 'claude', 'mistral', 
                          'ollama', 'windsurf', 'codeium', 'anthropic', 'openai']
        
        for keyword in entity_keywords:
            if keyword.lower() in repo_name.lower():
                entities.append(keyword.lower())
        
        # Extract from description if available
        if description:
            for pattern in patterns:
                matches = re.findall(pattern, description)
                for match in matches:
                    if len(match) > 5:
                        entities.append(match.lower().replace('_', '-').replace(' ', '-'))
            
            # Check for specific entity names in description
            for keyword in entity_keywords:
                if keyword.lower() in description.lower():
                    entities.append(keyword.lower())
        
        # Extract from README content (first 1000 chars only for performance)
        if readme_content:
            readme_sample = readme_content[:1000]
            for pattern in patterns:
                matches = re.findall(pattern, readme_sample)
                for match in matches:
                    if len(match) > 5:
                        entities.append(match.lower().replace('_', '-').replace(' ', '-'))
            
            # Check for specific entity names in README
            for keyword in entity_keywords:
                if keyword.lower() in readme_sample.lower():
                    entities.append(keyword.lower())
        
        # Remove duplicates and filter out common words that aren't likely to be entities
        common_words = ['github', 'readme', 'license', 'contributing', 'changelog']
        filtered_entities = []
        for entity in set(entities):
            if entity not in common_words and not any(word in entity for word in common_words):
                filtered_entities.append(entity)
        
        return filtered_entities
    
    def _generate_categorization_prompt(self, repo_name, description, readme_content, existing_categories, entity_names=None):
        """Generate a prompt for the LLM to categorize a repository"""
        
        # Create tech terminology context section
        tech_context_str = "\n".join([f"- {term}: {definition}" for term, definition in self.tech_context.items()])
        
        # Format entity names if available
        entity_names_str = ""
        if entity_names and len(entity_names) > 0:
            entity_names_str = "Potential entity names detected:\n" + "\n".join([f"- {entity}" for entity in entity_names])
        
        # Group similar categories to help the model understand relationships
        similar_categories = self._group_similar_categories(existing_categories)
        similar_categories_str = ""
        if similar_categories:
            similar_categories_str = "Similar Category Groups (use the most appropriate one):\n"
            for i, group in enumerate(similar_categories):
                similar_categories_str += f"Group {i+1}: {', '.join(group)}\n"
        
        prompt = f"""
You are an expert at categorizing GitHub repositories, especially in the fields of AI, LLMs, programming tools, and developer utilities. I need you to analyze this repository and suggest appropriate categories.

IMPORTANT CONTEXT - Technical Terminology:
{tech_context_str}

Repository Name: {repo_name}
Description: {description or "No description available"}

README Content:
{readme_content or "No README content available"}

{entity_names_str}

Existing Categories:
{', '.join(existing_categories)}

{similar_categories_str}

Please suggest categories for this repository. The categories can be from the existing list above or new categories if none of the existing ones fit well.

IMPORTANT INSTRUCTIONS:
1. Focus on the TECHNICAL PURPOSE of the repository, not literal interpretations of terms
2. For example, if a repo is named "AI-Cookbook", it's about AI code examples, NOT cooking
3. STRONGLY PRIORITIZE existing categories - only suggest new ones if absolutely necessary
4. AVOID creating new categories that are similar to existing ones - use the closest match instead
5. Be precise and specific - avoid overly general categories
6. Consider the actual function and domain of the repository
7. If you're unsure about a category, DON'T suggest it - only include high-confidence matches
8. IDENTIFY ENTITY NAMES in the repository (like "OpenWebUI", "LangChain", etc.) and suggest them as categories
9. A repository can belong to MULTIPLE categories - don't limit your suggestions if multiple categories apply
10. If you want to suggest a new category, first check if there's a similar existing one - ONLY create new categories when truly necessary
11. DO NOT create categories that are just plurals or slight variations of existing ones (e.g., "tool" vs "tools")
12. If a new category would be semantically similar to an existing one (>70% similar in meaning), use the existing one instead

For each suggested category, provide:
1. The category name (use kebab-case format, e.g., "machine-learning" not "Machine Learning")
2. A confidence score (0-100)
3. A brief explanation of why this category fits
4. Whether it's an entity name (like "openwebui", "langchain", etc.)

Format your response as a JSON object with this structure:
{{
  "categories": [
    {{
      "name": "category-name",
      "confidence": 95,
      "explanation": "Brief explanation",
      "is_entity": false
    }},
    ...
  ],
  "new_categories": [
    {{
      "name": "new-category-name",
      "confidence": 90,
      "explanation": "Explanation why a new category is needed and why NO existing category is suitable",
      "is_entity": true
    }},
    ...
  ]
}}

IMPORTANT: 
- Return ONLY the JSON object, no other text
- Use kebab-case for all category names (lowercase with hyphens)
- For entity names, create specific categories (e.g., "openwebui-tools" for OpenWebUI related repositories)
- There is NO LIMIT on how many categories a repository can belong to - assign all relevant ones
- For new categories, EXPLICITLY explain why existing categories are not suitable
- NEVER create a new category if an existing one covers the same concept, even if the wording is slightly different
"""
        return prompt
    
    def _group_similar_categories(self, categories):
        """
        Group similar categories to help the LLM understand relationships between them.
        This helps prevent creation of nearly identical categories.
        
        Args:
            categories (list): List of existing category names
            
        Returns:
            list: List of lists, where each inner list contains similar categories
        """
        # Define common prefixes/suffixes that indicate similarity
        similar_groups = []
        
        # Common patterns to group
        patterns = [
            # Programming languages
            ["python", "python-tools", "python-libraries", "python-scripts"],
            ["javascript", "javascript-tools", "js", "js-tools"],
            ["typescript", "typescript-tools", "ts", "ts-tools"],
            ["go", "go-tools", "golang"],
            ["rust", "rust-tools"],
            
            # AI related
            ["ai", "ai-tools", "ai-utilities", "ai-projects", "ai-apps", "ai-applications"],
            ["machine-learning", "ml", "ml-tools", "machine-learning-tools"],
            ["llm", "llm-tools", "llm-projects", "llm-apps", "llm-applications"],
            ["gpt", "gpt-tools", "gpt-projects", "gpt-apps"],
            ["openai", "openai-api", "openai-tools", "openai-projects"],
            
            # Web related
            ["web", "web-tools", "web-apps", "web-applications", "web-development", "web-dev"],
            ["frontend", "front-end", "ui", "user-interface", "gui", "gui-tools"],
            
            # Data related
            ["data", "data-tools", "data-processing", "data-analysis", "data-science"],
            ["database", "db", "sql", "postgres", "postgresql"],
            
            # Development tools
            ["dev-tools", "development-tools", "developer-tools", "coding-tools"],
            ["utilities", "tools", "utility", "utils"],
            
            # Specific domains
            ["docker", "containers", "containerization"],
            ["kubernetes", "k8s", "orchestration"],
            ["cli", "command-line", "terminal", "shell"],
            ["api", "api-tools", "api-clients", "api-wrappers"],
        ]
        
        # Add groups based on predefined patterns
        for pattern_group in patterns:
            # Only include categories that actually exist
            existing_in_group = [cat for cat in pattern_group if cat in categories]
            if len(existing_in_group) > 1:  # Only add if at least 2 categories in the group exist
                similar_groups.append(existing_in_group)
        
        # Find categories with common prefixes
        prefixes = {}
        for category in categories:
            parts = category.split('-')
            if len(parts) > 1:
                prefix = parts[0]
                if prefix not in prefixes:
                    prefixes[prefix] = []
                prefixes[prefix].append(category)
        
        # Add groups based on common prefixes
        for prefix, prefix_categories in prefixes.items():
            if len(prefix_categories) > 1 and prefix not in ['a', 'the', 'an', 'and', 'or', 'of', 'for', 'to', 'in', 'on', 'by']:
                # Check if this group is not already covered by pattern groups
                if not any(set(prefix_categories).issubset(set(group)) for group in similar_groups):
                    similar_groups.append(prefix_categories)
        
        return similar_groups
    
    def _is_similar_to_existing_category(self, new_category, existing_categories, threshold=0.7):
        """
        Check if a new category is similar to any existing category.
        
        Args:
            new_category (str): The new category name to check
            existing_categories (list): List of existing category names
            threshold (float): Similarity threshold (0.0-1.0)
            
        Returns:
            tuple: (bool, str) - (is_similar, most_similar_category)
        """
        if new_category in existing_categories:
            return True, new_category
            
        # Check for simple variations (plurals, prefixes, suffixes)
        singular = new_category[:-1] if new_category.endswith('s') else new_category
        plural = new_category + 's' if not new_category.endswith('s') else new_category
        
        for category in existing_categories:
            # Check for exact match after normalization
            if category.lower() == new_category.lower():
                return True, category
                
            # Check for singular/plural variations
            cat_singular = category[:-1] if category.endswith('s') else category
            if singular == cat_singular:
                return True, category
                
            # Check for prefix/suffix variations
            if (category.startswith(new_category + '-') or 
                new_category.startswith(category + '-') or
                category.endswith('-' + new_category) or
                new_category.endswith('-' + category)):
                return True, category
                
            # Check for hyphen vs no hyphen
            if category.replace('-', '') == new_category.replace('-', ''):
                return True, category
        
        # Check for semantic similarity based on shared words
        new_words = set(new_category.split('-'))
        for category in existing_categories:
            cat_words = set(category.split('-'))
            # Calculate Jaccard similarity (intersection over union)
            if len(new_words) > 0 and len(cat_words) > 0:
                intersection = len(new_words.intersection(cat_words))
                union = len(new_words.union(cat_words))
                similarity = intersection / union
                if similarity >= threshold:
                    return True, category
        
        return False, None
    
    def categorize_repository(self, repo_name, description=None, min_confidence=80):
        """
        Categorize a single repository using the LLM.
        
        Args:
            repo_name (str): Name of the repository
            description (str, optional): Repository description
            min_confidence (int): Minimum confidence score to accept a category suggestion
            
        Returns:
            dict: Dictionary with 'categories' and 'new_categories' lists
        """
        # Fetch README content if available
        readme_content = self._fetch_repo_readme(repo_name)
        
        # Get existing categories
        existing_categories = self._load_existing_categories()
        
        # Extract potential entity names
        entity_names = self._extract_entity_names(repo_name, description, readme_content)
        
        # Generate prompt for the LLM
        prompt = self._generate_categorization_prompt(
            repo_name, 
            description, 
            readme_content, 
            existing_categories,
            entity_names
        )
        
        # Call the LLM API
        response = self._call_openai_api(prompt)
        
        # Parse the response
        try:
            suggestions = json.loads(response)
            return suggestions
        except json.JSONDecodeError:
            print(f"Error: Failed to parse LLM response for {repo_name}")
            print(f"Response: {response}")
            return None
    
    def batch_categorize(self, repos_data, min_confidence=80, apply_changes=False):
        """
        Categorize a batch of repositories.
        
        Args:
            repos_data (list): List of repository dictionaries with 'name' and 'description'
            min_confidence (int): Minimum confidence score to accept a category suggestion
            apply_changes (bool): Whether to apply the changes to category files
            
        Returns:
            dict: Dictionary mapping repository names to suggested categories
        """
        results = {}
        new_categories = set()
        entity_mentions = {}  # Track entity mentions across repositories
        
        # Process each repository
        for i, repo in enumerate(repos_data):
            repo_name = repo.get('name', '')
            description = repo.get('description', '')
            
            print(f"Categorizing repository {i+1}/{len(repos_data)}: {repo_name}")
            
            # Skip if already categorized (optional)
            # if repo_name in self.category_assignments and len(self.category_assignments[repo_name]) > 0:
            #     print(f"Skipping {repo_name} - already categorized")
            #     continue
                
            # Categorize the repository
            suggestions = self.categorize_repository(repo_name, description, min_confidence)
            if not suggestions:
                print(f"No suggestions generated for {repo_name}")
                continue
                
            # Filter suggestions by confidence
            accepted_categories = []
            
            # Process existing categories
            for category in suggestions.get('categories', []):
                if category.get('confidence', 0) >= min_confidence:
                    accepted_categories.append({
                        'name': category['name'],
                        'confidence': category['confidence'],
                        'explanation': category.get('explanation', ''),
                        'is_new': False,
                        'is_entity': category.get('is_entity', False)
                    })
                    
                    # Track entity mentions
                    if category.get('is_entity', False):
                        entity_name = category['name']
                        if entity_name not in entity_mentions:
                            entity_mentions[entity_name] = []
                        entity_mentions[entity_name].append(repo_name)
            
            # Process new categories - check for similarity with existing ones first
            existing_categories = self._load_existing_categories()
            for category in suggestions.get('new_categories', []):
                if category.get('confidence', 0) >= min_confidence:
                    # Check if this new category is similar to an existing one
                    is_similar, similar_category = self._is_similar_to_existing_category(
                        category['name'], 
                        existing_categories + list(new_categories)
                    )
                    
                    if is_similar:
                        print(f"New category '{category['name']}' is similar to existing '{similar_category}' - using existing category")
                        # Add the repository to the similar existing category instead
                        accepted_categories.append({
                            'name': similar_category,
                            'confidence': category['confidence'],
                            'explanation': f"Similar to suggested new category '{category['name']}': {category.get('explanation', '')}",
                            'is_new': False,
                            'is_entity': category.get('is_entity', False)
                        })
                    else:
                        # This is a genuinely new category
                        accepted_categories.append({
                            'name': category['name'],
                            'confidence': category['confidence'],
                            'explanation': category.get('explanation', ''),
                            'is_new': True,
                            'is_entity': category.get('is_entity', False)
                        })
                        new_categories.add(category['name'])
                        
                        # Track entity mentions
                        if category.get('is_entity', False):
                            entity_name = category['name']
                            if entity_name not in entity_mentions:
                                entity_mentions[entity_name] = []
                            entity_mentions[entity_name].append(repo_name)
            
            results[repo_name] = accepted_categories
            
            # Add delay to avoid rate limiting
            time.sleep(self.request_delay)
        
        # Create entity-based categories for entities mentioned in multiple repositories
        entity_categories = {}
        for entity, repos in entity_mentions.items():
            if len(repos) >= 2:  # Entity appears in at least 2 repositories
                print(f"Found common entity '{entity}' in {len(repos)} repositories")
                entity_categories[entity] = repos
                if entity not in new_categories:
                    new_categories.add(entity)
        
        # Apply changes if requested
        if apply_changes:
            self._apply_category_changes(results, list(new_categories), entity_categories)
            
        return results
    
    def _apply_category_changes(self, categorization_results, new_categories, entity_categories=None):
        """
        Apply the categorization results to the category files.
        
        Args:
            categorization_results (dict): Dictionary mapping repo names to category lists
            new_categories (list): List of new categories to create
            entity_categories (dict, optional): Dictionary mapping entity names to lists of repositories
        """
        print("Applying category changes...")
        
        # Create directories if they don't exist
        categories_dir = self.base_path / "lists" / "categories"
        categories_dir.mkdir(parents=True, exist_ok=True)
        
        # Track changes for reporting
        changes_made = []
        
        # Create new category files
        for category in new_categories:
            category_file = categories_dir / f"{category}.txt"
            if not category_file.exists():
                print(f"Creating new category file: {category}")
                category_file.touch()
                changes_made.append(f"Created new category: {category}")
        
        # Update category assignments
        for repo_name, categories in categorization_results.items():
            # Get category names only
            category_names = [cat['name'] for cat in categories]
            
            # Skip if no categories suggested
            if not category_names:
                continue
                
            # Update each category file
            for category in category_names:
                category_file = categories_dir / f"{category}.txt"
                
                # Read existing entries
                existing_entries = []
                if category_file.exists():
                    with open(category_file, "r") as f:
                        existing_entries = [line.strip() for line in f if line.strip()]
                
                # Add the repository if not already present
                if repo_name not in existing_entries:
                    print(f"Adding {repo_name} to category {category}")
                    with open(category_file, "a") as f:
                        f.write(f"{repo_name}\n")
                    changes_made.append(f"Added {repo_name} to category {category}")
        
        # Apply entity-based categorization
        if entity_categories:
            for entity, repos in entity_categories.items():
                category_file = categories_dir / f"{entity}.txt"
                
                # Read existing entries
                existing_entries = []
                if category_file.exists():
                    with open(category_file, "r") as f:
                        existing_entries = [line.strip() for line in f if line.strip()]
                
                # Add repositories to entity category
                for repo_name in repos:
                    if repo_name not in existing_entries:
                        print(f"Adding {repo_name} to entity category {entity}")
                        with open(category_file, "a") as f:
                            f.write(f"{repo_name}\n")
                        changes_made.append(f"Added {repo_name} to entity category {entity}")
        
        # Print summary of changes
        if changes_made:
            print("\nSummary of changes made:")
            for change in changes_made:
                print(f"- {change}")
        else:
            print("No changes were made - all repositories were already correctly categorized.")
        
        # Create a report of the changes
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = self.base_path / "reports"
        report_dir.mkdir(exist_ok=True, parents=True)
        report_file = report_dir / f"categorization_report_{timestamp}.json"
        
        with open(report_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "new_categories": new_categories,
                "entity_categories": entity_categories or {},
                "changes_made": changes_made,
                "categorization_results": {
                    repo: [
                        {
                            "name": cat["name"],
                            "confidence": cat["confidence"],
                            "explanation": cat["explanation"],
                            "is_new": cat["is_new"],
                            "is_entity": cat.get("is_entity", False)
                        } 
                        for cat in cats
                    ]
                    for repo, cats in categorization_results.items()
                }
            }, f, indent=2)
            
        print(f"Categorization report saved to {report_file}")

    def consolidate_similar_categories(self):
        """
        Consolidate similar categories by merging them.
        
        This function identifies similar categories and merges the less common ones
        into the more common ones to avoid category fragmentation.
        
        Returns:
            dict: Dictionary mapping merged categories to their target categories
        """
        print("Consolidating similar categories...")
        
        # Get all category files
        categories_dir = self.base_path / "lists" / "categories"
        category_files = list(categories_dir.glob("*.txt"))
        
        # Map of category names to their file paths
        category_map = {cat_file.stem: cat_file for cat_file in category_files}
        
        # Count repositories in each category
        category_counts = {}
        category_repos = {}  # Track repos in each category for similarity comparison
        for category, file_path in category_map.items():
            with open(file_path, "r") as f:
                repos = [line.strip() for line in f if line.strip()]
                category_counts[category] = len(repos)
                category_repos[category] = set(repos)
        
        # Define similar category pairs to merge
        similar_pairs = [
            # Programming languages and their tools
            ("python", "python-tools"),
            ("javascript", "javascript-tools"),
            ("typescript", "typescript-tools"),
            ("go", "go-tools"),
            ("rust", "rust-tools"),
            
            # UI/GUI related
            ("ui", "user-interface"),
            ("gui", "gui-tools"),
            ("gui", "gui-utilities"),
            
            # AI related
            ("ai", "ai-tools"),
            ("ai-tools", "ai-utilities"),
            ("machine-learning", "ml"),
            ("llm", "llm-tools"),
            ("llm", "llm-projects"),
            ("gpt", "gpt-tools"),
            
            # Utilities and tools
            ("utilities", "tools"),
            ("utility", "utilities"),
            ("utils", "utilities"),
            
            # Web related
            ("web", "web-tools"),
            ("web-development", "web-dev"),
            ("web-app", "web-apps"),
            
            # Data related
            ("data", "data-tools"),
            ("data-processing", "data-tools"),
            ("data-analysis", "data-tools"),
            
            # Development related
            ("dev-tools", "development-tools"),
            ("developer-tools", "development-tools"),
            ("coding-tools", "development-tools"),
            
            # API related
            ("api", "api-tools"),
            ("api-client", "api-clients"),
            ("api-wrapper", "api-wrappers"),
            
            # CLI related
            ("cli", "cli-tools"),
            ("command-line", "cli"),
            
            # Documentation
            ("docs", "documentation"),
            
            # Backup related
            ("backup", "backups"),
            
            # Template related
            ("template", "templates"),
            
            # Experiment related
            ("experiment", "experiments"),
        ]
        
        # Track merges to be performed
        merges_to_perform = {}
        
        # Check each pair
        for primary, secondary in similar_pairs:
            # Skip if either category doesn't exist
            if primary not in category_map or secondary not in category_map:
                continue
                
            # Determine which category has more repositories
            primary_count = category_counts.get(primary, 0)
            secondary_count = category_counts.get(secondary, 0)
            
            # The category with more repos becomes the target
            if primary_count >= secondary_count:
                source = secondary
                target = primary
            else:
                source = primary
                target = secondary
                
            # Add to merges
            merges_to_perform[source] = target
            print(f"Will merge '{source}' into '{target}' ({category_counts.get(source, 0)} -> {category_counts.get(target, 0)} repos)")
        
        # Find additional similar categories based on name similarity
        all_categories = list(category_map.keys())
        for i, cat1 in enumerate(all_categories):
            for cat2 in all_categories[i+1:]:
                # Skip if already in merges
                if cat1 in merges_to_perform or cat2 in merges_to_perform:
                    continue
                
                # Check for similarity in names
                is_similar, _ = self._is_similar_to_existing_category(cat1, [cat2], threshold=0.6)
                
                if is_similar:
                    # Determine which has more repos
                    if category_counts.get(cat1, 0) >= category_counts.get(cat2, 0):
                        source = cat2
                        target = cat1
                    else:
                        source = cat1
                        target = cat2
                    
                    merges_to_perform[source] = target
                    print(f"Name similarity: Will merge '{source}' into '{target}' ({category_counts.get(source, 0)} -> {category_counts.get(target, 0)} repos)")
        
        # Find additional similar categories based on repository overlap
        for cat1, repos1 in category_repos.items():
            for cat2, repos2 in category_repos.items():
                # Skip if already in merges or same category
                if cat1 == cat2 or cat1 in merges_to_perform or cat2 in merges_to_perform:
                    continue
                
                # Skip if either category has too few repos for meaningful comparison
                if len(repos1) < 3 or len(repos2) < 3:
                    continue
                
                # Calculate Jaccard similarity of repositories
                if len(repos1) > 0 and len(repos2) > 0:
                    intersection = len(repos1.intersection(repos2))
                    smaller_set_size = min(len(repos1), len(repos2))
                    
                    # If more than 70% of the smaller category's repos are in the larger one
                    if intersection > 0 and intersection / smaller_set_size >= 0.7:
                        # Merge smaller into larger
                        if len(repos1) >= len(repos2):
                            source = cat2
                            target = cat1
                        else:
                            source = cat1
                            target = cat2
                        
                        merges_to_perform[source] = target
                        print(f"Repo overlap: Will merge '{source}' into '{target}' ({category_counts.get(source, 0)} -> {category_counts.get(target, 0)} repos)")
        
        # Perform the merges
        changes_made = []
        
        for source, target in merges_to_perform.items():
            source_file = category_map[source]
            target_file = category_map[target]
            
            # Read repositories from source
            with open(source_file, "r") as f:
                source_repos = [line.strip() for line in f if line.strip()]
                
            # Read repositories from target
            with open(target_file, "r") as f:
                target_repos = [line.strip() for line in f if line.strip()]
                
            # Identify repos to add (those not already in target)
            repos_to_add = [repo for repo in source_repos if repo not in target_repos]
            
            # Add repos to target
            if repos_to_add:
                with open(target_file, "a") as f:
                    for repo in repos_to_add:
                        f.write(f"{repo}\n")
                        changes_made.append(f"Moved {repo} from {source} to {target}")
                        
            # Create a backup of the source file
            backup_dir = self.base_path / "reports" / "category_backups"
            backup_dir.mkdir(exist_ok=True, parents=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"{source}_{timestamp}.txt"
            
            # Copy source file to backup
            import shutil
            shutil.copy2(source_file, backup_file)
            
            # Delete the source file
            source_file.unlink()
            changes_made.append(f"Merged category {source} into {target} and removed {source}")
        
        # Create a report of the consolidation
        if changes_made:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_dir = self.base_path / "reports"
            report_dir.mkdir(exist_ok=True, parents=True)
            report_file = report_dir / f"category_consolidation_{timestamp}.json"
            
            with open(report_file, "w") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "merges_performed": merges_to_perform,
                    "changes_made": changes_made
                }, f, indent=2)
                
            print(f"Category consolidation report saved to {report_file}")
            print(f"Performed {len(merges_to_perform)} category merges")
            
        return merges_to_perform

def categorize_repositories(json_path=None, min_confidence=80, apply_changes=False):
    """
    Main function to categorize repositories from a JSON file.
    
    Args:
        json_path (str): Path to the JSON file containing repository data
        min_confidence (int): Minimum confidence score to accept a category suggestion
        apply_changes (bool): Whether to apply the changes to category files
    """
    # Ensure reports directory exists
    os.makedirs("reports", exist_ok=True)
    
    # Initialize the categorizer
    categorizer = LLMCategorizer()
    
    # Default JSON path if not provided
    if not json_path:
        json_path = Path(__file__).parent.parent / "data" / "exports" / "repo-index.json"
    
    # Load repository data
    try:
        with open(json_path, "r") as f:
            repos_data = json.load(f)
    except Exception as e:
        print(f"Error loading repository data: {e}")
        return
    
    print(f"Loaded {len(repos_data)} repositories from {json_path}")
    
    # Categorize repositories
    results = categorizer.batch_categorize(
        repos_data, 
        min_confidence=min_confidence,
        apply_changes=apply_changes
    )
    
    # Log results summary
    total_repos = len(results)
    total_suggestions = sum(len(cats) for cats in results.values())
    print(f"Categorization complete: {total_suggestions} suggestions for {total_repos} repositories")
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Categorize GitHub repositories using an LLM")
    parser.add_argument("--json", help="Path to the JSON file containing repository data")
    parser.add_argument("--min-confidence", type=int, default=80, help="Minimum confidence score (0-100)")
    parser.add_argument("--apply", action="store_true", help="Apply changes to category files")
    
    args = parser.parse_args()
    
    categorize_repositories(
        json_path=args.json,
        min_confidence=args.min_confidence,
        apply_changes=args.apply
    )
