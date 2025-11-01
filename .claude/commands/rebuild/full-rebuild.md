---
description: Complete rebuild of all indexes and documentation
tags: [rebuild, index, complete]
---

# Full Rebuild of All Indexes

Perform a complete rebuild of all repository indexes and documentation.

## Instructions

Execute the following steps in order:

1. **Update Repository Index**
   - Run: `./management/run-indexer.sh`
   - Show summary of new repos added

2. **Generate Main Index**
   - Run: `python3 management/generate-index.py --refresh`
   - Confirm index.md was updated

3. **Update Time Indexes**
   - Run: `python3 management/update-time-indexes.py`
   - Show time-based organization

4. **Rebuild README**
   - Run: `python3 scripts/build-hierarchical-readme.py`
   - Confirm README.md was updated

5. **Generate Category Indexes**
   - Run: `python3 scripts/generate-category-indexes.py`
   - Show category files updated

6. **Review Changes**
   - Show git status
   - Display summary of all changes

After completion, provide:
- Complete summary of all operations
- Total files modified
- Statistics (repos, categories, etc.)
- Ask if user wants to commit changes

This is a comprehensive operation that updates everything. Use when:
- Significant changes have been made to the hierarchy
- Need to ensure all indexes are in sync
- After bulk categorization
