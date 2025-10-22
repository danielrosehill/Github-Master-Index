# GitHub Repository Index Management

This directory contains tools for automatically managing and updating the GitHub repository index.

## Overview

The repository indexing system consists of several main components:

1. **hierarchy-schema.json** - Defines the category structure and keywords for matching repositories
2. **pull-and-index.py** - Main Python script that pulls repositories and automatically categorizes them
3. **generate-index.py** - Creates the main index.md file with all repositories sorted by date
4. **run-indexer.sh** - Convenient wrapper script for running the categorizer
5. **run-index-generator.sh** - Wrapper script for running the index generator

## Features

- Automatically pulls all public repositories from GitHub using `gh` CLI
- Scans existing section files to identify already indexed repositories
- Uses intelligent keyword matching to categorize unindexed repositories
- Automatically adds repositories to the best-matching section file
- Generates detailed reports for manual review of low-confidence matches
- Maintains timestamped repository data and reports

## Quick Start

### Prerequisites

- Python 3.x
- GitHub CLI (`gh`) installed and authenticated
- Repository cloned locally

### Generating the Main Index

To create/update the main `index.md` file:

```bash
# Use cached data (faster)
./management/run-index-generator.sh

# Fetch fresh data from GitHub
./management/run-index-generator.sh --refresh
```

### Running the Categorizer

To automatically categorize unindexed repositories:

```bash
./management/run-indexer.sh
```

Or directly with Python:

```bash
python3 management/pull-and-index.py
```

## How It Works

### 1. Repository Pull

The script uses the GitHub CLI to fetch all public repositories:

```bash
gh repo list danielrosehill --limit 1000 --json name,description,url,updatedAt,isPrivate,repositoryTopics --public
```

Repository data is saved to `claude-space/repo-data/` with timestamps.

### 2. Index Scanning

The script scans all markdown files in the `sections/` directory to identify repositories that are already indexed by extracting GitHub URLs.

### 3. Keyword Matching

For each unindexed repository, the script:

- Combines the repository name, description, and topics
- Compares against keywords defined in `hierarchy-schema.json`
- Calculates a confidence score for each potential section
- Name matches are weighted 3x higher than description matches

### 4. Auto-Categorization

Repositories with a confidence score ≥ 2.0 are automatically:

- Added to the best-matching section file
- Formatted with a consistent markdown template
- Listed in the categorization report

### 5. Manual Review Queue

Repositories with scores < 2.0 are flagged for manual review and included in the report with suggestions.

## Scripts Overview

### generate-index.py

**Purpose:** Creates the main `index.md` file with all repositories sorted newest to oldest.

**Features:**
- Pulls all public repositories using `gh` CLI
- Sorts by last updated date
- Shows stars, forks, and topics
- Caches data to avoid unnecessary API calls
- Saves timestamped data snapshots

**Usage:**
```bash
# Use cached data
./management/run-index-generator.sh

# Fetch fresh data from GitHub
./management/run-index-generator.sh --refresh
```

**Output:**
- `index.md` - Main repository listing at root
- `repo-data/all-repos-TIMESTAMP.json` - Repository data snapshot
- `repo-data/latest.json` - Symlink to most recent data

### pull-and-index.py

**Purpose:** Automatically categorizes unindexed repositories into topic sections.

**Features:**
- Scans existing markdown files for indexed repos
- Uses keyword matching for categorization
- Auto-adds high-confidence matches to section files
- Generates reports for manual review

**Usage:**
```bash
./management/run-indexer.sh
```

## File Structure

```
management/
├── README.md                          # This file
├── hierarchy-schema.json              # Category structure and keywords
├── pull-and-index.py                  # Repository categorization script
├── generate-index.py                  # Main index generator
├── run-indexer.sh                     # Wrapper for categorizer
├── run-index-generator.sh             # Wrapper for index generator
└── indexing-report-{timestamp}.json   # Generated categorization reports

repo-data/
├── all-repos-{timestamp}.json         # Repository data snapshots
├── latest.json                        # Symlink to most recent data
└── .gitkeep                           # Keep directory in git
```

