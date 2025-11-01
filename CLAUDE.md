# CLAUDE.md - GitHub Master Index Repository

## Project Overview

This repository is an automated indexing system for Daniel's GitHub repositories. It pulls public repositories, categorizes them by topic and time, and generates comprehensive index files for easy browsing.

## Purpose

The main goals of this system are:
- Automatically discover and categorize new GitHub repositories
- Maintain organized index files by topic and creation date
- Generate comprehensive README files with repository statistics
- Provide multiple views of the repository collection (by-topic, by-time, main index)

## Repository Structure

```
.
├── scripts/             # All indexing and generation scripts
│   ├── sync-all.sh                   # Master sync script (runs everything)
│   ├── pull-and-index.py             # Pulls repos & auto-categorizes
│   ├── generate-index.py             # Generates index.md
│   ├── update-time-indexes.py        # Updates time-based indexes
│   ├── build-hierarchical-readme.py  # Builds main README
│   ├── generate-category-indexes.py  # Generates category indexes
│   ├── hierarchy-schema.json         # Category hierarchy and keywords
│   └── run-*.sh                      # Individual script wrappers
├── sections/            # Organized repository sections
│   ├── by-topic/       # Topical categorization
│   │   ├── ai-ml/      # AI & Machine Learning
│   │   ├── data-tools/ # Data processing tools
│   │   ├── development/# Development tools
│   │   └── ...
│   └── by-time/        # Chronological organization (by creation date)
│       ├── 2025/       # Year directories
│       │   └── 01_25.md, 02_25.md, etc.
│       └── README.md   # Time index overview
├── repo-data/          # Cached repository data from GitHub
│   ├── all-repos-YYYYMMDD-HHMMSS.json  # Timestamped snapshots
│   └── latest.json     # Symlink to most recent data
├── index.md            # Main index (all repos by update date)
└── README.md           # Main readme with navigation
```

## Quick Start

### Complete Sync (Recommended)
Run the master sync script to update everything:
```bash
./scripts/sync-all.sh
```

This runs all steps in order:
1. Pulls latest repos from GitHub
2. Auto-categorizes new repos into sections
3. Generates main index.md
4. Updates time-based indexes
5. Generates category indexes
6. Builds README.md

### Individual Scripts

If you need to run specific steps:

```bash
# 1. Pull and categorize new repos only
./scripts/run-indexer.sh

# 2. Generate main index only
./scripts/run-index-generator.sh
# or with fresh GitHub data:
python3 scripts/generate-index.py --refresh

# 3. Update time indexes only
python3 scripts/update-time-indexes.py

# 4. Build README only
python3 scripts/build-hierarchical-readme.py

# 5. Generate category indexes only
python3 scripts/generate-category-indexes.py
```

## Key Scripts

### 1. sync-all.sh (Master Script)
**Location:** `scripts/sync-all.sh`

Runs the complete workflow in correct order. Use this for most updates.

### 2. pull-and-index.py
**Location:** `scripts/pull-and-index.py`

- Pulls all public repos using `gh` CLI
- Scans existing section files to find indexed repos
- Auto-categorizes new repos based on keywords from `hierarchy-schema.json`
- Generates indexing report showing:
  - High confidence matches (auto-added)
  - Low confidence matches (need manual review)

### 3. generate-index.py
**Location:** `scripts/generate-index.py`

- Creates `index.md` with ALL repos sorted by update date (newest first)
- Includes: description, stars, forks, topics, dates
- Use `--refresh` flag to pull fresh GitHub data first

### 4. update-time-indexes.py
**Location:** `scripts/update-time-indexes.py`

- Creates/updates chronological organization in `sections/by-time/`
- Organizes by CREATION date (not update date)
- Creates year directories with monthly files (01_25.md, 02_25.md, etc.)
- Updates year and main time index READMEs

### 5. build-hierarchical-readme.py
**Location:** `scripts/build-hierarchical-readme.py`

- Generates the main `README.md` from `hierarchy-schema.json`
- Creates category structure with badges
- Adds navigation links

### 6. generate-category-indexes.py
**Location:** `scripts/generate-category-indexes.py`

- Creates `index.md` files for each category directory
- Lists subcategories and their files

## Categorization System

