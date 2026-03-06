# SWE-bench Metric Extractor

Extracts 13 graph-based complexity metrics from SWE-bench bug patches.
Measures the difficulty of each bug fix by analyzing code structure changes (DFG, AST, CFG, etc.).

## Supported Datasets

Datasets are registered in `benchmarks.json`. The three built-in entries are:

| Alias | Name | Instances | HuggingFace |
|-------|------|-----------|-------------|
| `verified` | SWE-bench Verified | ~500 | princeton-nlp/SWE-bench_Verified |
| `full` | SWE-bench Full | ~2,294 | princeton-nlp/SWE-bench |
| `pro` | SWE-bench Pro | ~731 | ScaleAI/SWE-bench_Pro |

### Adding a New Benchmark

Edit `benchmarks.json` — no Python or shell script changes needed:

```json
{
  "my_bench": {
    "name":            "My Benchmark",
    "hf_dataset":      "org/My-Benchmark",
    "hf_split":        "test",
    "total_instances": 1000,
    "cache_file":      "my_bench.json"
  }
}
```

Then use it exactly like the built-in datasets:

```bash
./pre_clone_repos.sh my_bench
./run_parallel_tmux.sh my_bench
```

> **Requirement:** the dataset must follow SWE-bench field conventions
> (`repo`, `base_commit`, `patch` fields per instance).

## Metrics

13 metrics computed per instance, comparing code **before** and **after** the patch:

**Graph-based GED** (`metrics/graph_metrics.py`)
| Metric | Description |
|--------|-------------|
| DFG-GED | Data Flow Graph Edit Distance — main hypothesis |
| CFG-GED | Control Flow Graph Edit Distance |
| PDG-GED | Program Dependence Graph (CFG + DFG) Edit Distance |
| CPG-GED | Code Property Graph (CFG + DFG + Call Graph) Edit Distance |
| Call Graph-GED | Function call graph Edit Distance |

**AST-based** (`metrics/ast_metrics.py`)
| Metric | Description |
|--------|-------------|
| AST-GED | Abstract Syntax Tree Edit Distance (Zhang-Shasha approximation) |
| Exception Handling | Delta in try/except/raise/finally blocks |
| Type Changes | Delta in type annotations (args, return, variables) |

**Basic** (`metrics/basic_metrics.py`)
| Metric | Description |
|--------|-------------|
| LOC | Lines added / deleted / modified |
| Token Edit Distance | Levenshtein distance at token level |
| Cyclomatic Complexity | Delta in McCabe complexity per function |
| Halstead Difficulty | Delta in Halstead difficulty / volume / effort |
| Variable Scope | Changes in local / global / nonlocal variable scope |

## Setup

```bash
pip install -r requirements.txt
```

## Workflow

### Step 1: Download Dataset

Datasets are auto-downloaded on first run. To download manually:

```bash
python3 -c "from swebench_loader import SWEBenchLoader; SWEBenchLoader(dataset_type='verified').download_dataset()"
python3 -c "from swebench_loader import SWEBenchLoader; SWEBenchLoader(dataset_type='full').download_dataset()"
python3 -c "from swebench_loader import SWEBenchLoader; SWEBenchLoader(dataset_type='pro').download_dataset()"
```

Saved to `datasets/swebench_{type}.json` (gitignored).

### Step 2: Clone Repositories

```bash
./pre_clone_repos.sh <dataset>
```

Clones all unique repositories into `repo_cache/` (~10-30 GB depending on dataset).
Running without arguments prints the list of available datasets.

### Step 3: Setup Batch Copies

```bash
./setup_batch_repos.sh
```

Creates 28 independent copies in `batch_repos/batch{0-27}/` using hard links (disk-efficient).
Dataset-independent — run this once after Step 2.

### Step 4: Run Parallel Analysis

```bash
./run_parallel_tmux.sh <dataset>
```

Launches 28 tmux sessions, each processing a slice of the dataset.
Results are saved to `outputs_{type}/`.
Logs are saved to `logs/`.

