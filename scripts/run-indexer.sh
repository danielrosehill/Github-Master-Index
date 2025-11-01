#!/bin/bash
# Wrapper script to run the GitHub repository indexer

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/pull-and-index.py"

echo "GitHub Repository Indexer"
echo "========================="
echo ""

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed or not in PATH"
    echo "Please install it: https://cli.github.com/"
    exit 1
fi

# Check if gh is authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: GitHub CLI is not authenticated"
    echo "Please run: gh auth login"
    exit 1
fi

# Run the Python script
python3 "$PYTHON_SCRIPT" "$@"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "Indexing completed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Review the indexing report in management/"
    echo "  2. Check git status to see modified files"
    echo "  3. Review changes before committing"
    echo "  4. Consider manually categorizing low-confidence matches"
else
    echo ""
    echo "Indexing failed with exit code: $exit_code"
fi

exit $exit_code
