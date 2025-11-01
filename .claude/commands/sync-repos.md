---
description: Pull new repos, categorize them, and update all indexes
tags: [sync, update, index, primary]
---

# Sync Repository Index

The primary workflow for keeping the index up to date. This command:
1. Pulls new repositories from GitHub
2. Auto-categorizes them into appropriate section files
3. Creates new section files if needed
4. Updates the main README to include any new sub-indexes
5. Updates time-based indexes

## Instructions

Execute the following workflow:

### Step 1: Pull and Categorize New Repos
```bash
./management/run-indexer.sh
```
- Display summary of new repos found
- Show which repos were auto-categorized
- List any low-confidence matches

### Step 2: Rebuild Main README
```bash
python3 scripts/build-hierarchical-readme.py
```
- This ensures any new section files created in Step 1 are added to the index of indexes
- Updates category structure in README

### Step 3: Update Time Indexes
```bash
python3 management/update-time-indexes.py
```
- Updates chronological organization
- Ensures new repos appear in time-based views

### Step 4: Review Changes
```bash
git status
git diff --stat sections/
```
- Show what section files were created or modified
- Show if README was updated with new sub-indexes
- Display summary of all changes

## Post-Execution Summary

Provide:
- **New repos added**: Count and names
- **Section files modified/created**: List them
- **New sub-indexes added to README**: Highlight if any new categories were created
- **Low-confidence matches**: List repos needing manual categorization
- **Files changed**: Summary from git status

Ask the user if they want to:
- View the latest indexing report for details
- Manually categorize any low-confidence repos
- Review diffs of specific files
- Commit the changes
- Continue with other operations

This is the main workflow command - use it whenever you want to pull the latest repos and keep everything in sync.