Also auto-generates `stop_all_batches.sh` for stopping all sessions.

**tmux management:**
```bash
tmux ls                                    # list all sessions
tmux attach -t swebench_verified_b0        # attach to batch 0
Ctrl+B, D                                  # detach from session
./stop_all_batches.sh verified             # stop all sessions
```

### Step 5: Monitor Progress

```bash
python3 search_logs.py progress
watch -n 30 "python3 search_logs.py progress"

# Other commands
python3 search_logs.py errors              # find all errors
python3 search_logs.py instance <id>       # find specific instance
python3 search_logs.py failed              # list failed instances
```

### Step 6: Resume Interrupted Batches

If some batches stop midway:

```bash
./resume_batches.sh <dataset>
```

Automatically detects which batches are incomplete and resumes from the last saved checkpoint.
Skips batches that are already complete or still running.

### Step 7: Merge Results

```bash
python3 merge_results.py --dataset verified   # or full / pro
```

Merges all `outputs_{type}/*_results_*.json` files into:
- `outputs_{type}/merged_{timestamp}.json`
- `outputs_{type}/merged_summary_{timestamp}.csv`

## Output Format

Each result file contains per-instance metrics:

```json
{
  "instance_id": "astropy__astropy-12907",
  "repo_name": "astropy/astropy",
  "scope": {
    "primary": [...],
    "secondary": [...],
    "direct_imports": [...],
    "total_size": 59
  },
  "metrics": {
    "overall_metrics": {
      "summary": {
        "graph": { "DFG_GED": {"sum": 881.0, "avg": 15.5, "max": 108.5} },
        "ast":   { "AST_GED": {"sum": ..., "avg": ..., "max": ...} }
      }
    }
  }
}
```

## Project Structure

```
.
├── core/
│   ├── graphs.py               # Graph data structures
│   ├── enhanced_dfg_builder.py # DFG builder (SSA-inspired)
│   ├── cfg_builder.py          # CFG builder
│   ├── callgraph_builder.py    # Call graph builder
│   ├── dfg_builder.py          # Base DFG builder
│   ├── beam_search_ged.py      # Beam search GED
│   ├── ged_approximation.py    # GED approximation
│   ├── hybrid_ged.py           # Adaptive GED calculator
│   ├── repo_manager.py         # Git operations
│   └── scope_extractor.py      # Module scope extraction
├── metrics/
│   ├── basic_metrics.py        # LOC, Token, Cyclomatic, Halstead, Scope
│   ├── ast_metrics.py          # AST-GED, Exception, Type
│   └── graph_metrics.py        # Graph-based GED metrics
├── utils/
│   └── git_diff_parser.py      # Patch parsing
├── production_analyzer_v2.py   # Base analyzer (full-file analysis)
├── production_analyzer_v3.py   # V3 analyzer (module-scope analysis)
├── run_swebench_analysis_v3.py # Main pipeline entry point
├── swebench_loader.py          # Dataset loader with auto-download
├── merge_results.py            # Merge batch output files
├── search_logs.py              # Log search and progress monitoring
├── benchmarks.json             # Dataset registry (add new benchmarks here)
├── pre_clone_repos.sh          # Step 2: clone repositories
├── setup_batch_repos.sh        # Step 3: create batch copies
├── run_parallel_tmux.sh        # Step 4: launch parallel analysis
└── resume_batches.sh           # Resume interrupted batches
```

## Resource Requirements

| Dataset | Disk (repo_cache) | Disk (batch_repos) | RAM (28 workers) | Time |
|---------|-------------------|--------------------|------------------|------|
| verified | ~10 GB | ~280 GB | ~56 GB | 3-5 hours |
| full | ~30 GB | ~840 GB | ~56 GB | 15-20 hours |
| pro | ~15 GB | ~420 GB | ~56 GB | 5-8 hours |

## Single Instance (Quick Test)

```bash
python3 run_swebench_analysis_v3.py --dataset verified --limit 5
```
