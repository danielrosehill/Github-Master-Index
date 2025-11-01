---
description: Pull new GitHub repos and auto-categorize them
tags: [index, update, repos]
---

# Update Repository Index

Run the GitHub repository indexer to:
1. Pull all public repositories from GitHub
2. Identify new (unindexed) repositories
3. Auto-categorize them based on keywords
4. Generate an indexing report

## Instructions

1. Activate the virtual environment and run the indexer script
2. Display the indexing summary
3. Show which repos were auto-categorized (high confidence)
4. List any low-confidence matches that need manual review
5. Show git status to see which files were modified
6. Ask if the user wants to view the detailed report or make any manual adjustments

Run the script: `./management/run-indexer.sh`

After completion, provide a summary of:
- Total repos found
- New repos added
- Low-confidence matches needing review
- Files modified

If there are low-confidence matches, offer to help categorize them manually.
