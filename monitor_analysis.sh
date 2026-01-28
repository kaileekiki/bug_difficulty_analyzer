#!/bin/bash
# Monitor V3 Analysis Progress

echo "==================================================================="
echo "SWE-BENCH V3 ANALYSIS MONITOR"
echo "==================================================================="
echo ""

# Function to show progress
show_progress() {
    echo "📊 PROGRESS:"
    echo ""
    
    # Find latest progress file (v3_progress_* or progress_v3_*)
    PROGRESS_FILE=$(ls -t outputs/*progress*.json 2>/dev/null | head -1)
    
    if [ -f "$PROGRESS_FILE" ]; then
        # Try to get 'count' field first (v3_progress format)
        PROCESSED=$(grep -o '"count": [0-9]*' "$PROGRESS_FILE" | grep -o '[0-9]*' | tail -1)
        # Fallback to 'processed' field if count not found
        if [ -z "$PROCESSED" ]; then
            PROCESSED=$(grep -o '"processed": [0-9]*' "$PROGRESS_FILE" | grep -o '[0-9]*' | tail -1)
        fi
        
        # Count errors array length
        ERROR_COUNT=$(grep -c '"errors":' "$PROGRESS_FILE" 2>/dev/null || echo "0")
        
        if [ -n "$PROCESSED" ]; then
            echo "  Processed: $PROCESSED / 500 ($(echo "scale=1; $PROCESSED * 100 / 500" | bc)%)"
            echo "  Progress file: $(basename $PROGRESS_FILE)"
            echo ""
        else
            echo "  Progress file found but couldn't parse count"
            echo ""
        fi
    else
        echo "  No progress file found yet"
        echo ""
    fi
}

# Function to show current task
show_current() {
    echo "🔄 CURRENT TASK:"
    echo ""
    
    LOG_FILE=$(ls -t v3_full_*.log 2>/dev/null | head -1)
    
    if [ -f "$LOG_FILE" ]; then
        # Look for "Processing" line
        CURRENT=$(tail -100 "$LOG_FILE" | grep "Processing" | tail -1)
        if [ -n "$CURRENT" ]; then
            echo "  $CURRENT"
        else
            echo "  Waiting for next instance..."
        fi
        echo ""
    else
        echo "  No log file found"
        echo ""
    fi
}

# Function to show resource usage
show_resources() {
    echo "💾 RESOURCES:"
    echo ""
    
    # Disk space
    DISK_INFO=$(df -h . | tail -1)
    AVAIL=$(echo $DISK_INFO | awk '{print $4}')
    USED=$(echo $DISK_INFO | awk '{print $3}')
    PERCENT=$(echo $DISK_INFO | awk '{print $5}')
    
    echo "  Disk: $USED used, $AVAIL available ($PERCENT)"
    
    # Memory (if process is running)
    MEM=$(ps aux | grep "python3 run_swebench" | grep -v grep | awk '{print $3}' | head -1)
    if [ -n "$MEM" ]; then
        echo "  Memory: ${MEM}%"
    fi
    
    # Repo cache size
    if [ -d "repo_cache" ]; then
        CACHE_SIZE=$(du -sh repo_cache 2>/dev/null | awk '{print $1}')
        echo "  Repo cache: $CACHE_SIZE"
    fi
    
    # Output size
    if [ -d "outputs" ]; then
        OUTPUT_SIZE=$(du -sh outputs 2>/dev/null | awk '{print $1}')
        echo "  Outputs: $OUTPUT_SIZE"
    fi
    
    echo ""
}

# Function to estimate time remaining
show_eta() {
    echo "⏱️  ESTIMATED TIME:"
    echo ""
    
    PROGRESS_FILE=$(ls -t outputs/*progress*.json 2>/dev/null | head -1)
    
    if [ -f "$PROGRESS_FILE" ]; then
        # Try to get 'count' field first (v3_progress format)
        PROCESSED=$(grep -o '"count": [0-9]*' "$PROGRESS_FILE" | grep -o '[0-9]*' | tail -1)
        # Fallback to 'processed' field
        if [ -z "$PROCESSED" ]; then
            PROCESSED=$(grep -o '"processed": [0-9]*' "$PROGRESS_FILE" | grep -o '[0-9]*' | tail -1)
        fi
        
        if [ -n "$PROCESSED" ] && [ "$PROCESSED" -gt 0 ]; then
            # Calculate average time per instance
            LOG_FILE=$(ls -t v3_full_*.log 2>/dev/null | head -1)
            if [ -f "$LOG_FILE" ]; then
                # Simple estimation: assume 60s per instance
                AVG_TIME=60
                REMAINING=$((500 - PROCESSED))
                TOTAL_SECONDS=$((REMAINING * AVG_TIME))
                HOURS=$((TOTAL_SECONDS / 3600))
                MINUTES=$(((TOTAL_SECONDS % 3600) / 60))
                
                echo "  Remaining: ~${HOURS}h ${MINUTES}m"
                echo "  (Based on $AVG_TIME sec/instance average)"
            fi
        fi
    fi
    
    echo ""
}

# Main loop
while true; do
    clear
    echo "==================================================================="
    echo "SWE-BENCH V3 ANALYSIS MONITOR"
    echo "Updated: $(date)"
    echo "==================================================================="
    echo ""
    
    show_progress
    show_current
    show_resources
    show_eta
    
    echo "==================================================================="
    echo "Press Ctrl+C to stop monitoring"
    echo "Refresh in 30 seconds..."
    
    sleep 30
done
