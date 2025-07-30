#!/bin/bash

# Enhanced AI Agent Runner Script
# This script runs the AI agent with proper logging and error handling

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
CONFIG_FILE="$SCRIPT_DIR/ai-agent-config.json"
VENV_PATH="$SCRIPT_DIR/.venv"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Generate timestamp for logs
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/ai-agent_$TIMESTAMP.log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_PATH" ]; then
        log "Virtual environment not found. Creating one..."
        python3 -m venv "$VENV_PATH"
    fi
    
    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
    
    # Install/update requirements
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        log "Installing/updating Python dependencies..."
        pip install -r "$SCRIPT_DIR/requirements.txt" >> "$LOG_FILE" 2>&1
    fi
    
    # Check for API keys
    if [ -z "$OPENAI_API_KEY" ]; then
        log "WARNING: OPENAI_API_KEY not set. Checking .env file..."
        if [ -f "$SCRIPT_DIR/.env" ]; then
            source "$SCRIPT_DIR/.env"
        fi
        
        if [ -z "$OPENAI_API_KEY" ]; then
            log "ERROR: OPENAI_API_KEY not found. Please set it in .env file or environment."
            exit 1
        fi
    fi
}

# Function to run the AI agent
run_agent() {
    local mode="$1"
    
    log "Starting AI Agent in $mode mode..."
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
    
    # Run the agent based on mode
    case "$mode" in
        "full")
            python ai-agent-categorizer.py --full-update --config "$CONFIG_FILE" 2>&1 | tee -a "$LOG_FILE"
            ;;
        "categorize")
            python ai-agent-categorizer.py --categorize-only --config "$CONFIG_FILE" 2>&1 | tee -a "$LOG_FILE"
            ;;
        "indexes")
            python ai-agent-categorizer.py --update-indexes-only --config "$CONFIG_FILE" 2>&1 | tee -a "$LOG_FILE"
            ;;
        "force-refresh")
            python ai-agent-categorizer.py --full-update --force-refresh --force-recategorize --config "$CONFIG_FILE" 2>&1 | tee -a "$LOG_FILE"
            ;;
        *)
            log "ERROR: Unknown mode '$mode'. Use: full, categorize, indexes, or force-refresh"
            exit 1
            ;;
    esac
}

# Function to cleanup old logs
cleanup_logs() {
    log "Cleaning up old log files..."
    
    # Keep only last 10 log files
    cd "$LOG_DIR"
    ls -t ai-agent_*.log | tail -n +11 | xargs -r rm
    
    log "Log cleanup completed"
}

# Function to generate summary report
generate_summary() {
    log "Generating summary report..."
    
    # Get latest report
    LATEST_REPORT=$(find "$SCRIPT_DIR/reports/ai-agent" -name "update_report_*.json" -type f | sort | tail -n 1)
    
    if [ -f "$LATEST_REPORT" ]; then
        log "Latest report: $LATEST_REPORT"
        
        # Extract key metrics using jq if available
        if command -v jq &> /dev/null; then
            TOTAL_REPOS=$(jq -r '.summary.total_repositories' "$LATEST_REPORT")
            CATEGORIZED=$(jq -r '.summary.categorized_repositories' "$LATEST_REPORT")
            NEW_REPOS=$(jq -r '.summary.new_repositories' "$LATEST_REPORT")
            
            log "Summary: $TOTAL_REPOS total repos, $CATEGORIZED categorized, $NEW_REPOS new"
        else
            log "Install jq for detailed report parsing"
        fi
    else
        log "No reports found"
    fi
}

# Main execution
main() {
    local mode="${1:-full}"
    
    log "=== AI Agent Runner Started ==="
    log "Mode: $mode"
    log "Config: $CONFIG_FILE"
    log "Log: $LOG_FILE"
    
    # Check dependencies
    check_dependencies
    
    # Run the agent
    if run_agent "$mode"; then
        log "AI Agent completed successfully"
        
        # Generate summary
        generate_summary
        
        # Cleanup old logs
        cleanup_logs
        
        log "=== AI Agent Runner Completed ==="
        exit 0
    else
        log "ERROR: AI Agent failed with exit code $?"
        log "=== AI Agent Runner Failed ==="
        exit 1
    fi
}

# Help function
show_help() {
    echo "Usage: $0 [MODE]"
    echo ""
    echo "Modes:"
    echo "  full           - Run complete update cycle (default)"
    echo "  categorize     - Only run categorization"
    echo "  indexes        - Only update index repositories"
    echo "  force-refresh  - Force refresh all data from GitHub"
    echo "  help           - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run full update"
    echo "  $0 categorize         # Only categorize repositories"
    echo "  $0 force-refresh      # Force complete refresh"
    echo ""
    echo "Logs are saved to: $LOG_DIR/"
}

# Handle command line arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
