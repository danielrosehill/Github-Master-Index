---
description: Generate the main repository index (index.md)
tags: [index, generate]
---

# Generate Main Repository Index

Regenerate the main `index.md` file with all repositories sorted by update date.

## Instructions

1. Run the index generator script with the `--refresh` flag to pull fresh data from GitHub
2. Display a summary of the generated index
3. Show the file location and preview the first few entries
4. Show git diff to see what changed

Run: `python3 management/generate-index.py --refresh`

After completion, provide:
- Total number of repositories indexed
- Location of the generated file
- Brief preview of the index
- Summary of changes (use git diff)
