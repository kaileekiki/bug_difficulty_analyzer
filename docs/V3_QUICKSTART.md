# V3 Module-Level Scope Analysis

## Overview

V3 introduces **module-level scope analysis** for bug difficulty measurement. Unlike V2 which only analyzes changed files, V3 analyzes the entire module context to capture cross-file dependencies and provide more accurate complexity assessment.

## Key Features

### 1. Module-Level Scope Extraction

V3 automatically expands the analysis scope beyond just changed files:

```
Scope = Primary_Modules ∪ Secondary_Modules ∪ Direct_Imports

where:
- Primary_Modules: ALL files in modules containing changed files (Depth=3)
- Secondary_Modules: Top-5 files from dependent modules  
- Direct_Imports: Explicitly imported files
```

### 2. Enhanced Metrics

- **Scope Information**: Total scope size, primary/secondary/import counts
- **Context Analysis**: Separate metrics for changed vs context files
- **Module-Level GED**: More accurate graph edit distance capturing cross-file changes

## Installation

No additional dependencies needed. V3 uses the same infrastructure as V2.

```bash
cd /path/to/bug_difficulty_analyzer
# V3 is ready to use!
```

## Usage

### Basic Usage

```bash
# Analyze with default settings (depth=3, top-k=5)
python3 run_swebench_analysis_v3.py --limit 5

# Use mock data for testing
python3 run_swebench_analysis_v3.py --mock --limit 2
```

### Custom Scope Configuration

```bash
# Adjust module depth (1-5)
python3 run_swebench_analysis_v3.py --limit 5 --scope-depth 2

# Adjust secondary modules count (1-20)
python3 run_swebench_analysis_v3.py --limit 5 --top-k 10

# Combine both
python3 run_swebench_analysis_v3.py --limit 5 --scope-depth 4 --top-k 8
```

### Advanced Options

```bash
# Resume from checkpoint
python3 run_swebench_analysis_v3.py --start-from 50 --limit 100

# Use different repo cache
python3 run_swebench_analysis_v3.py --repo-cache /tmp/repos --limit 10

# Disable hybrid GED (faster but less accurate)
python3 run_swebench_analysis_v3.py --no-hybrid --limit 5
```

## Configuration Parameters

### Scope Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `--scope-depth` | 3 | 1-5 | Directory levels up from changed file to include |
| `--top-k` | 5 | 1-20 | Number of secondary module files to include |

**Depth Examples:**
```python
# Changed file: astropy/modeling/separable.py

depth=1: astropy/*.py
depth=2: astropy/modeling/*.py  
depth=3: astropy/modeling/**/*.py (DEFAULT)
depth=4: astropy/modeling/**/**/*.py
```

### General Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--limit` | None | Max instances to analyze |
| `--start-from` | 0 | Start index (for resuming) |
| `--mock` | False | Use mock data instead of real dataset |
| `--no-hybrid` | False | Disable hybrid GED calculator |
| `--repo-cache` | repo_cache | Repository cache directory |

## Output Format

### JSON Output

```json
{
  "instance_id": "astropy-12907",
  "scope": {
    "primary": ["file1.py", "file2.py", ...],
    "secondary": ["dep1.py", ...],
    "direct_imports": ["import1.py", ...],
    "total_size": 45
  },
  "metrics": {
    "num_files_analyzed": 45,
    "num_changed_files": 3,
    "num_context_files": 42,
    "changed_files_metrics": {...},
    "context_files_metrics": {...},
    "overall_metrics": {
      "summary": {
        "graph": {
          "DFG_GED": {"sum": 12.5, "avg": 2.5, "max": 5.0}
        }
      }
    }
  }
}
```

### CSV Output

The CSV includes scope information:

```csv
instance_id,repo_name,num_changed_files,scope_size,primary_files,secondary_files,direct_imports,...
astropy-12907,astropy_astropy,3,45,38,5,2,12.5,2.5,5.0,...
```

## Programmatic Usage

### Basic Example

