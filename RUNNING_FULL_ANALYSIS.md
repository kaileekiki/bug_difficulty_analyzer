# Running Full SWE-bench Analysis

Guide for running the complete 500-instance analysis.

## Prerequisites

- **Disk space**: 50+ GB free
- **Time**: ~8-10 hours
- **RAM**: 4+ GB recommended

## Quick Start

### Using screen/tmux (Recommended)

```bash
# Start screen session
screen -S swebench

# Run full analysis
./run_full_analysis.sh

# Detach: Ctrl+A, then D

# Reattach later
screen -r swebench
```

### Direct run (foreground)

```bash
./run_full_analysis.sh
```

### Background with nohup

```bash
nohup ./run_full_analysis.sh &
tail -f v3_full_*.log
```

## Monitoring Progress

### In another terminal:

```bash
# Real-time monitor (auto-refresh)
./monitor_analysis.sh

# Or manual checks:
tail -f v3_full_*.log
ls -lh outputs/
```

### Progress file:

```bash
cat outputs/progress_v3_*.json
```

## Handling Interruptions

### Resume from checkpoint:

```bash
# Check last completed instance
cat outputs/progress_v3_*.json | grep "processed"

# Resume from that point (e.g., 234)
python3 run_swebench_analysis_v3.py --start-from 234
```

### After Completion

### Merge results (if run in batches):

```bash
python3 merge_results.py
```

### View results:

```bash
# CSV summary
cat outputs/v3_merged_summary_*.csv

# Or individual batch results
cat outputs/v3_summary_*.csv
```

## Troubleshooting

### Out of disk space:

```bash
# Clean repo cache (will re-download on next run)
rm -rf repo_cache/

# Or clean specific repos
rm -rf repo_cache/large_repo_name/
```

### Stuck on one instance:

Kill and resume:
```bash
# Find process
ps aux | grep python3

# Kill
kill <PID>

# Resume from last checkpoint
python3 run_swebench_analysis_v3.py --start-from <last_completed_instance>
```

### Memory issues:

```bash
# Monitor memory usage
watch -n 5 'ps aux | grep python3 | grep -v grep'

# If memory is high, restart in smaller batches
python3 run_swebench_analysis_v3.py --start-from <N> --limit 10
```

### Batch failure:

```bash
# Check the log for failed batches
tail -100 v3_full_*.log

# Retry specific batch (e.g., batch 5 = instances 200-249)
python3 run_swebench_analysis_v3.py --start-from 200 --limit 50
```

## Advanced Usage

### Custom batch size:

Edit `run_full_analysis.sh` and modify:
```bash
BATCH_SIZE=25  # Smaller batches for stability
TOTAL_BATCHES=20
```

### Different scope configuration:

```bash
# Faster analysis (smaller scope)
python3 run_swebench_analysis_v3.py --scope-depth 2 --top-k 3

# More accurate (larger scope)
python3 run_swebench_analysis_v3.py --scope-depth 4 --top-k 10
```

## Performance Tips

### Speed optimization:
- Use smaller scope: `--scope-depth 1 --top-k 2`
- Disable hybrid GED: `--no-hybrid`
- Run during off-peak hours

### Stability optimization:
- Use screen/tmux for long runs
- Monitor disk space regularly
- Keep repo cache if re-running
- Save progress frequently (done automatically every 5 instances)

## Results

After successful completion:

- **JSON results**: `outputs/v3_results_*.json`
- **CSV summary**: `outputs/v3_summary_*.csv`
- **Merged results**: `outputs/v3_merged_*.json` (after running merge_results.py)
- **Progress checkpoints**: `outputs/progress_v3_*.json`
- **Logs**: `v3_full_*.log`

## FAQ

**Q: How long does it take?**  
A: Approximately 8-10 hours for all 500 instances with default settings (60s per instance average).

**Q: Can I pause and resume?**  
A: Yes! The pipeline saves progress every 5 instances. Use `--start-from` to resume.

**Q: What if a batch fails?**  
A: The script continues with the next batch. Failed batches are reported at the end with retry commands.

**Q: How much disk space is needed?**  
A: 50+ GB recommended (repos ~30 GB + outputs ~5 GB + overhead ~15 GB).

**Q: Can I run multiple analyses in parallel?**  
A: Not recommended. They will compete for resources and may cause issues with repo cache.

**Q: How do I clean up after analysis?**  
A: 
```bash
# Keep results, remove cache
rm -rf repo_cache/

# Archive results
tar -czf results_archive.tar.gz outputs/

# Remove archived results
rm -rf outputs/
```

## Getting Help

- Check logs: `tail -100 v3_full_*.log`
- Review progress: `cat outputs/progress_v3_*.json`
- Monitor resources: `./monitor_analysis.sh`
- Read documentation: `docs/V3_QUICKSTART.md`

## Example Session

```bash
# 1. Start analysis in screen
screen -S swebench
./run_full_analysis.sh

# 2. Detach (Ctrl+A, D)

# 3. Monitor in another terminal
./monitor_analysis.sh

# 4. After completion (8-10 hours later)
python3 merge_results.py

# 5. View results
cat outputs/v3_merged_summary_*.csv
```

## Success Criteria

✅ All 500 instances processed  
✅ Results saved in `outputs/`  
✅ CSV summary generated  
✅ No critical errors in logs  
✅ Merged results created (if using batches)

---

**Note**: This guide assumes you have already installed dependencies and downloaded the SWE-bench dataset. See `docs/V3_QUICKSTART.md` for initial setup.
