#!/usr/bin/env python3
"""
Merge V3 Analysis Results
Combines batch result files from outputs_{type}/ into a single merged file.

Usage:
    python3 merge_results.py --dataset verified
    python3 merge_results.py --dataset full
    python3 merge_results.py --dataset pro
    python3 merge_results.py --output-dir outputs_verified
"""

import json
import glob
import argparse
from datetime import datetime
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is required for this script")
    print("   Install with: pip install pandas")
    exit(1)


def merge_results(output_dir: str):
    """Merge all result files from the given output directory"""

    print("="*70)
    print("MERGING V3 ANALYSIS RESULTS")
    print("="*70)
    print(f"Source directory: {output_dir}")

    # Find all result files
    result_files = sorted(glob.glob(f'{output_dir}/*_results_*.json'))
    print(f"\nFound {len(result_files)} result files:")
    for f in result_files:
        size = Path(f).stat().st_size / (1024*1024)
        print(f"   - {f} ({size:.1f} MB)")

    if not result_files:
        print(f"\nNo result files found in {output_dir}/")
        print("   Looking for pattern: *_results_*.json")
        return

    # Merge all results
    all_results = []
    all_errors = []

    print(f"\nMerging results...")
    for file in result_files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                all_results.extend(data.get('results', []))
                all_errors.extend(data.get('errors', []))
        except Exception as e:
            print(f"   Warning: Error reading {file}: {e}")

    print(f"   - Total results loaded: {len(all_results)}")

    # Remove duplicates by instance_id
    seen = set()
    unique_results = []
    duplicates = 0

    for r in all_results:
        iid = r.get('instance_id')
        if not iid or iid not in seen:
            if iid:
                seen.add(iid)
            unique_results.append(r)
        else:
            duplicates += 1

    print(f"   - Unique instances: {len(unique_results)}")
    if duplicates > 0:
        print(f"   - Duplicates removed: {duplicates}")

    successful = [r for r in unique_results if not r.get('errors')]
    with_errors = [r for r in unique_results if r.get('errors')]

    print(f"\nStatistics:")
    print(f"   Successful: {len(successful)}")
    print(f"   With errors: {len(with_errors)}")
    print(f"   Failed completely: {len(all_errors)}")

    # Save merged JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    merged = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'version': 'v3',
            'total_instances': len(unique_results),
            'successful': len(successful),
            'with_errors': len(with_errors),
            'merged_files': len(result_files),
            'source_files': result_files
        },
        'results': unique_results,
        'errors': all_errors
    }

    json_file = f'{output_dir}/merged_{timestamp}.json'
    with open(json_file, 'w') as f:
        json.dump(merged, f, indent=2)

    json_size = Path(json_file).stat().st_size / (1024*1024)
    print(f"\nMerged JSON saved:")
    print(f"   {json_file} ({json_size:.1f} MB)")

    # Create merged CSV
    print(f"\nCreating merged CSV...")

    csv_rows = []
    for result in unique_results:
        row = {
            'instance_id': result.get('instance_id'),
            'repo_name': result.get('repo_name'),
            'analysis_time': result.get('analysis_time', 0),
            'has_errors': bool(result.get('errors'))
        }

        scope = result.get('scope', {})
        row['scope_size'] = scope.get('total_size', 0)
        row['primary_files'] = len(scope.get('primary', []))
        row['secondary_files'] = len(scope.get('secondary', []))
        row['direct_imports'] = len(scope.get('direct_imports', []))

        metrics = result.get('metrics', {})
        overall = metrics.get('overall_metrics', {})
        summary = overall.get('summary', {})

        graph_metrics = summary.get('graph', {})
        dfg_ged = graph_metrics.get('DFG_GED', {})
        row['dfg_ged_sum'] = dfg_ged.get('sum', -1)
        row['dfg_ged_avg'] = dfg_ged.get('avg', -1)
        row['dfg_ged_max'] = dfg_ged.get('max', -1)

        ast_ged = summary.get('ast', {}).get('AST_GED', {})
        row['ast_ged_sum'] = ast_ged.get('sum', -1)
        row['ast_ged_avg'] = ast_ged.get('avg', -1)
        row['ast_ged_max'] = ast_ged.get('max', -1)

        cfg_ged = graph_metrics.get('CFG_GED', {})
        row['cfg_ged_sum'] = cfg_ged.get('sum', -1)
        row['cfg_ged_avg'] = cfg_ged.get('avg', -1)
        row['cfg_ged_max'] = cfg_ged.get('max', -1)

        csv_rows.append(row)

    df = pd.DataFrame(csv_rows)
    csv_file = f'{output_dir}/merged_summary_{timestamp}.csv'
    df.to_csv(csv_file, index=False)

    csv_size = Path(csv_file).stat().st_size / 1024
    print(f"   {csv_file} ({csv_size:.1f} KB)")

    print(f"\nSummary Statistics:")
    print(f"   Total instances: {len(df)}")

    dfg_avg_valid = df[df['dfg_ged_avg'] != -1]['dfg_ged_avg']
    if len(dfg_avg_valid) > 0:
        print(f"   Average DFG-GED: {dfg_avg_valid.mean():.2f} ({len(dfg_avg_valid)} valid)")
        print(f"   Max DFG-GED: {df[df['dfg_ged_max'] != -1]['dfg_ged_max'].max():.2f}")
    else:
        print(f"   Average DFG-GED: N/A")

    print(f"   Average scope size: {df['scope_size'].mean():.1f} files")
    print(f"   Average analysis time: {df['analysis_time'].mean():.1f}s")

    print(f"\nMerge complete!")
    print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description='Merge V3 analysis results from batch output files'
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--dataset', choices=['verified', 'full', 'pro'],
                       help='Dataset type (determines output directory)')
    group.add_argument('--output-dir',
                       help='Output directory containing result files')
    args = parser.parse_args()

    if args.output_dir:
        output_dir = args.output_dir
    elif args.dataset:
        output_dir = f'outputs_{args.dataset}'
    else:
        parser.print_help()
        print("\nError: specify --dataset or --output-dir")
        exit(1)

    if not Path(output_dir).exists():
        print(f"Error: directory not found: {output_dir}")
        exit(1)

    merge_results(output_dir)


if __name__ == '__main__':
    main()