```python
from production_analyzer_v3 import ProductionBugAnalyzerV3
from swebench_loader import SWEBenchLoader

# Initialize V3 analyzer
analyzer = ProductionBugAnalyzerV3(
    scope_depth=3,
    top_k_secondary=5
)

# Load dataset
loader = SWEBenchLoader()
dataset = loader.load_dataset()
instance = dataset[0]

# Analyze
result = analyzer.analyze_instance(instance, instance['instance_id'])

# Check scope
print(f"Scope size: {result['scope']['total_size']}")
print(f"Primary: {len(result['scope']['primary'])}")
print(f"Secondary: {len(result['scope']['secondary'])}")
```

### Custom Scope Configuration

```python
# Shallow scope (faster, less context)
analyzer = ProductionBugAnalyzerV3(
    scope_depth=1,
    top_k_secondary=2
)

# Deep scope (slower, more context)
analyzer = ProductionBugAnalyzerV3(
    scope_depth=4,
    top_k_secondary=10
)
```

## Comparison: V2 vs V3

| Aspect | V2 | V3 |
|--------|----|----|
| Scope | Changed files only | Full module context |
| Typical Files | 1-2 | 10-50 |
| Analysis Time | 10-30s | 60-120s |
| GED Accuracy | Good | Better |
| Context Capture | Limited | Comprehensive |
| Cross-file Dependencies | ❌ | ✅ |

## Examples

### Example 1: Small Bug Fix

```bash
# Changed: myapp/core/models.py

# V2 analyzes: 1 file
# V3 analyzes (depth=3, k=5):
# - Primary: myapp/core/*.py (10 files)
# - Secondary: myapp/utils/*.py (5 files)  
# - Imports: myapp/config.py (1 file)
# Total: 16 files
```

### Example 2: Astropy Bug

```bash
# Changed: astropy/modeling/separable.py

# V2: 1 file
# V3 (depth=3, k=5):
# - Primary: astropy/modeling/ (38 files)
# - Secondary: astropy/coordinates/ (5 files)
# - Imports: astropy/utils/indent.py (1 file)
# Total: 44 files
```

## Performance Tips

### For Speed
```bash
# Reduce scope
python3 run_swebench_analysis_v3.py --scope-depth 1 --top-k 2 --limit 100

# Disable hybrid GED
python3 run_swebench_analysis_v3.py --no-hybrid --limit 100
```

### For Accuracy
```bash
# Increase scope
python3 run_swebench_analysis_v3.py --scope-depth 4 --top-k 10 --limit 20

# Use hybrid GED (default)
python3 run_swebench_analysis_v3.py --limit 20
```

## Testing

### Unit Tests
```bash
# Test scope extractor
python3 core/scope_extractor.py

# Test V3 functionality
python3 test_v3_scope.py
```

### Integration Tests
```bash
# Test with mock data
python3 run_swebench_analysis_v3.py --mock --limit 2

# Test with real data (small sample)
python3 run_swebench_analysis_v3.py --limit 1
```

## Troubleshooting

### Issue: Scope too large
```bash
# Reduce depth or top-k
python3 run_swebench_analysis_v3.py --scope-depth 2 --top-k 3
```

### Issue: Analysis too slow
```bash
# Use shallower scope
python3 run_swebench_analysis_v3.py --scope-depth 1 --no-hybrid
```

### Issue: Missing context
```bash
# Increase scope
python3 run_swebench_analysis_v3.py --scope-depth 4 --top-k 10
```

## Migration from V2

V3 is **backward compatible** with V2. You can:

1. Keep using V2: `run_swebench_analysis_v2.py`
2. Switch to V3: `run_swebench_analysis_v3.py`  
3. Compare results from both versions

No code changes needed in your analysis scripts.

## Research Questions Supported

V3 directly addresses:

- **RQ1**: Better difficulty prediction through module-level context
- **RQ2**: Captures cross-file dependencies via scope analysis
- **RQ3**: More accurate GED computation with full module graphs

## Future Enhancements

Potential V4 features:
- Semantic similarity for secondary module ranking
- Dynamic scope adjustment based on code coupling
- Incremental analysis for large repositories
- Parallel scope extraction for faster processing

## References

- V2 Documentation: `V2_QUICKSTART.md`
- Scope Extractor: `core/scope_extractor.py`
- V3 Analyzer: `production_analyzer_v3.py`
- V3 Pipeline: `run_swebench_analysis_v3.py`
