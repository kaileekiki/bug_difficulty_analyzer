#!/bin/bash
# Resume only the batches that stopped midway.
# Usage: ./resume_batches.sh <dataset>
#
# - Skips batches that already have a completed results file
# - Skips batches whose tmux session is still running
# - Resumes from the latest progress checkpoint if one exists
# - Starts from scratch for batches with no progress at all
#
# Available datasets are defined in benchmarks.json.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Helper: print available datasets ────────────────────────────────────────
print_usage() {
    echo "Usage: $0 <dataset>"
    echo ""
    echo "Available datasets (defined in benchmarks.json):"
    python3 -c "
import json, sys
try:
    reg = {k: v for k, v in json.load(open('benchmarks.json')).items() if not k.startswith('_')}
    for alias, info in reg.items():
        print(f'  {alias:<12}  {info[\"name\"]}  ({info[\"total_instances\"]} instances)')
except FileNotFoundError:
    print('  (benchmarks.json not found)')
"
    echo ""
    echo "Example:"
    echo "  $0 full"
}

# ── Require exactly one argument ─────────────────────────────────────────────
if [ $# -eq 0 ]; then
    print_usage
    exit 1
fi

DATASET_TYPE="$1"

# ── Load info from registry ───────────────────────────────────────────────────
read -r DATASET_NAME TOTAL_INSTANCES <<< $(python3 -c "
import json, sys
try:
    reg = {k: v for k, v in json.load(open('benchmarks.json')).items() if not k.startswith('_')}
except FileNotFoundError:
    print('Error: benchmarks.json not found', file=sys.stderr)
    sys.exit(1)
if '$DATASET_TYPE' not in reg:
    available = ', '.join(reg.keys())
    print(f\"Error: unknown dataset '$DATASET_TYPE'. Available: {available}\", file=sys.stderr)
    sys.exit(1)
info = reg['$DATASET_TYPE']
print(info['name'], info['total_instances'])
") || exit 1

NUM_WORKERS=28
BATCH_SIZE=$((TOTAL_INSTANCES / NUM_WORKERS))
OUTPUT_DIR="outputs_${DATASET_TYPE}"

mkdir -p logs

echo "=========================================="
echo "Resume Interrupted Batches"
echo "=========================================="
echo "Dataset  : $DATASET_NAME"
echo "Instances: $TOTAL_INSTANCES"
echo "Workers  : $NUM_WORKERS"
echo "Output   : $OUTPUT_DIR/"
echo "=========================================="
echo ""

RESUMED=0
SKIPPED=0
FRESH=0

for i in $(seq 0 $((NUM_WORKERS - 1))); do
    START=$((i * BATCH_SIZE))

    if [ $i -eq $((NUM_WORKERS - 1)) ]; then
        LIMIT=$((TOTAL_INSTANCES - START))
    else
        LIMIT=$BATCH_SIZE
    fi

    END=$((START + LIMIT - 1))
    SESSION="swebench_${DATASET_TYPE}_b${i}"
    BATCH_REPO_DIR="$SCRIPT_DIR/batch_repos/batch${i}"

    # 1) Already completed — results file exists
    RESULT_FILE=$(ls "$OUTPUT_DIR"/batch${i}_*_results_*.json 2>/dev/null | tail -1)
    if [ -n "$RESULT_FILE" ]; then
        echo "  [batch $i] Done — skipping ($START–$END)"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    # 2) Already running — tmux session alive
    if tmux has-session -t "$SESSION" 2>/dev/null; then
        echo "  [batch $i] Running — skipping ($START–$END)"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    # 3) Has a progress checkpoint — resume from last saved count
    LATEST_PROGRESS=$(ls "$OUTPUT_DIR"/batch${i}_*_progress_*.json 2>/dev/null | tail -1)
    if [ -n "$LATEST_PROGRESS" ]; then
        COUNT=$(basename "$LATEST_PROGRESS" | sed 's/.*_progress_\([0-9]*\)_.*/\1/')
        RESUME_FROM=$((START + COUNT))
        RESUME_LIMIT=$((LIMIT - COUNT))

        if [ "$RESUME_LIMIT" -le 0 ]; then
            echo "  [batch $i] Progress complete — skipping ($START–$END)"
            SKIPPED=$((SKIPPED + 1))
            continue
        fi

        echo "  [batch $i] Resuming from instance $RESUME_FROM ($COUNT/$LIMIT done)"
        RESUMED=$((RESUMED + 1))
    else
        # 4) No progress at all — start from scratch
        RESUME_FROM=$START
        RESUME_LIMIT=$LIMIT
        echo "  [batch $i] Starting fresh ($START–$END)"
        FRESH=$((FRESH + 1))
    fi

    LOGFILE="logs/batch${i}_${RESUME_FROM}_${END}_${DATASET_TYPE}_$(date +%Y%m%d_%H%M%S).log"

    tmux kill-session -t "$SESSION" 2>/dev/null || true

    tmux new-session -d -s "$SESSION" bash -c "
        cd '$SCRIPT_DIR'
        echo '==========================================' | tee '$LOGFILE'
        echo 'Dataset: $DATASET_NAME' | tee -a '$LOGFILE'
        echo 'Batch $i: resuming from $RESUME_FROM to $END' | tee -a '$LOGFILE'
        echo 'Repo  : $BATCH_REPO_DIR' | tee -a '$LOGFILE'
        echo '==========================================' | tee -a '$LOGFILE'
        echo '' | tee -a '$LOGFILE'

        BATCH_ID=$i python3 run_swebench_analysis_v3.py \
            --dataset $DATASET_TYPE \
            --start-from $RESUME_FROM \
            --limit $RESUME_LIMIT \
            --output-dir $OUTPUT_DIR \
            --repo-cache $BATCH_REPO_DIR \
            2>&1 | tee -a '$LOGFILE'

        echo '' | tee -a '$LOGFILE'
        echo '==========================================' | tee -a '$LOGFILE'
        echo 'Batch $i complete!' | tee -a '$LOGFILE'
        echo '==========================================' | tee -a '$LOGFILE'
        echo ''
        echo 'Press ENTER to close this session...'
        read
    "

    sleep 0.5
done

echo ""
echo "=========================================="
echo "Resume complete"
echo "=========================================="
echo "  Skipped (done/running) : $SKIPPED"
echo "  Resumed from checkpoint : $RESUMED"
echo "  Started fresh           : $FRESH"
echo ""
echo "Monitor:"
echo "  tmux ls"
echo "  python3 search_logs.py progress"
echo "=========================================="
