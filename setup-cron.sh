#!/bin/bash

# Script to set up a cron job for automatically updating the GitHub repository index

# Get the absolute path to the repository
REPO_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$(which python3)"
LOG_DIR="$REPO_PATH/logs"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Define the cron job command
# This will run at 2:00 AM every day and log output to a file
CRON_CMD="0 2 * * * cd $REPO_PATH && $PYTHON_PATH $REPO_PATH/run_all.py --push >> $LOG_DIR/update-$(date +\%Y\%m\%d).log 2>&1"

# Check if the cron job already exists
if crontab -l 2>/dev/null | grep -q "$REPO_PATH/run_all.py"; then
    echo "Cron job already exists. Skipping."
else
    # Add the new cron job
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "Cron job added successfully. It will run daily at 2:00 AM."
    echo "Command: $CRON_CMD"
fi

# Make the script executable
chmod +x "$REPO_PATH/run_all.py"

echo "Setup complete!"
echo "Logs will be saved to: $LOG_DIR"
