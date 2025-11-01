#!/bin/bash
# Simple wrapper to run the index generator

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "Running GitHub Repository Index Generator..."
python3 "$SCRIPT_DIR/generate-index.py" "$@"
