#!/bin/bash
# Full SWE-bench Verified Analysis Runner
# Processes 500 instances in 10 batches of 50

set -e

LOG_FILE="v3_full_$(date +%Y%m%d_%H%M%S).log"
BATCH_SIZE=50
TOTAL_BATCHES=10

echo "======================================================================" | tee -a $LOG_FILE
echo "SWE-BENCH VERIFIED FULL ANALYSIS (V3)" | tee -a $LOG_FILE
echo "======================================================================" | tee -a $LOG_FILE
echo "Configuration:" | tee -a $LOG_FILE
echo "  - Total instances: 500" | tee -a $LOG_FILE
echo "  - Batch size: $BATCH_SIZE" | tee -a $LOG_FILE
echo "  - Total batches: $TOTAL_BATCHES" | tee -a $LOG_FILE
echo "  - Started at: $(date)" | tee -a $LOG_FILE
echo "  - Log file: $LOG_FILE" | tee -a $LOG_FILE
echo "======================================================================" | tee -a $LOG_FILE

# Check disk space
AVAIL_GB=$(df -h . | tail -1 | awk '{print $4}' | sed 's/Gi//')
echo "" | tee -a $LOG_FILE
echo "Disk space check:" | tee -a $LOG_FILE
echo "  Available: ${AVAIL_GB} GB" | tee -a $LOG_FILE

if (( $(echo "$AVAIL_GB < 50" | bc -l) )); then
    echo "  ⚠️  Warning: Less than 50 GB available" | tee -a $LOG_FILE
    echo "  Recommended: 50 GB (repos ~30 GB + outputs ~5 GB)" | tee -a $LOG_FILE
else
    echo "  ✅ Sufficient disk space" | tee -a $LOG_FILE
fi

echo "" | tee -a $LOG_FILE

# Run batches
FAILED_BATCHES=()

for i in $(seq 0 $((TOTAL_BATCHES - 1))); do
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
    else
        EXIT_CODE=$?
        echo "" | tee -a $LOG_FILE
        echo "❌ Batch $BATCH_NUM failed with exit code $EXIT_CODE" | tee -a $LOG_FILE
        echo "Failed at: $(date)" | tee -a $LOG_FILE
        FAILED_BATCHES+=($BATCH_NUM)
        
        # Continue to next batch instead of stopping
        echo "Continuing to next batch..." | tee -a $LOG_FILE
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
echo "ANALYSIS COMPLETE" | tee -a $LOG_FILE
echo "======================================================================" | tee -a $LOG_FILE
echo "Finished at: $(date)" | tee -a $LOG_FILE
echo "Total batches: $TOTAL_BATCHES" | tee -a $LOG_FILE
echo "Successful: $((TOTAL_BATCHES - ${#FAILED_BATCHES[@]}))" | tee -a $LOG_FILE
echo "Failed: ${#FAILED_BATCHES[@]}" | tee -a $LOG_FILE

if [ ${#FAILED_BATCHES[@]} -gt 0 ]; then
    echo "" | tee -a $LOG_FILE
    echo "Failed batches: ${FAILED_BATCHES[*]}" | tee -a $LOG_FILE
    echo "" | tee -a $LOG_FILE
    echo "To retry failed batches:" | tee -a $LOG_FILE
    for batch in "${FAILED_BATCHES[@]}"; do
        start=$(( (batch - 1) * BATCH_SIZE ))
        echo "  python3 run_swebench_analysis_v3.py --start-from $start --limit $BATCH_SIZE" | tee -a $LOG_FILE
    done
fi

echo "" | tee -a $LOG_FILE
echo "Results location: outputs/" | tee -a $LOG_FILE
echo "Log file: $LOG_FILE" | tee -a $LOG_FILE
echo "======================================================================" | tee -a $LOG_FILE
