# Documentation Index

## Getting Started
- **[V3 Quick Start](V3_QUICKSTART.md)** - Start here! (5 minutes)
- [V2 Quick Start](V2_QUICKSTART.md) - Single file analysis

## Implementation Details
- **[V3 Implementation](V3_IMPLEMENTATION_SUMMARY.md)** - Module scope analysis
- [V2 Implementation](V2_IMPLEMENTATION_SUMMARY.md) - Full file analysis
- [GED Calculation](GED_CALCULATION_EXPLAINED.md) - How GED works

## Usage Guides
- [Execution Guide](EXECUTION_GUIDE.md) - Step-by-step execution
- [13 Metrics Usage](USAGE_13_METRICS.md) - All metrics explained
- [How to Run](HOW_TO_RUN.md) - Running the analyzer

## Development
- [Final Summary](FINAL_SUMMARY.md) - Project summary
- [Production README](README_PRODUCTION.md) - Production deployment
- [Quick Start (Legacy)](QUICKSTART.md) - Legacy quick start guide
- [Final README (Legacy)](README_FINAL.md) - Legacy README

## Quick Reference

### Run V3 Analysis
```bash
python3 run_swebench_analysis_v3.py --limit 50
```

### Scope Configuration
```bash
# Custom scope settings
python3 run_swebench_analysis_v3.py \
  --scope-depth 2 \
  --top-k 3 \
  --limit 10
```

### View Results
```bash
# CSV summary
cat outputs/v3_summary_*.csv

# Full JSON
cat outputs/v3_full_*.json
```
