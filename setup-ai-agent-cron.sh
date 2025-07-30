#!/bin/bash

# Setup script for AI Agent cron automation
# This script sets up automated repository categorization

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_SCRIPT="$SCRIPT_DIR/run-ai-agent.sh"

echo "Setting up AI Agent automation..."

# Function to add cron job
setup_cron() {
    local schedule="$1"
    local mode="$2"
    
    echo "Setting up cron job: $schedule for mode: $mode"
    
    # Create cron entry
    CRON_ENTRY="$schedule cd $SCRIPT_DIR && ./run-ai-agent.sh $mode"
    
    # Check if entry already exists
    if crontab -l 2>/dev/null | grep -q "run-ai-agent.sh"; then
        echo "Cron job already exists. Updating..."
        # Remove existing entry and add new one
        (crontab -l 2>/dev/null | grep -v "run-ai-agent.sh"; echo "$CRON_ENTRY") | crontab -
    else
        echo "Adding new cron job..."
        (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    fi
}

# Function to remove cron job
remove_cron() {
    echo "Removing AI Agent cron jobs..."
    crontab -l 2>/dev/null | grep -v "run-ai-agent.sh" | crontab -
    echo "Cron jobs removed"
}

# Function to show current cron jobs
show_cron() {
    echo "Current cron jobs related to AI Agent:"
    crontab -l 2>/dev/null | grep "run-ai-agent.sh" || echo "No AI Agent cron jobs found"
}

# Function to test the setup
test_setup() {
    echo "Testing AI Agent setup..."
    
    # Check if script exists and is executable
    if [ ! -x "$CRON_SCRIPT" ]; then
        echo "ERROR: $CRON_SCRIPT is not executable"
        exit 1
    fi
    
    # Test dry run
    echo "Running dry run test..."
    cd "$SCRIPT_DIR"
    python ai-agent-categorizer.py --dry-run --config ai-agent-config.json
    
    echo "Setup test completed successfully"
}

# Show help
show_help() {
    echo "AI Agent Cron Setup Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup [SCHEDULE] [MODE]  - Setup cron job with schedule and mode"
    echo "  remove                   - Remove all AI Agent cron jobs"
    echo "  show                     - Show current cron jobs"
    echo "  test                     - Test the setup"
    echo "  presets                  - Show preset schedules"
    echo ""
    echo "Schedule format: minute hour day month weekday"
    echo "Mode: full, categorize, indexes, force-refresh"
    echo ""
    echo "Examples:"
    echo "  $0 setup '0 2 * * *' full        # Daily at 2 AM, full update"
    echo "  $0 setup '0 */6 * * *' categorize # Every 6 hours, categorize only"
    echo "  $0 remove                         # Remove cron jobs"
    echo "  $0 presets                        # Show common schedules"
}

# Show preset schedules
show_presets() {
    echo "Common Schedule Presets:"
    echo ""
    echo "Daily schedules:"
    echo "  '0 2 * * *'     - Daily at 2:00 AM"
    echo "  '0 6 * * *'     - Daily at 6:00 AM"
    echo "  '0 22 * * *'    - Daily at 10:00 PM"
    echo ""
    echo "Multiple times per day:"
    echo "  '0 */6 * * *'   - Every 6 hours"
    echo "  '0 */12 * * *'  - Every 12 hours"
    echo "  '0 8,20 * * *'  - At 8 AM and 8 PM"
    echo ""
    echo "Weekly schedules:"
    echo "  '0 2 * * 1'     - Every Monday at 2 AM"
    echo "  '0 2 * * 0'     - Every Sunday at 2 AM"
    echo ""
    echo "Recommended setup for repository management:"
    echo "  Daily full update:      '0 2 * * *' full"
    echo "  Frequent categorization: '0 */8 * * *' categorize"
}

# Main execution
case "${1:-help}" in
    "setup")
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "ERROR: Schedule and mode required"
            echo "Usage: $0 setup 'SCHEDULE' MODE"
            echo "Run '$0 presets' to see schedule examples"
            exit 1
        fi
        setup_cron "$2" "$3"
        echo "Cron job setup completed"
        show_cron
        ;;
    "remove")
        remove_cron
        ;;
    "show")
        show_cron
        ;;
    "test")
        test_setup
        ;;
    "presets")
        show_presets
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
