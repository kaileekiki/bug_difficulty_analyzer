# Bug Difficulty Analyzer

Quantitative difficulty measurement for software bugs using graph-based metrics.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run V3 analysis (Module-level scope)
python3 run_swebench_analysis_v3.py --limit 10

# View results
cat outputs/v3_summary_*.csv
```

## What's This?

Measures bug difficulty using 13 metrics:
- **DFG-GED** (Data Flow Graph Edit Distance) ⭐ Main hypothesis
- AST-GED, PDG-GED, CFG-GED, CPG-GED, Call Graph GED
- LOC, Token Distance, Cyclomatic Complexity, Halstead Difficulty
- Variable Scope, Type Changes, Exception Handling

## Project Structure

```
bug_difficulty_analyzer/
├── core/                          # Core analysis engine
│   ├── graphs.py                  # Graph data structures
│   ├── enhanced_dfg_builder.py    # DFG builder (SSA-inspired)
│   ├── cfg_builder.py             # CFG builder
│   ├── hybrid_ged.py              # Adaptive GED calculator
│   ├── repo_manager.py            # Git operations
│   └── scope_extractor.py         # Module scope extraction
│
├── metrics/                       # 13 metrics implementation
│   ├── basic_metrics.py           # LOC, Token, Cyclomatic, Halstead, Scope
│   ├── ast_metrics.py             # AST-GED, Exception, Type
│   └── graph_metrics.py           # Graph-based metrics
│
├── utils/                         # Utilities
│   └── git_diff_parser.py         # Patch parsing
│
├── production_analyzer_v2.py      # V2: Full file analysis
├── production_analyzer_v3.py      # V3: Module scope analysis ⭐
├── run_swebench_analysis_v2.py    # V2 pipeline
├── run_swebench_analysis_v3.py    # V3 pipeline ⭐
├── swebench_loader.py             # SWE-bench data loader
│
├── test_v2_analysis.py            # V2 tests
├── test_v3_scope.py               # V3 scope tests
│
└── docs/                          # All documentation
    ├── V3_QUICKSTART.md           # Start here!
    ├── V3_IMPLEMENTATION_SUMMARY.md
    └── ...
```

## Versions

| Version | Analysis Unit | Status | Use Case |
|---------|---------------|--------|----------|
| V1 | Patch hunks only | ❌ Deprecated | - |
| V2 | Full files | ✅ Stable | Single file bugs |
| V3 | Module scope | ⭐ Recommended | Real-world bugs |

## Documentation

- **Quick Start**: `docs/V3_QUICKSTART.md`
- **Implementation**: `docs/V3_IMPLEMENTATION_SUMMARY.md`
- **GED Explained**: `docs/GED_CALCULATION_EXPLAINED.md`
- **All Docs**: `docs/`

## Results

V3 results show strong correlation between DFG-GED and bug complexity:

```csv
instance_id,scope_size,dfg_ged_sum,dfg_ged_avg,dfg_ged_max
astropy-12907,59,881.0,15.5,108.5
astropy-13033,48,915.5,20.3,102.5
astropy-13236,67,1898.0,30.6,1017.5
```

## Citation

```bibtex
@software{bug_difficulty_analyzer,
  title={Bug Difficulty Analyzer: Graph-based Metrics for Software Bug Complexity},
  author={Your Name},
  year={2026},
  url={https://github.com/kaileekiki/bug_difficulty_analyzer}
}
```

## License

MIT

