#!/usr/bin/env python3
"""
Merge V3 Analysis Results
Combines multiple JSON result files into one merged file
"""

import json
import glob
from datetime import datetime
from pathlib import Path
import pandas as pd


def merge_results():
    """Merge all V3 result files"""
    
    print("="*70)
    print("MERGING V3 ANALYSIS RESULTS")
    print("="*70)
    
    # Find all result files (both patterns for flexibility)
    result_files = sorted(set(
        glob.glob('outputs/v3_full_*.json') + 
        glob.glob('outputs/v3_results_*.json')
    ))
    print(f"\n📂 Found {len(result_files)} result files:")
    for f in result_files:
        size = Path(f).stat().st_size / (1024*1024)  # MB
        print(f"   - {f} ({size:.1f} MB)")
    
    if not result_files:
        print("\n❌ No result files found!")
        print("   Looking for: outputs/v3_full_*.json or outputs/v3_results_*.json")
        return
    
    # Merge all results
    all_results = []
    all_errors = []
    
    print(f"\n📥 Merging results...")
    for file in result_files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                all_results.extend(data.get('results', []))
                all_errors.extend(data.get('errors', []))
        except Exception as e:
            print(f"   ⚠️  Error reading {file}: {e}")
    
    print(f"   - Total results loaded: {len(all_results)}")
    
    # Remove duplicates (by instance_id)
    seen = set()
    unique_results = []
    duplicates = 0
    
    for r in all_results:
        iid = r.get('instance_id')
        if iid and iid not in seen:
            seen.add(iid)
            unique_results.append(r)
        else:
            duplicates += 1
    
    print(f"   - Unique instances: {len(unique_results)}")
    if duplicates > 0:
        print(f"   - Duplicates removed: {duplicates}")
    
    # Count successful vs errors
    successful = [r for r in unique_results if not r.get('errors')]
    with_errors = [r for r in unique_results if r.get('errors')]
    
    print(f"\n📊 Statistics:")
    print(f"   ✅ Successful: {len(successful)}")
    print(f"   ⚠️  With errors: {len(with_errors)}")
    print(f"   ❌ Failed completely: {len(all_errors)}")
    
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
    
    json_file = f'outputs/v3_merged_{timestamp}.json'
    with open(json_file, 'w') as f:
        json.dump(merged, f, indent=2)
    
    json_size = Path(json_file).stat().st_size / (1024*1024)
    print(f"\n💾 Merged JSON saved:")
    print(f"   {json_file} ({json_size:.1f} MB)")
    
    # Create merged CSV
    print(f"\n📊 Creating merged CSV...")
    
    csv_rows = []
    for result in unique_results:
        row = {
            'instance_id': result.get('instance_id'),
            'repo_name': result.get('repo_name'),
            'analysis_time': result.get('analysis_time', 0),
            'has_errors': bool(result.get('errors'))
        }
        
        # Extract scope info
        scope = result.get('scope', {})
        row['scope_size'] = scope.get('total_size', 0)
        row['primary_files'] = len(scope.get('primary', []))
        row['secondary_files'] = len(scope.get('secondary', []))
        row['direct_imports'] = len(scope.get('direct_imports', []))
        
        # Extract metrics from the actual structure
        metrics = result.get('metrics', {})
        overall = metrics.get('overall_metrics', {})
        summary = overall.get('summary', {})
        
        # DFG-GED
        graph_metrics = summary.get('graph', {})
        dfg_ged = graph_metrics.get('DFG_GED', {})
        row['dfg_ged_sum'] = dfg_ged.get('sum', -1)
        row['dfg_ged_avg'] = dfg_ged.get('avg', -1)
        row['dfg_ged_max'] = dfg_ged.get('max', -1)
        
        # AST-GED
        ast_metrics = summary.get('ast', {})
        ast_ged = ast_metrics.get('AST_GED', {})
        row['ast_ged_sum'] = ast_ged.get('sum', -1)
        row['ast_ged_avg'] = ast_ged.get('avg', -1)
        row['ast_ged_max'] = ast_ged.get('max', -1)
        
        # CFG-GED
        cfg_ged = graph_metrics.get('CFG_GED', {})
        row['cfg_ged_sum'] = cfg_ged.get('sum', -1)
        row['cfg_ged_avg'] = cfg_ged.get('avg', -1)
        row['cfg_ged_max'] = cfg_ged.get('max', -1)
        
        csv_rows.append(row)
    
    df = pd.DataFrame(csv_rows)
    csv_file = f'outputs/v3_merged_summary_{timestamp}.csv'
    df.to_csv(csv_file, index=False)
    
    csv_size = Path(csv_file).stat().st_size / 1024
    print(f"   {csv_file} ({csv_size:.1f} KB)")
    
    # Summary statistics
    print(f"\n📈 Summary Statistics:")
    print(f"   Total instances: {len(df)}")
    print(f"   Average DFG-GED: {df['dfg_ged_avg'].mean():.2f}")
    print(f"   Max DFG-GED: {df['dfg_ged_max'].max():.2f}")
    print(f"   Average scope size: {df['scope_size'].mean():.1f} files")
    print(f"   Average analysis time: {df['analysis_time'].mean():.1f}s")
    
    print(f"\n✅ Merge complete!")
    print("="*70)


if __name__ == '__main__':
    merge_results()
