#!/bin/bash

# Enhanced GitHub Repository Index Update Script
# This is a simple wrapper around the Python master script

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Generate timestamp for logs
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/update_all_$TIMESTAMP.log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to show help
show_help() {
    echo "🚀 GitHub Repository Index Update Script"
    echo "========================================="
    echo ""
    echo "Usage: $0 [MODE] [OPTIONS]"
    echo ""
    echo "Modes:"
    echo "  full              Complete update with AI categorization (default)"
    echo "  quick             Full update and push to git"
    echo "  incremental       Only update if data is older than 12 hours"
    echo "  no-ai             Update without AI categorization"
    echo "  dry-run           Show what would be done"
    echo "  help              Show this help message"
    echo ""
    echo "Options:"
    echo "  --push            Push changes to git (can combine with any mode)"
    echo "  --no-git          Skip all git operations"
    echo ""
    echo "Examples:"
    echo "  $0                        # Full update with AI, no git push"
    echo "  $0 quick                  # Full update with AI and git push"
    echo "  $0 incremental --push     # Incremental update with git push"
    echo "  $0 no-ai --push           # Update without AI, with git push"
    echo "  $0 dry-run                # Preview what would be done"
    echo ""
    echo "Features:"
    echo "  ✅ Fetches latest repositories from GitHub"
    echo "  🤖 AI-powered categorization (enabled by default)"
    echo "  📊 Generates comprehensive statistics"
    echo "  📝 Updates all markdown files and README"
    echo "  🔄 Optional git commit and push"
    echo "  📋 Detailed logging"
}

# Function to check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    # Check if Python is available
    if ! command -v python &> /dev/null; then
        log "ERROR: Python not found. Please install Python 3."
        exit 1
    fi
    
    # Check if we're in the right directory
    if [ ! -f "run_all.py" ]; then
        log "ERROR: run_all.py not found. Please run this script from the repository root."
        exit 1
    fi
    
    # Check for API keys
    if [ -z "$OPENAI_API_KEY" ]; then
        log "WARNING: OPENAI_API_KEY not set. AI categorization may be skipped."
        if [ -f ".env" ]; then
            log "INFO: Found .env file, will try to load API key from there."
        fi
    fi
    
    log "Dependencies check completed"
}

# Function to run the update
run_update() {
    local mode="$1"
    local push_flag="$2"
    local no_git_flag="$3"
    
    log "Starting GitHub Repository Index update..."
    log "Mode: $mode"
    log "Push to git: $push_flag"
    log "Skip git: $no_git_flag"
    log "Log file: $LOG_FILE"
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Build Python command based on mode
    local python_cmd="python run_all.py"
    
    case "$mode" in
        "full")
            # Default behavior - full update with AI
            ;;
        "quick")
            python_cmd="$python_cmd --push"
            ;;
        "incremental")
            python_cmd="$python_cmd --incremental"
            ;;
        "no-ai")
            python_cmd="$python_cmd --no-ai"
            ;;
        "dry-run")
            python_cmd="$python_cmd --dry-run"
            ;;
        *)
            log "ERROR: Unknown mode '$mode'"
            exit 1
            ;;
    esac
    
    # Add flags
    if [ "$push_flag" = "true" ] && [ "$mode" != "quick" ]; then
        python_cmd="$python_cmd --push"
    fi
    
    if [ "$no_git_flag" = "true" ]; then
        python_cmd="$python_cmd --no-git"
    fi
    
    log "Executing: $python_cmd"
    
    # Run the Python script and capture output
    if $python_cmd 2>&1 | tee -a "$LOG_FILE"; then
        log "✅ Update completed successfully"
        
        # Show summary
        echo ""
        echo "📋 Summary:"
        echo "   📁 Log file: $LOG_FILE"
        echo "   🕐 Completed at: $(date '+%Y-%m-%d %H:%M:%S')"
        
        # Show recent log entries
        echo ""
        echo "📝 Recent activity:"
        tail -n 5 "$LOG_FILE" | sed 's/^/   /'
        
        return 0
    else
        log "❌ Update failed"
        echo ""
        echo "❌ Update failed. Check the log file for details:"
        echo "   📁 $LOG_FILE"
        return 1
    fi
}

# Function to cleanup old logs
cleanup_logs() {
    log "Cleaning up old log files..."
    
    # Keep only last 10 log files
    cd "$LOG_DIR"
    ls -t update_all_*.log 2>/dev/null | tail -n +11 | xargs -r rm
    
    log "Log cleanup completed"
}

# Main execution
main() {
    local mode="${1:-full}"
    local push_flag="false"
    local no_git_flag="false"
    
    # Parse additional arguments
    shift || true
    while [[ $# -gt 0 ]]; do
        case $1 in
            --push)
                push_flag="true"
                shift
                ;;
            --no-git)
                no_git_flag="true"
                shift
                ;;
            *)
                log "WARNING: Unknown option '$1'"
                shift
                ;;
        esac
    done
    
    # Handle special modes
    case "$mode" in
        "help"|"-h"|"--help")
            show_help
            exit 0
            ;;
        "dry-run")
            # For dry-run, we don't need dependency checks
            run_update "$mode" "$push_flag" "$no_git_flag"
            exit $?
            ;;
    esac
    
    log "=== GitHub Repository Index Update Started ==="
    
    # Check dependencies
    check_dependencies
    
    # Run the update
    if run_update "$mode" "$push_flag" "$no_git_flag"; then
        # Cleanup old logs on success
        cleanup_logs
        
        log "=== Update Completed Successfully ==="
        exit 0
    else
        log "=== Update Failed ==="
        exit 1
    fi
}

# Execute main function with all arguments
main "$@"
