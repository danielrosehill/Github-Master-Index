import os
import requests
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

def fetch_repos(incremental=False):
    load_dotenv()  # Load environment variables from .env file
    token = os.getenv('GITHUB_PAT')
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    url = 'https://api.github.com/user/repos'
    params = {
        'visibility': 'public',
        'per_page': 100,
        'affiliation': 'owner'
    }
    
    repos = []
    existing_repos = []
    page = 1
    
    # If incremental update, load existing repos and check last update time
    if incremental:
        try:
            # Load existing repos.txt
            if os.path.exists('data/repos.txt'):
                with open('data/repos.txt', 'r') as f:
                    existing_repos = [line.strip() for line in f]
            
            # Check last update timestamp
            if os.path.exists('data/.last_update'):
                with open('data/.last_update', 'r') as f:
                    last_update = float(f.read().strip())
                    # If updated in the last 12 hours, skip fetching
                    if time.time() - last_update < 12 * 3600:
                        print("Repositories were updated recently. Skipping fetch.")
                        return
        except Exception as e:
            print(f"Error checking incremental state: {e}")
    
    while True:
        print(f"Fetching page {page}...")
        params['page'] = page
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching repos: {response.status_code}")
            return
            
        page_repos = response.json()
        if not page_repos:
            break
            
        repos.extend((repo['name'], repo['fork'], repo['created_at']) for repo in page_repos)
        page += 1
    
    # Write repos to file
    os.makedirs('data', exist_ok=True)
    os.makedirs('lists/categories', exist_ok=True)
    
    # Write all repos to repos.txt
    with open('data/repos.txt', 'w') as f:
        for repo, _, _ in sorted(repos):
            f.write(f"{repo}\n")
    
    # Write fork repos to forks.txt
    with open('lists/categories/forks.txt', 'w') as f:
        for repo, is_fork, _ in sorted(repos):
            if is_fork:
                f.write(f"{repo}\n")
                
    # If this is an incremental update, identify new repos for easier categorization
    if incremental and existing_repos:
        new_repos = []
        for repo, _, created_at in repos:
            if repo not in existing_repos:
                new_repos.append((repo, created_at))
        
        if new_repos:
            # Write new repos to a separate file for easy identification
            os.makedirs('data/incremental', exist_ok=True)
            with open('data/incremental/new_repos.txt', 'w') as f:
                for repo, created_at in sorted(new_repos, key=lambda x: x[1], reverse=True):
                    created_date = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
                    f.write(f"{repo} (created: {created_date})\n")
            
            print(f"Found {len(new_repos)} new repositories since last update.")
            print(f"New repositories saved to data/incremental/new_repos.txt")
        else:
            print("No new repositories found since last update.")

if __name__ == "__main__":
    import sys
    fetch_repos("--incremental" in sys.argv)