## Configuration

### Modifying the Hierarchy

Edit `hierarchy-schema.json` to:

- Add new categories or sections
- Update keyword lists for better matching
- Adjust section descriptions

Example structure:

```json
{
  "sections": {
    "category-name": {
      "name": "Display Name",
      "description": "Category description",
      "keywords": ["keyword1", "keyword2"],
      "subsections": {
        "subcategory": {
          "name": "Subcategory Name",
          "keywords": ["more", "keywords"],
          "files": {
            "filename.md": ["file-specific", "keywords"]
          }
        }
      }
    }
  }
}
```

### Adjusting Confidence Threshold

In `pull-and-index.py`, modify the threshold:

```python
if score >= 2.0:  # Change this value
    # Auto-categorize
```

## Generated Reports

Reports are saved as `indexing-report-{timestamp}.json` and include:

```json
{
  "total_unindexed": 25,
  "categorized": [
    {
      "repo": "repository-name",
      "description": "Repo description",
      "best_match": "filename.md",
      "path": "sections/category/filename.md",
      "score": 5.0,
      "url": "https://github.com/..."
    }
  ],
  "low_confidence": [...],
  "added": 20
}
```

## Workflow Recommendations

### Regular Maintenance

Run the indexer periodically (weekly or monthly):

```bash
cd ~/repos/indexing-repos/Github-Master-Index
./management/run-indexer.sh
```

### After Running

1. Review the generated report
2. Check `git status` to see which files were modified
3. Review the changes in modified section files
4. Manually categorize low-confidence matches
5. Update keywords in `hierarchy-schema.json` if needed
6. Commit changes:

```bash
git add sections/
git commit -m "Auto-index: Added X new repositories"
```

### Improving Categorization

If repositories are frequently miscategorized:

1. Review the low-confidence matches in reports
2. Add more specific keywords to `hierarchy-schema.json`
3. Consider creating new sections for emerging patterns
4. Adjust keyword weights in the matching algorithm if needed

## Automation

### Cron Job

To run automatically, add to crontab:

```bash
# Run every Sunday at 2 AM
0 2 * * 0 cd /home/daniel/repos/indexing-repos/Github-Master-Index && ./management/run-indexer.sh >> /var/log/github-indexer.log 2>&1
```

### Systemd Timer

Or create a systemd service and timer for more control.

## Troubleshooting

### GitHub CLI Issues

If the script fails to pull repositories:

```bash
# Check authentication
gh auth status

# Re-authenticate if needed
gh auth login
```

### Python Dependencies

The script uses only standard library modules. If you encounter import errors, ensure you're using Python 3.6+.

### Permission Errors

If you can't execute the scripts:

```bash
chmod +x management/run-indexer.sh
chmod +x management/pull-and-index.py
```

### No Repositories Found

If no unindexed repositories are found:

- Check that repositories aren't already indexed
- Verify the repository data was pulled correctly
- Look at `claude-space/repo-data/latest.json`

## Extending the System

### Adding New Matching Criteria

Modify the `calculate_match_score()` method in `pull-and-index.py` to include:

- Repository size
- Programming language
- Star count
- Recent activity
- File contents

### Custom Formatters

Modify the `format_repo_entry()` method to change how repositories are displayed in section files.

### Integration with Other Tools

The indexer can be extended to:

- Generate a static site from the index
- Create dashboards showing repository statistics
- Send notifications about new repositories
- Automatically create issues for manual review

## Support

For issues or questions:

1. Check the generated reports for error messages
2. Review this README for configuration options
3. Examine the Python script for detailed comments
4. Check Git history for examples of manual fixes

## Version History

- **v1.0** (2025-10-22): Initial release
  - Automatic repository pulling
  - Keyword-based categorization
  - Report generation
  - Auto-indexing with confidence scoring
