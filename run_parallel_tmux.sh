#!/bin/bash
# Launch parallel analysis across 28 tmux sessions.
# Usage: ./run_parallel_tmux.sh <dataset>
#
# Available datasets are defined in benchmarks.json.
# Also generates stop_all_batches.sh for stopping sessions.

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
    echo "  $0 verified"
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

# ── Settings ─────────────────────────────────────────────────────────────────
NUM_WORKERS=28
BATCH_SIZE=$((TOTAL_INSTANCES / NUM_WORKERS))
OUTPUT_DIR="outputs_${DATASET_TYPE}"

mkdir -p logs
mkdir -p "$OUTPUT_DIR"

echo "=========================================="
echo "SWE-bench Parallel Analysis"
echo "=========================================="
echo "Dataset  : $DATASET_NAME"
echo "Instances: $TOTAL_INSTANCES"
echo "Workers  : $NUM_WORKERS"
echo "Batch    : ~$BATCH_SIZE instances each"
echo "Output   : $OUTPUT_DIR/"
echo "=========================================="
echo ""

# ── Check prerequisites ───────────────────────────────────────────────────────
if ! command -v tmux &> /dev/null; then
    echo "Error: tmux is not installed."
    echo "  macOS : brew install tmux"
    echo "  Linux : apt install tmux"
    exit 1
fi

if [ ! -d "batch_repos/batch0" ]; then
    echo "Error: batch_repos/ is not set up."
    echo "  Run: ./setup_batch_repos.sh"
    exit 1
fi

# ── Launch one tmux session per batch ────────────────────────────────────────
for i in $(seq 0 $((NUM_WORKERS - 1))); do
    START=$((i * BATCH_SIZE))

    if [ $i -eq $((NUM_WORKERS - 1)) ]; then
        LIMIT=$((TOTAL_INSTANCES - START))
    else
        LIMIT=$BATCH_SIZE
    fi

    SESSION="swebench_${DATASET_TYPE}_b${i}"
    LOGFILE="logs/batch${i}_${START}_$((START + LIMIT - 1))_${DATASET_TYPE}_$(date +%Y%m%d_%H%M%S).log"
    BATCH_REPO_DIR="$SCRIPT_DIR/batch_repos/batch${i}"

    tmux kill-session -t "$SESSION" 2>/dev/null || true

    tmux new-session -d -s "$SESSION" bash -c "
        cd '$SCRIPT_DIR'
        echo '==========================================' | tee '$LOGFILE'
        echo 'Dataset: $DATASET_NAME' | tee -a '$LOGFILE'
        echo 'Batch $i: instances $START to $((START + LIMIT - 1))' | tee -a '$LOGFILE'
        echo 'Repo  : $BATCH_REPO_DIR' | tee -a '$LOGFILE'
        echo '==========================================' | tee -a '$LOGFILE'
        echo '' | tee -a '$LOGFILE'

        BATCH_ID=$i python3 run_swebench_analysis_v3.py \
            --dataset $DATASET_TYPE \
            --start-from $START \
            --limit $LIMIT \
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

    echo "Started: $SESSION  (instances $START–$((START + LIMIT - 1)))"
    sleep 0.5
done

echo ""
echo "=========================================="
echo "All $NUM_WORKERS batches started!"
echo "=========================================="
echo ""
echo "Monitor progress:"
echo "  python3 search_logs.py progress"
echo "  watch -n 30 'python3 search_logs.py progress'"
echo ""
echo "Attach to a session:"
echo "  tmux ls"
echo "  tmux attach -t swebench_${DATASET_TYPE}_b0"
echo "  Ctrl+B, D  — detach"
echo ""
echo "Stop all sessions:"
echo "  ./stop_all_batches.sh $DATASET_TYPE"
echo "=========================================="

# ── Generate stop_all_batches.sh ─────────────────────────────────────────────
cat > stop_all_batches.sh << 'STOP_SCRIPT'
#!/bin/bash
# Usage: ./stop_all_batches.sh <dataset>   — stop sessions for one dataset
#        ./stop_all_batches.sh all         — stop all swebench sessions

DATASET_TYPE="${1:-}"

if [ -z "$DATASET_TYPE" ]; then
    echo "Usage: $0 <dataset|all>"
    exit 1
fi

if [ "$DATASET_TYPE" = "all" ]; then
    echo "Stopping all swebench sessions..."
    for session in $(tmux ls -F "#{session_name}" 2>/dev/null | grep "^swebench_"); do
        echo "  Killing: $session"
        tmux kill-session -t "$session"
    done
else
    echo "Stopping swebench_${DATASET_TYPE} sessions..."
    for session in $(tmux ls -F "#{session_name}" 2>/dev/null | grep "^swebench_${DATASET_TYPE}_"); do
        echo "  Killing: $session"
        tmux kill-session -t "$session"
    done
fi

echo "Done."
STOP_SCRIPT

chmod +x stop_all_batches.sh
