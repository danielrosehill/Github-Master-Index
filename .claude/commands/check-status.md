---
description: Check git status and recent changes
tags: [git, status, changes]
---

# Check Repository Status

View the current state of the repository and recent changes.

## Instructions

1. Show git status
2. Display recent commits (last 5)
3. Show summary of modified files in sections/
4. If there are changes, offer to show detailed diff

Commands to run:
```bash
git status
git log --oneline -5
git diff --stat sections/
```

Present the information in a clean, organized format and ask if the user wants to:
- See detailed diffs of specific files
- Commit the changes
- Undo changes
- Continue with other operations
