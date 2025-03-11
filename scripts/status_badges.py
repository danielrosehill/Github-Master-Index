import os
import json
import glob
from datetime import datetime

# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def generate_status_badges():
    """
    Generate status badges for repositories based on their activity.
    Creates a JSON file with repository status information.
    """
    # Check if we have repo data available
    data_dir = os.path.join(project_root, 'data', 'exports')
    json_path = os.path.join(data_dir, 'repo-index.json')
    
    if not os.path.exists(json_path):
        print("Repository data not found. Please run repo-fetcher.py first.")
        return
    
    # Load repository data
    with open(json_path, 'r') as f:
        try:
            repo_data = json.load(f)
        except json.JSONDecodeError:
            print("Error parsing repository data.")
            return
    
    # Create status data
    status_data = {}
    
    for repo in repo_data:
        repo_name = repo.get('name')
        if not repo_name:
            continue
            
        # Determine status based on archived flag and last update date
        is_archived = repo.get('archived', False)
        
        # Parse updated_at date
        updated_at_str = repo.get('updated_at')
        if updated_at_str:
            try:
                updated_at = datetime.strptime(updated_at_str, '%Y-%m-%dT%H:%M:%SZ')
                last_update_days = (datetime.now() - updated_at).days
            except ValueError:
                last_update_days = 999  # Default to a large number if date parsing fails
        else:
            last_update_days = 999
        
        # Determine status
        if is_archived:
            status = "archived"
        elif last_update_days > 365:
            status = "inactive"
        elif last_update_days > 180:
            status = "stale"
        else:
            status = "active"
        
        # Store status
        status_data[repo_name] = {
            "status": status,
            "last_updated_days": last_update_days,
            "language": repo.get('language', 'Unknown')
        }
    
    # Save status data
    status_path = os.path.join(data_dir, 'repo-status.json')
    os.makedirs(os.path.dirname(status_path), exist_ok=True)
    
    with open(status_path, 'w') as f:
        json.dump(status_data, f, indent=2)
    
    print(f"Generated status data for {len(status_data)} repositories.")
    return status_data

if __name__ == "__main__":
    generate_status_badges()
