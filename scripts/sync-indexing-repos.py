#!/usr/bin/env python3
"""
Sync indexing repositories list from Index-Of-Indices repo.

Fetches the indices.json file from the Index-Of-Indices repository
and saves it locally for use by this indexing system.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Configuration
SOURCE_REPO = "danielrosehill/Index-Of-Indices"
SOURCE_FILE = "indices.json"
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_JSON = PROJECT_ROOT / "indexing-repos.json"
OUTPUT_MD = PROJECT_ROOT / "private" / "indexing-repos.md"


def fetch_indices_json() -> dict | None:
    """Fetch indices.json from the Index-Of-Indices repository."""
    try:
        # Use gh CLI to fetch file content via GitHub API
        result = subprocess.run(
            [
                "gh", "api",
                f"repos/{SOURCE_REPO}/contents/{SOURCE_FILE}",
                "--jq", ".content"
            ],
            capture_output=True,
            text=True,
            check=True
        )

        # Decode base64 content
        import base64
        content = base64.b64decode(result.stdout.strip()).decode('utf-8')
        return json.loads(content)

    except subprocess.CalledProcessError as e:
        print(f"Error fetching from GitHub: {e.stderr}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        return None


def save_json(data: dict) -> bool:
    """Save the indices data as JSON file."""
    try:
        # Add metadata
        output_data = {
            "source": f"https://github.com/{SOURCE_REPO}",
            "synced_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "indices": data.get("indices", [])
        }

        with open(OUTPUT_JSON, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"✓ Saved JSON to {OUTPUT_JSON}")
        return True

    except IOError as e:
        print(f"Error saving JSON: {e}", file=sys.stderr)
        return False


def save_markdown(data: dict) -> bool:
    """Save the indices data as markdown file (URL list)."""
    try:
        OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)

        indices = data.get("indices", [])
        urls = [idx["url"] for idx in indices if "url" in idx]

        with open(OUTPUT_MD, 'w') as f:
            f.write("\n\n".join(urls))
            f.write("\n")

        print(f"✓ Saved markdown to {OUTPUT_MD}")
        return True

    except IOError as e:
        print(f"Error saving markdown: {e}", file=sys.stderr)
        return False


def main():
    print(f"Syncing indexing repos from {SOURCE_REPO}...")

    # Fetch data
    data = fetch_indices_json()
    if not data:
        print("Failed to fetch indices.json", file=sys.stderr)
        sys.exit(1)

    indices = data.get("indices", [])
    print(f"Found {len(indices)} indexing repositories")

    # Save both formats
    json_ok = save_json(data)
    md_ok = save_markdown(data)

    if not (json_ok and md_ok):
        sys.exit(1)

    # Print summary
    print(f"\nIndexing repositories ({len(indices)}):")
    for idx in indices:
        title = idx.get("title", "Unknown")
        url = idx.get("url", "")
        print(f"  - {title}: {url}")

    print("\n✓ Sync complete")


if __name__ == "__main__":
    main()
