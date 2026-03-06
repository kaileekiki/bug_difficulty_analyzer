#!/bin/bash
# Clone all repositories needed for a dataset.
# Usage: ./pre_clone_repos.sh <dataset>
#
# Available datasets are defined in benchmarks.json.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Helper: print available datasets from registry ──────────────────────────
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

# ── Validate against registry ────────────────────────────────────────────────
DATASET_NAME=$(python3 -c "
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
print(reg['$DATASET_TYPE']['name'])
") || exit 1

DATASET_FILE="datasets/swebench_${DATASET_TYPE}.json"
REPO_CACHE="repo_cache"

echo "=========================================="
echo "Repository Pre-Clone"
echo "=========================================="
echo "Dataset : $DATASET_NAME"
echo "File    : $DATASET_FILE"
echo ""

# ── Check dataset file ───────────────────────────────────────────────────────
if [ ! -f "$DATASET_FILE" ]; then
    echo "Error: dataset file not found: $DATASET_FILE"
    echo ""
    echo "Download it first:"
    echo "  python3 -c \"from swebench_loader import SWEBenchLoader; SWEBenchLoader(dataset_type='$DATASET_TYPE').download_dataset()\""
    exit 1
fi

mkdir -p "$REPO_CACHE"

# ── Extract unique repos from dataset ────────────────────────────────────────
echo "Extracting repository list..."
REPOS=$(python3 -c "
import json
with open('$DATASET_FILE') as f:
    data = json.load(f)
repos = set()
for item in data:
    repo = item['repo']
    if 'github.com/' in repo:
        repo = repo.split('github.com/')[-1].replace('.git', '')
    repos.add(repo)
for repo in sorted(repos):
    print(repo)
")

REPO_COUNT=$(echo "$REPOS" | grep -c .)
echo "Found $REPO_COUNT unique repositories"
echo ""

# ── Clone each repo ───────────────────────────────────────────────────────────
CURRENT=0
for REPO in $REPOS; do
    CURRENT=$((CURRENT + 1))
    REPO_NAME=$(echo "$REPO" | tr '/' '_')
    REPO_PATH="$REPO_CACHE/$REPO_NAME"
    REPO_URL="https://github.com/$REPO.git"

    echo "[$CURRENT/$REPO_COUNT] $REPO"

    if [ -d "$REPO_PATH/.git" ]; then
        cd "$REPO_PATH"
        if git rev-parse --git-dir >/dev/null 2>&1; then
            echo "  Already cloned: $REPO_PATH"
            cd - >/dev/null
            continue
        else
            echo "  Corrupted repo, re-cloning..."
            cd - >/dev/null
            rm -rf "$REPO_PATH"
        fi
    fi

    if git clone "$REPO_URL" "$REPO_PATH"; then
        REPO_SIZE=$(du -sh "$REPO_PATH" 2>/dev/null | cut -f1 || echo "N/A")
        echo "  Cloned ($REPO_SIZE)"
    else
        echo "  Clone failed — skipping"
    fi
    echo ""
done

echo "=========================================="
echo "All repositories cloned!"
echo "=========================================="
echo ""
echo "repo_cache/ size: $(du -sh "$REPO_CACHE" | cut -f1)"
echo ""
echo "Next steps:"
echo "  ./setup_batch_repos.sh"
echo "  ./run_parallel_tmux.sh $DATASET_TYPE"
