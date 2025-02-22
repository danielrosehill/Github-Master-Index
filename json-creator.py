import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime

def generate_timeline_json():
    load_dotenv()
    github_token = os.getenv("GITHUB_PAT")
    if not github_token:
        print("Error: GITHUB_PAT not found in .env file")
        return None

    username = "danielrosehill"  # Replace with your GitHub username

    # Dictionary for expanding abbreviations
    abbreviations = {
        "HA": "Home Assistant",
        "LLM": "Large Language Model",
        "GPT": "Generative Pre-trained Transformer",
        "AI": "Artificial Intelligence",
        "STT": "Speech to Text",
        "TTS": "Text to Speech",
        "RAG": "Retrieval Augmented Generation",
    }

    def prettify_repo_name(name):
        # Split by hyphens and process each word
        words = name.split('-')
        processed_words = []
        
        for word in words:
            # Check if the word is an abbreviation that needs expansion
            if word.upper() in abbreviations:
                processed_words.append(abbreviations[word.upper()])
            else:
                # Capitalize the word
                processed_words.append(word.capitalize())
        
        return ' '.join(processed_words)

    # Function to fetch all repositories with pagination
    def get_all_repos(username, token):
        repos = []
        page = 1
        while True:
            url = f"https://api.github.com/users/{username}/repos?sort=created&direction=desc&page={page}"
            headers = {"Authorization": f"token {token}"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                new_repos = response.json()
                if not new_repos:
                    break  # No more repos to fetch
                repos.extend(new_repos)
                page += 1
            else:
                print(f"Error fetching repos: {response.status_code}")
                return None
        return repos

    # Fetch all current repositories
    all_repos = get_all_repos(username, github_token)
    if not all_repos:
        return None

    # Process repositories into a simple array
    timeline_data = []

    for repo in all_repos:
        if repo["private"]:
            continue

        repo_entry = {
            "name": repo["name"],
            "pretty_name": prettify_repo_name(repo["name"]),
            "description": repo["description"] or "No description provided",
            "url": repo["html_url"],
            "is_fork": repo["fork"],
            "created_at": repo["created_at"]
        }

        timeline_data.append(repo_entry)

    return timeline_data

def save_timeline_json(timeline_data, output_file="repo-index.json"):
    """Save the timeline data to a JSON file"""
    if timeline_data:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(timeline_data, f, indent=2, ensure_ascii=False)
        print(f"Timeline data saved to {output_file}")
    else:
        print("No timeline data to save")

if __name__ == "__main__":
    timeline_data = generate_timeline_json()
    if timeline_data:
        save_timeline_json(timeline_data)