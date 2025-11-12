# Claude Code Configuration for GitHub Master Index

This directory contains Claude Code configuration files for managing the GitHub repository index system.

## Slash Commands

Located in `.claude/commands/` - these are the main workflows you'll use:

### Primary Command

**`/sync-repos`** - The main command you'll use most often
- Pulls new GitHub repos
- Auto-categorizes them into section files
- Creates new section files as needed
- Updates the README to include any new sub-indexes
- Updates time-based indexes
- Shows a comprehensive summary

### Individual Operations

**`/update-index`** - Pull and categorize new repos only
**`/generate-index`** - Regenerate the main index.md file
**`/update-time-indexes`** - Update chronological organization
**`/rebuild-readme`** - Rebuild the main README.md
**`/check-status`** - View git status and recent changes
**`/view-report`** - Display the latest indexing report
**`/full-rebuild`** - Complete rebuild of everything (use sparingly)

## Subagents

Located in `.claude/agents/` - specialized agents for specific tasks:

### index-manager
Manages the full indexing workflow. Use when you want:
- Complete index updates with quality control
- Comprehensive summaries of changes
- Monitoring of new sub-indexes

### categorizer
Helps manually categorize repositories. Use when:
- Auto-categorization had low confidence
- You have repos that don't fit existing categories
- You need help deciding between multiple categories
- You want to improve the hierarchy schema

### report-analyzer
Analyzes indexing reports and provides insights. Use when:
- You want to understand patterns in your repos
- You need recommendations for hierarchy improvements
- You want to see categorization health metrics
- You're planning to restructure categories

## Quick Start

1. **Pull and categorize new repos:**
   ```
   /sync-repos
   ```

2. **Review what happened:**
   ```
   /view-report
   ```

3. **Manually categorize low-confidence matches:**
   Use the categorizer agent or do it manually

4. **Check changes before committing:**
   ```
   /check-status
   ```

## Typical Workflow

```
/sync-repos
  ↓
Review summary & low-confidence matches
  ↓
Use categorizer agent for manual categorization if needed
  ↓
/check-status
  ↓
Review changes and commit
```

## Understanding the System

Read `CLAUDE.md` in the repository root for:
- Complete project overview
- Repository structure
- Script documentation
- Best practices
- Common tasks

## Tips

- **Use `/sync-repos` regularly** - It's the all-in-one command for keeping things current
- **Review low-confidence matches** - The categorizer agent can help with these
- **Check the report** - Use `/view-report` to see what the indexer did
- **Git diff is your friend** - Always review changes before committing
- **Update hierarchy keywords** - When you manually categorize, consider adding keywords to help future auto-categorization

## File Organization

```
.claude/
├── README.md (this file)
├── settings.local.json (permissions)
├── commands/ (slash commands)
│   ├── sync-repos.md ⭐ PRIMARY
│   ├── update-index.md
│   ├── generate-index.md
│   ├── update-time-indexes.md
│   ├── rebuild-readme.md
│   ├── check-status.md
│   ├── view-report.md
│   └── full-rebuild.md
└── agents/ (specialized subagents)
    ├── index-manager.md
    ├── categorizer.md
    └── report-analyzer.md
```

---

**Note:** All commands and agents have access to the repository's Python scripts and can execute them as needed. The virtual environment at `.venv/` is used automatically.
