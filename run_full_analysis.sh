#!/bin/bash
# Full SWE-bench Verified Analysis Runner
# Processes 500 instances in 10 batches of 50

set -e
set -o pipefail  # Ensure pipe failures are caught

LOG_FILE="v3_full_$(date +%Y%m%d_%H%M%S).log"
BATCH_SIZE=50
TOTAL_BATCHES=10
PROGRESS_FILE=".analysis_progress"
TOTAL_INSTANCES=500

# Parse command line arguments for batch number
START_BATCH=1
if [ $# -gt 0 ]; then
    START_BATCH=$1
    
    # Validate batch number
    if ! [[ "$START_BATCH" =~ ^[0-9]+$ ]]; then
        echo "❌ Error: Batch number must be a positive integer"
        exit 1
    fi
    
    if [ $START_BATCH -lt 1 ] || [ $START_BATCH -gt $TOTAL_BATCHES ]; then
        echo "❌ Error: Batch number must be between 1 and $TOTAL_BATCHES"
        exit 1
    fi
fi

echo "======================================================================" | tee -a $LOG_FILE
echo "SWE-BENCH VERIFIED FULL ANALYSIS (V3)" | tee -a $LOG_FILE
echo "======================================================================" | tee -a $LOG_FILE

# Display resume message if starting from non-default batch
if [ $START_BATCH -gt 1 ]; then
    echo "📍 Resuming from batch $START_BATCH (requested by user)" | tee -a $LOG_FILE
    echo "" | tee -a $LOG_FILE
fi

echo "Configuration:" | tee -a $LOG_FILE
echo "  - Total instances: 500" | tee -a $LOG_FILE
echo "  - Batch size: $BATCH_SIZE" | tee -a $LOG_FILE
echo "  - Total batches: $TOTAL_BATCHES" | tee -a $LOG_FILE
echo "  - Started at: $(date)" | tee -a $LOG_FILE
echo "  - Log file: $LOG_FILE" | tee -a $LOG_FILE
echo "======================================================================" | tee -a $LOG_FILE

# Check disk space (convert to GB regardless of unit)
AVAIL_SPACE=$(df -h . | tail -1 | awk '{print $4}')
# Extract numeric value and convert to GB
AVAIL_GB=$(echo "$AVAIL_SPACE" | sed 's/[^0-9.]//g')
UNIT=$(echo "$AVAIL_SPACE" | sed 's/[0-9.]//g')

echo "" | tee -a $LOG_FILE
echo "Disk space check:" | tee -a $LOG_FILE
echo "  Available: ${AVAIL_SPACE}" | tee -a $LOG_FILE

# Convert to GB if needed
if [ -n "$AVAIL_GB" ]; then
    case "$UNIT" in
        T|Ti) AVAIL_GB=$(echo "$AVAIL_GB * 1024" | awk '{print $1 * 1024}') ;;
        M|Mi) AVAIL_GB=$(echo "$AVAIL_GB / 1024" | awk '{print $1 / 1024}') ;;
        G|Gi) ;; # Already in GB
        *) AVAIL_GB=0 ;;
    esac
    
    if [ $(echo "$AVAIL_GB < 50" | awk '{print ($1 < 50)}') -eq 1 ]; then
        echo "  ⚠️  Warning: Less than 50 GB available" | tee -a $LOG_FILE
        echo "  Recommended: 50 GB (repos ~30 GB + outputs ~5 GB)" | tee -a $LOG_FILE
    else
        echo "  ✅ Sufficient disk space (${AVAIL_GB} GB)" | tee -a $LOG_FILE
    fi
else
    echo "  ⚠️  Could not determine disk space" | tee -a $LOG_FILE
fi

echo "" | tee -a $LOG_FILE

