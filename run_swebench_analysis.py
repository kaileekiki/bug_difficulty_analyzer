#!/usr/bin/env python3
"""
Final Pipeline - Analyze SWE-bench Verified Dataset

Measures bug → patch transformation complexity using 13 metrics.
This measures how much the code changes from buggy state to fixed state.
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import traceback

sys.path.insert(0, str(Path(__file__).parent))

from production_analyzer import ProductionBugAnalyzer
from swebench_loader import SWEBenchLoader


class SWEBenchPipeline:
    """
    Complete pipeline for analyzing SWE-bench dataset.
    
    Process:
    1. Load SWE-bench Verified dataset
    2. For each instance:
       - Extract patch (bug → fix transformation)
       - Compute 13 complexity metrics
       - Measure how much code structure changed
    3. Save results with progress tracking
    """
    
    def __init__(self, 
                 dataset_dir: str = "datasets",
                 output_dir: str = "outputs",
                 use_hybrid_ged: bool = True):
        self.dataset_dir = Path(dataset_dir)
        self.output_dir = Path(output_dir)
        
        # Create directories
        self.dataset_dir.mkdir(exist_ok=True, parents=True)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize components
        self.loader = SWEBenchLoader(dataset_dir=str(self.dataset_dir))
        self.analyzer = ProductionBugAnalyzer(use_hybrid_ged=use_hybrid_ged)
        
        # Results tracking
        self.results = []
        self.errors = []
    
    def run_analysis(self, 
                    limit: Optional[int] = None,
                    start_from: int = 0,
                    use_mock: bool = False) -> Dict[str, Any]:
        """
        Run complete analysis on SWE-bench dataset.
        
        Args:
            limit: Maximum number of instances to process
            start_from: Start from this instance index (for resuming)
            use_mock: Use mock data instead of real dataset
            
        Returns:
            Summary statistics
        """
        print("\n" + "="*70)
        print("SWE-BENCH DIFFICULTY ANALYSIS PIPELINE")
        print("="*70)
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Dataset dir: {self.dataset_dir}")
        print(f"📁 Output dir: {self.output_dir}")
        print(f"🔧 Hybrid GED: {self.analyzer.use_hybrid_ged}")
        print("="*70)
        
        # Load dataset
        try:
            if use_mock:
                print("\n🧪 Using mock dataset...")
                dataset = self.loader.create_mock_dataset(n=10)
            else:
                print("\n📥 Loading SWE-bench Verified dataset...")
                dataset = self.loader.load_dataset()
        except Exception as e:
            print(f"\n❌ Failed to load dataset: {e}")
            print("💡 Falling back to mock dataset...")
            dataset = self.loader.create_mock_dataset(n=10)
        
        # Apply filters
        if start_from > 0:
            dataset = dataset[start_from:]
            print(f"⏭️  Starting from instance {start_from}")
        
        if limit:
            dataset = dataset[:limit]
            print(f"🔢 Processing {len(dataset)} instances (limited)")
        else:
            print(f"🔢 Processing all {len(dataset)} instances")
        
        # Process instances
        print("\n" + "="*70)
        print("PROCESSING INSTANCES")
        print("="*70)
        
        start_time = time.time()
        
        for i, instance in enumerate(dataset, start=start_from + 1):
            try:
                result = self._process_instance(instance, i, len(dataset) + start_from)
                self.results.append(result)
                
                # Save progress periodically
                if i % 10 == 0:
                    self._save_progress()
            
            except Exception as e:
                error_info = {
                    'instance_id': instance.get('instance_id', f'unknown_{i}'),
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
                self.errors.append(error_info)
                print(f"  ❌ Error: {e}")
        
        elapsed = time.time() - start_time
        
        # Final save
        final_file = self._save_final_results()
        
        # Print summary
        self._print_summary(elapsed)
        
        return {
            'total_processed': len(self.results),
            'total_errors': len(self.errors),
            'elapsed_time': elapsed,
            'output_file': str(final_file)
        }
    
    def _process_instance(self, instance: Dict[str, Any], 
                         index: int, total: int) -> Dict[str, Any]:
        """Process single instance"""
        instance_id = instance.get('instance_id', f'unknown_{index}')
        
        print(f"\n[{index}/{total}] {instance_id}")
        print("-" * 70)
        
        # Extract patch
        patch = instance.get('patch', '')
        if not patch:
            print("  ⚠️  No patch found, skipping")
            return {
                'instance_id': instance_id,
                'status': 'skipped',
                'reason': 'no_patch'
            }
        
        print(f"  📝 Patch size: {len(patch)} characters")
        
        # Analyze
        analysis_start = time.time()
        result = self.analyzer.analyze_patch(patch, instance_id)
        analysis_time = time.time() - analysis_start
        
        print(f"  ⏱️  Analysis time: {analysis_time:.2f}s")
        
        # Add instance metadata
        result['repo'] = instance.get('repo', 'unknown')
        result['base_commit'] = instance.get('base_commit', 'unknown')
        result['problem_statement'] = instance.get('problem_statement', '')[:200]  # First 200 chars
        
        # Show key metrics
        if 'metrics' in result and 'aggregated' in result['metrics']:
            agg = result['metrics']['aggregated']
            
            # DFG-GED (Main Hypothesis)
            if 'graph' in agg and 'DFG_GED' in agg['graph']:
                dfg = agg['graph']['DFG_GED'][0]
                print(f"  ⭐ DFG-GED: {dfg.get('dfg_ged', 'N/A'):.2f}")
            
            # LOC
            if 'basic' in agg and 'LOC' in agg['basic']:
                loc = agg['basic']['LOC'][0]
                print(f"  📏 LOC: +{loc.get('added', 0)}/-{loc.get('deleted', 0)}")
        
        print("  ✅ Complete")
        
        return result
    
    def _save_progress(self):
        """Save current progress"""
        progress_file = self.output_dir / f"progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(progress_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'processed': len(self.results),
                'errors': len(self.errors),
                'results': self.results[-10:]  # Last 10 results
            }, f, indent=2)
        
        print(f"\n💾 Progress saved to: {progress_file}")
    
    def _save_final_results(self) -> Path:
        """Save final complete results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = self.output_dir / f"swebench_analysis_{timestamp}.json"
        
        complete_results = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_instances': len(self.results),
                'total_errors': len(self.errors),
                'hybrid_ged': self.analyzer.use_hybrid_ged
            },
            'results': self.results,
            'errors': self.errors
        }
        
        with open(results_file, 'w') as f:
            json.dump(complete_results, f, indent=2)
        
        print(f"\n💾 Final results saved to: {results_file}")
        
        # Also save summary CSV
        self._save_summary_csv(results_file.stem)
        
        return results_file
    
    def _save_summary_csv(self, base_name: str):
        """Save summary in CSV format for easy analysis"""
        import csv
        
        csv_file = self.output_dir / f"{base_name}_summary.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'instance_id', 'repo', 'analysis_time',
                'ast_ged', 'dfg_ged', 'pdg_ged', 'cfg_ged', 'cpg_ged', 'callgraph_ged',
                'loc_added', 'loc_deleted', 'token_distance',
                'cyclomatic_delta', 'halstead_delta', 'scope_changes',
                'type_changes', 'exception_changes'
            ])
            
            # Data
            for result in self.results:
                if result.get('status') == 'skipped':
                    continue
                
                row = [
                    result.get('instance_id', ''),
                    result.get('repo', ''),
                    result.get('analysis_time', 0)
                ]
                
                # Extract metrics
                metrics = result.get('metrics', {}).get('aggregated', {})
                
                # AST-GED
                ast_ged = metrics.get('ast', {}).get('AST_GED', [{}])[0].get('ast_ged', -1)
                row.append(ast_ged)
                
                # Graph GEDs
                graph = metrics.get('graph', {})
                row.append(graph.get('DFG_GED', [{}])[0].get('dfg_ged', -1))
                row.append(graph.get('PDG_GED', [{}])[0].get('pdg_ged', -1))
                row.append(graph.get('CFG_GED', [{}])[0].get('cfg_ged', -1))
                row.append(graph.get('CPG_GED', [{}])[0].get('cpg_ged', -1))
                row.append(graph.get('Call_Graph_GED', [{}])[0].get('callgraph_ged', -1))
                
                # Basic metrics
                basic = metrics.get('basic', {})
                loc = basic.get('LOC', [{}])[0]
                row.append(loc.get('added', -1))
                row.append(loc.get('deleted', -1))
                row.append(basic.get('Token_Edit_Distance', [{}])[0].get('token_distance', -1))
                row.append(basic.get('Cyclomatic_Complexity', [{}])[0].get('delta_total', -1))
                row.append(basic.get('Halstead_Difficulty', [{}])[0].get('delta_difficulty', -1))
                row.append(basic.get('Variable_Scope', [{}])[0].get('total_scope_changes', -1))
                
                # AST metrics
                ast_metrics = metrics.get('ast', {})
                row.append(ast_metrics.get('Type_Changes', [{}])[0].get('total_type_changes', -1))
                row.append(ast_metrics.get('Exception_Handling', [{}])[0].get('total_exception_changes', -1))
                
                writer.writerow(row)
        
        print(f"📊 Summary CSV saved to: {csv_file}")
    
    def _print_summary(self, elapsed: float):
        """Print analysis summary"""
        print("\n" + "="*70)
        print("ANALYSIS SUMMARY")
        print("="*70)
        print(f"✅ Successfully processed: {len(self.results)}")
        print(f"❌ Errors: {len(self.errors)}")
        print(f"⏱️  Total time: {elapsed/60:.1f} minutes")
        print(f"⚡ Average time per instance: {elapsed/max(len(self.results), 1):.2f}s")
        print("="*70)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze SWE-bench dataset')
    parser.add_argument('--limit', type=int, help='Limit number of instances')
    parser.add_argument('--start-from', type=int, default=0, help='Start from instance index')
    parser.add_argument('--mock', action='store_true', help='Use mock data')
    parser.add_argument('--no-hybrid', action='store_true', help='Disable hybrid GED')
    
    args = parser.parse_args()
    
    # Create pipeline
    pipeline = SWEBenchPipeline(
        use_hybrid_ged=not args.no_hybrid
    )
    
    # Run analysis
    summary = pipeline.run_analysis(
        limit=args.limit,
        start_from=args.start_from,
        use_mock=args.mock
    )
    
    print("\n✅ Pipeline complete!")
    print(f"📁 Results: {summary['output_file']}")


if __name__ == '__main__':
    main()
