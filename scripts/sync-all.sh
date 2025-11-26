#!/bin/bash
# Master sync script - runs complete repository indexing workflow
#
# This script:
# 1. Pulls latest repos from GitHub and auto-categorizes new ones
# 2. Generates the main index.md (sorted by update date)
# 3. Updates time-based indexes (by creation date)
# 4. Generates category indexes
# 5. Builds the main README.md
# 6. Copies JSON to root for website consumption
#
# Run this whenever you want to sync everything with GitHub

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "═══════════════════════════════════════════════════════"
echo "  GitHub Repository Index - Complete Sync"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v gh &> /dev/null; then
    echo "✗ Error: GitHub CLI (gh) not installed"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "✗ Error: GitHub CLI not authenticated"
    echo "  Run: gh auth login"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "✗ Error: Python 3 not installed"
    exit 1
fi

echo "✓ Prerequisites OK"
echo ""

# Step 0: Sync indexing repos list from Index-Of-Indices
echo "──────────────────────────────────────────────────────"
echo "STEP 0/6: Syncing indexing repos from Index-Of-Indices"
echo "──────────────────────────────────────────────────────"
python3 "$SCRIPT_DIR/sync-indexing-repos.py"
if [ $? -ne 0 ]; then
    echo "✗ Warning: Failed to sync indexing repos (continuing anyway)"
fi
echo ""

# Step 1: Pull and auto-categorize new repos
echo "──────────────────────────────────────────────────────"
echo "STEP 1/6: Pulling repos and auto-categorizing new ones"
echo "──────────────────────────────────────────────────────"
python3 "$SCRIPT_DIR/pull-and-index.py"
if [ $? -ne 0 ]; then
    echo "✗ Failed at pull-and-index step"
    exit 1
fi
echo "✓ Pull and categorization complete"
echo ""

# Step 2: Generate main index
echo "──────────────────────────────────────────────────────"
echo "STEP 2/6: Generating main index.md"
echo "──────────────────────────────────────────────────────"
python3 "$SCRIPT_DIR/generate-index.py" --refresh
if [ $? -ne 0 ]; then
    echo "✗ Failed at generate-index step"
    exit 1
fi
echo "✓ Main index generated"
echo ""

# Step 3: Update time-based indexes
echo "──────────────────────────────────────────────────────"
echo "STEP 3/6: Updating time-based indexes"
echo "──────────────────────────────────────────────────────"
python3 "$SCRIPT_DIR/update-time-indexes.py"
if [ $? -ne 0 ]; then
    echo "✗ Failed at update-time-indexes step"
    exit 1
fi
echo "✓ Time-based indexes updated"
echo ""

# Step 4: Generate category indexes
echo "──────────────────────────────────────────────────────"
echo "STEP 4/6: Generating category indexes"
echo "──────────────────────────────────────────────────────"
python3 "$SCRIPT_DIR/generate-category-indexes.py"
if [ $? -ne 0 ]; then
    echo "✗ Failed at generate-category-indexes step"
    exit 1
fi
echo "✓ Category indexes generated"
echo ""

# Step 5: Build README
echo "──────────────────────────────────────────────────────"
echo "STEP 5/6: Building README.md"
echo "──────────────────────────────────────────────────────"
python3 "$SCRIPT_DIR/build-hierarchical-readme.py"
if [ $? -ne 0 ]; then
    echo "✗ Failed at build-readme step"
    exit 1
fi
echo "✓ README built"
echo ""

# Step 6: Copy JSON to root for website access
echo "──────────────────────────────────────────────────────"
echo "STEP 6/6: Copying JSON to root for website"
echo "──────────────────────────────────────────────────────"
if [ -f "repo-data/latest.json" ]; then
    cp repo-data/latest.json repositories.json
    echo "✓ Copied repo-data/latest.json → repositories.json"
else
    echo "✗ Warning: repo-data/latest.json not found"
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════════"
echo "  ✓ SYNC COMPLETE"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Generated files:"
echo "  • index.md - Main repository index (by update date)"
echo "  • sections/by-topic/* - Categorized repositories"
echo "  • sections/by-time/* - Chronological indexes (by creation date)"
echo "  • README.md - Main readme with category links"
echo "  • repositories.json - JSON data for website (at root)"
echo "  • indexing-repos.json - List of indexing repositories (from Index-Of-Indices)"
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Check git diff for accuracy"
echo "  3. Commit: git add . && git commit -m 'Update repository index'"
echo "  4. Push: git push"
echo ""
