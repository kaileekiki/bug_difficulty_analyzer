# V2 Full Repository Analysis - Quick Start

## Overview
V2 adds full repository support for accurate metric calculations. Unlike V1 (which only processes patch hunks), V2 analyzes complete files before and after changes.

## Key Features
- **Full file analysis** instead of just patch hunks
- **Repository caching** to avoid re-cloning
- **Real metric values** (no more 0s and -1s)
- **Complete code graphs** for semantic analysis

## Quick Start

### 1. Test with Mock Data (2 instances)
```bash
python3 run_swebench_analysis_v2.py --mock --limit 2
```

### 2. Analyze SWE-bench Dataset (5 instances)
```bash
python3 run_swebench_analysis_v2.py --limit 5
```

### 3. Full Dataset Analysis
```bash
python3 run_swebench_analysis_v2.py
```

## Command Line Options
```
--limit N          # Process only N instances
--start-from N     # Resume from instance N
--mock             # Use mock data for testing
--no-hybrid        # Disable hybrid GED (use fixed beam width)
--repo-cache DIR   # Custom repository cache directory
```

## Output Files
Results are saved in `outputs/`:
- `swebench_v2_YYYYMMDD_HHMMSS.json` - Complete results
- `swebench_v2_YYYYMMDD_HHMMSS_summary.csv` - Summary spreadsheet
- `progress_v2_*.json` - Progress checkpoints (every 5 instances)

## Repository Cache
Cloned repositories are cached in `repo_cache/`:
```
repo_cache/
├── django_django/
├── astropy_astropy/
└── ...
```

To clean the cache:
```bash
rm -rf repo_cache/
```

## Expected Results

### V1 (Patch Hunks Only)
Most metrics return 0 or -1:
```
AST-GED: 0
DFG-GED: 0
CFG-GED: -1
LOC: Limited to changed lines
```

### V2 (Full Files)
Real metric values:
```
AST-GED: 59.00
DFG-GED: 12.50  ⭐ (Main hypothesis)
CFG-GED: 2.00
Call Graph-GED: 1.00
PDG-GED: 14.50
CPG-GED: 15.50
LOC: Accurate full file comparison
```

## Test V2 Analyzer Directly
```python
from production_analyzer_v2 import ProductionBugAnalyzerV2

# Create analyzer
analyzer = ProductionBugAnalyzerV2(repo_cache_dir="repo_cache")

# Analyze instance
instance = {
    'repo': 'https://github.com/owner/repo',
    'base_commit': 'abc123',
    'patch': '... git diff ...'
}

result = analyzer.analyze_instance(instance, 'test-001')
print(result)
```

## Testing
```bash
# Test repository manager
python3 core/repo_manager.py

# Test V2 analyzer with actual code
python3 test_v2_analysis.py

# Test V2 pipeline with mock data
python3 run_swebench_analysis_v2.py --mock --limit 2
```

## Backward Compatibility
V1 files remain unchanged:
- `production_analyzer.py` - Original analyzer
- `run_swebench_analysis.py` - Original pipeline

Use V1 if you only need patch-based analysis:
```bash
python3 run_swebench_analysis.py --limit 5
```

## Requirements
- Python 3.8+
- Git command in PATH
- ~500MB disk space per large repository (Django, etc.)
- Internet connection for cloning repositories

## Timeouts
- Clone: 300 seconds
- Checkout: 30 seconds
- Patch apply: 30 seconds

## Progress Tracking
Progress is saved every 5 instances (changed from 10 in V1).
To resume from instance 100:
```bash
python3 run_swebench_analysis_v2.py --start-from 100
```

## Troubleshooting

### Clone timeout
Large repos may timeout. The system automatically tries shallow clone first, then full clone.

### Patch apply fails
This is normal for some SWE-bench instances. The analyzer continues and analyzes available files.

### File not found
If a file doesn't exist at base_commit, it's treated as new file (empty before content).

## Configuration
Default settings in code:
```python
repo_cache_dir = "repo_cache"      # Repository cache
clone_timeout = 300                 # 5 minutes
checkout_timeout = 30               # 30 seconds
use_hybrid_ged = True              # Adaptive beam width
progress_save_interval = 5          # Every 5 instances
```

## Performance
- First run: Slow (clones repositories)
- Subsequent runs: Fast (uses cache)
- Average: 10-30 seconds per instance (cached)

## Disk Space
- Small repos (< 50MB): ~20MB cached
- Medium repos (50-200MB): ~100MB cached
- Large repos (Django): ~500MB cached

Clean up space:
```bash
# Remove all cached repos
rm -rf repo_cache/

# Remove specific repo
rm -rf repo_cache/django_django
```