Categories are defined in `scripts/hierarchy-schema.json`:

**Main Categories:**
- **AI & Machine Learning** - AI agents, LLM tools, prompt engineering
- **Data Tools** - Data processing, analysis, visualization
- **Development** - Code generation, IDEs, GitHub tools
- **Infrastructure** - Automation, backups, Linux tools
- **Platforms & Services** - Platform-specific integrations
- **Tools & Utilities** - General CLI/GUI utilities
- **Project Types** - Templates, experiments, awesome lists, misc

Each category has:
- **Keywords**: Used for auto-categorization matching
- **Subsections**: Nested organization
- **Files**: Individual `.md` files for each subcategory

## Typical Workflows

### Full Sync (Most Common)
```bash
# Run complete sync
./scripts/sync-all.sh

# Review changes
git status
git diff

# Commit
git add .
git commit -m "Update repository index"
git push
```

### Manual Categorization
If repos have low confidence matches:

1. Check the indexing report in `scripts/indexing-report-*.json`
2. Manually add repo to appropriate section file
3. Update `hierarchy-schema.json` keywords if needed
4. Re-run sync to regenerate indexes

### Update Category Structure
1. Edit `scripts/hierarchy-schema.json`
2. Run `./scripts/sync-all.sh`
3. Review and commit

## Environment Setup

### Prerequisites
- **GitHub CLI (`gh`)**: Must be authenticated
  ```bash
  gh auth login
  gh auth status
  ```
- **Python 3**: For running scripts
- **Git**: For version control

### Virtual Environment
```bash
# Activate
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Data Files

### Repository Data (`repo-data/`)
- Timestamped JSON files: `all-repos-YYYYMMDD-HHMMSS.json`
- `latest.json` symlink → most recent snapshot
- Contains full repo metadata from GitHub API

### Indexing Reports (`scripts/`)
- Created after each pull-and-index run
- Format: `indexing-report-YYYYMMDD-HHMMSS.json`
- Shows categorization results and confidence scores
- Lists low-confidence matches for manual review

### Generated Files
- `index.md` - Main index (all repos by update date)
- `README.md` - Main readme with category navigation
- `sections/by-topic/*/*.md` - Category files
- `sections/by-time/YYYY/*.md` - Monthly chronological files

## Common Tasks

### Check for New Repos
```bash
./scripts/sync-all.sh
```

### View Latest Indexing Report
```bash
ls -lt scripts/indexing-report-*.json | head -1 | xargs cat | jq
```

### Fix Miscategorized Repo
1. Find repo in wrong section file
2. Remove entry from that file
3. Add to correct section file
4. Update `hierarchy-schema.json` keywords if needed
5. Run `./scripts/sync-all.sh`
6. Commit changes

### Add New Category
1. Edit `scripts/hierarchy-schema.json`
2. Add new category with keywords
3. Create corresponding `.md` file in `sections/by-topic/`
4. Run `./scripts/sync-all.sh`
5. Commit changes

## Best Practices

1. **Use sync-all.sh** for most updates (keeps everything consistent)
2. **Review low-confidence matches** before committing
3. **Keep hierarchy-schema.json up to date** with new categories/keywords
4. **Check git diff** to review categorization accuracy
5. **Don't manually edit generated files** (index.md, README.md, time indexes)
6. **Only edit section files manually** when fixing miscategorized repos

## Understanding the Data Flow

```
GitHub API
    ↓ (via gh CLI)
repo-data/all-repos-*.json
    ↓
pull-and-index.py
    ↓
sections/by-topic/*/*.md (categorized repos)
    ↓
┌──────────────┬──────────────────┬────────────────┐
│              │                  │                │
generate-     update-time-    build-           generate-
index.py      indexes.py      hierarchical-    category-
              │               readme.py         indexes.py
              ↓               ↓                ↓
index.md      sections/       README.md        sections/*/
              by-time/                         index.md
```

## Notes

- The system is designed to be mostly automated with manual review
- Auto-categorization uses keyword matching with confidence scoring
- Low confidence matches (score < 2.0) require manual categorization
- The hierarchy schema is the single source of truth for categories
- All scripts are idempotent (safe to re-run)
- Time indexes use CREATION date, main index uses UPDATE date