# Run batches
for i in $(seq $((START_BATCH - 1)) $((TOTAL_BATCHES - 1))); do
    START=$((i * BATCH_SIZE))
    BATCH_NUM=$((i + 1))
    
    echo "" | tee -a $LOG_FILE
    echo "======================================================================" | tee -a $LOG_FILE
    echo "BATCH $BATCH_NUM/$TOTAL_BATCHES: Instances $START-$((START + BATCH_SIZE - 1))" | tee -a $LOG_FILE
    echo "======================================================================" | tee -a $LOG_FILE
    echo "Started: $(date)" | tee -a $LOG_FILE
    echo "" | tee -a $LOG_FILE
    
    # Run analysis
    if python3 run_swebench_analysis_v3.py \
        --start-from $START \
        --limit $BATCH_SIZE \
        2>&1 | tee -a $LOG_FILE; then
        
        echo "" | tee -a $LOG_FILE
        echo "✅ Batch $BATCH_NUM completed successfully" | tee -a $LOG_FILE
        echo "Completed: $(date)" | tee -a $LOG_FILE
        
        # Save progress on success
        echo "$BATCH_NUM" > "$PROGRESS_FILE"
    else
        EXIT_CODE=$?
        echo "" | tee -a $LOG_FILE
        echo "❌ BATCH $BATCH_NUM FAILED with exit code $EXIT_CODE" | tee -a $LOG_FILE
        echo "🛑 STOPPING EXECUTION" | tee -a $LOG_FILE
        echo "" | tee -a $LOG_FILE
        
        # Calculate progress statistics
        COMPLETED_BATCHES=$((BATCH_NUM - 1))
        COMPLETED_INSTANCES=$((COMPLETED_BATCHES * BATCH_SIZE))
        REMAINING_BATCHES=$((TOTAL_BATCHES - BATCH_NUM + 1))
        REMAINING_INSTANCES=$((REMAINING_BATCHES * BATCH_SIZE))
        
        # Display detailed progress summary
        echo "📊 Progress Summary:" | tee -a $LOG_FILE
        if [ $COMPLETED_BATCHES -gt 0 ]; then
            if [ $COMPLETED_BATCHES -eq 1 ]; then
                echo "  ✅ Successfully completed batches: 1 (1 batch)" | tee -a $LOG_FILE
            else
                echo "  ✅ Successfully completed batches: 1-$COMPLETED_BATCHES ($COMPLETED_BATCHES batches)" | tee -a $LOG_FILE
            fi
            echo "  ✅ Successfully completed instances: $COMPLETED_INSTANCES instances" | tee -a $LOG_FILE
        fi
        echo "  ❌ Failed at batch: $BATCH_NUM" | tee -a $LOG_FILE
        echo "  📌 Remaining batches: $REMAINING_BATCHES batches" | tee -a $LOG_FILE
        echo "  📌 Remaining instances: $REMAINING_INSTANCES instances" | tee -a $LOG_FILE
        echo "" | tee -a $LOG_FILE
        echo "🔧 To resume after fixing the issue:" | tee -a $LOG_FILE
        echo "  ./run_full_analysis.sh $BATCH_NUM" | tee -a $LOG_FILE
        
        # Exit with the error code
        exit $EXIT_CODE
    fi
    
    # Brief pause between batches (system stability)
    if [ $i -lt $((TOTAL_BATCHES - 1)) ]; then
        echo "" | tee -a $LOG_FILE
        echo "Pausing 10 seconds before next batch..." | tee -a $LOG_FILE
        sleep 10
    fi
done

# Summary
echo "" | tee -a $LOG_FILE
echo "======================================================================" | tee -a $LOG_FILE
echo "🎉 ALL BATCHES COMPLETED SUCCESSFULLY!" | tee -a $LOG_FILE
echo "======================================================================" | tee -a $LOG_FILE
echo "Finished at: $(date)" | tee -a $LOG_FILE
echo "Total batches processed: $TOTAL_BATCHES" | tee -a $LOG_FILE
echo "Total instances processed: $TOTAL_INSTANCES" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE
echo "📁 Results location: outputs/" | tee -a $LOG_FILE
echo "📝 Log file: $LOG_FILE" | tee -a $LOG_FILE
echo "======================================================================" | tee -a $LOG_FILE

# Clean up progress file on successful completion
if [ -f "$PROGRESS_FILE" ]; then
    rm "$PROGRESS_FILE"
fi
