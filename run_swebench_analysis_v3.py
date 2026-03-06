#!/usr/bin/env python3
"""
V3 Pipeline - Analyze SWE-bench Dataset with Module-Level Scope
Measures bug → patch transformation complexity using 13 metrics with full module context.
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import traceback

sys.path.insert(0, str(Path(__file__).parent))

from production_analyzer_v3 import ProductionBugAnalyzerV3
from swebench_loader import SWEBenchLoader


class SWEBenchPipelineV3:
    """
    V3 Pipeline with module-level scope analysis.

    Key differences from V2:
    - Uses ProductionBugAnalyzerV3 (module-level scope)
    - Configurable scope depth and top-k parameters
    - Enhanced metrics with scope information
    - Analyzes entire module context, not just changed files
    """

    def __init__(self,
                 dataset_dir: str = "datasets",
                 output_dir: str = "outputs",
                 repo_cache_dir: str = "repo_cache",
                 use_hybrid_ged: bool = True,
                 scope_depth: int = 3,
                 top_k_secondary: int = 5,
                 dataset_type: str = "verified"):
        """
        Initialize V3 pipeline.

        Args:
            dataset_dir: Directory containing SWE-bench dataset
            output_dir: Directory for output files
            repo_cache_dir: Directory for caching repositories
            use_hybrid_ged: Use hybrid GED calculator
            scope_depth: Module depth for primary files (1-5, default: 3)
            top_k_secondary: Number of secondary module files (1-20, default: 5)
            dataset_type: Dataset type - "verified" or "full" (default: "verified")
        """
        self.dataset_dir = Path(dataset_dir)
        self.output_dir = Path(output_dir)
        self.repo_cache_dir = Path(repo_cache_dir)
        self.dataset_type = dataset_type

        # Create directories
        self.dataset_dir.mkdir(exist_ok=True, parents=True)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.repo_cache_dir.mkdir(exist_ok=True, parents=True)

        # Initialize components with V3 analyzer
        self.loader = SWEBenchLoader(
            dataset_dir=str(self.dataset_dir),
            dataset_type=dataset_type
        )
        self.analyzer = ProductionBugAnalyzerV3(
            repo_cache_dir=str(self.repo_cache_dir),
            use_hybrid_ged=use_hybrid_ged,
            scope_depth=scope_depth,
            top_k_secondary=top_k_secondary
        )

        # Results tracking
        self.results = []
        self.errors = []

        # Store config
        self.scope_depth = scope_depth
        self.top_k_secondary = top_k_secondary

    def run_analysis(self,
                    limit: Optional[int] = None,
                    start_from: int = 0,
                    use_mock: bool = False) -> Dict[str, Any]:
        """
        Run complete V3 analysis on SWE-bench dataset.

        Args:
            limit: Maximum number of instances to process
            start_from: Start from this instance index (for resuming)
            use_mock: Use mock data instead of real dataset

        Returns:
            Summary statistics
        """
        dataset_display_name = {
            "verified": "SWE-bench Verified",
            "full": "SWE-bench Full",
            "pro": "SWE-bench Pro",
        }.get(self.dataset_type, self.dataset_type)

        print("\n" + "="*70)
        print("SWE-BENCH V3 ANALYSIS PIPELINE")
        print("Module-Level Scope Analysis")
        print("="*70)
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Dataset: {dataset_display_name}")
        print(f"📁 Dataset dir: {self.dataset_dir}")
        print(f"📁 Output dir: {self.output_dir}")
        print(f"📁 Repo cache: {self.repo_cache_dir}")
        print(f"🔧 Hybrid GED: {self.analyzer.use_hybrid_ged}")
        print(f"🔧 Scope depth: {self.scope_depth}")
        print(f"🔧 Top-k secondary: {self.top_k_secondary}")
        print("="*70)

        # Load dataset
        try:
            if use_mock:
                print("\n🧪 Using mock dataset...")
                dataset = self._create_mock_dataset(n=10)
            else:
                print(f"\n📥 Loading {dataset_display_name} dataset...")
                dataset = self.loader.load_dataset()
        except Exception as e:
            print(f"\n❌ Failed to load dataset: {e}")
            print("💡 Falling back to mock dataset...")
            dataset = self._create_mock_dataset(n=10)

        # Apply filters
        if start_from > 0:
            dataset = dataset[start_from:]
            print(f"⏭️  Starting from instance {start_from}")

        if limit:
            dataset = dataset[:limit]
            print(f"🔢 Limiting to {limit} instances")

        print(f"\n📊 Total instances to analyze: {len(dataset)}")

        # Set file prefix: batch{id}_{start}_{end}
        batch_id = os.environ.get('BATCH_ID', '0')
        actual_end = start_from + len(dataset) - 1
        self.file_prefix = f"batch{batch_id}_{start_from}_{actual_end}"
        print(f"📝 File prefix: {self.file_prefix}")

        # Analyze each instance
        start_time = time.time()

        for i, instance in enumerate(dataset, start=1):
            instance_id = instance.get('instance_id', f'instance_{i}')

            print(f"\n{'─'*70}")
            print(f"Processing {i}/{len(dataset)}: {instance_id}")
            print(f"{'─'*70}")

            try:
                result = self.analyzer.analyze_instance(instance, instance_id)
                self.results.append(result)

                # Check for errors
                if result.get('errors'):
                    self.errors.append({
                        'instance_id': instance_id,
                        'errors': result['errors']
                    })
                    print(f"⚠️  Instance had errors: {result['errors'][:2]}")

            except Exception as e:
                error_msg = f"Failed to analyze {instance_id}: {str(e)}"
                print(f"❌ {error_msg}")
                self.errors.append({
                    'instance_id': instance_id,
                    'errors': [error_msg, traceback.format_exc()]
                })

            # Save progress every 5 instances
            if i % 5 == 0:
                self._save_progress(i)

        # Final save
        elapsed = time.time() - start_time
        summary = self._save_results(elapsed)

        return summary

    def _save_progress(self, count: int):
        """Save intermediate results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = getattr(self, 'file_prefix', f"batch0_0_0")
        progress_file = self.output_dir / f"{prefix}_progress_{count}_{timestamp}.json"

        with open(progress_file, 'w') as f:
            json.dump({
                'count': count,
                'dataset_type': self.dataset_type,
                'results': self.results,
                'errors': self.errors
            }, f, indent=2, default=str)

        print(f"💾 Progress saved: {progress_file.name}")

    def _save_results(self, elapsed: float) -> Dict[str, Any]:
        """Save final results and generate summary"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = getattr(self, 'file_prefix', f"batch0_0_0")

        # Save detailed JSON
        json_file = self.output_dir / f"{prefix}_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump({
                'pipeline_version': 'v3',
                'dataset_type': self.dataset_type,
                'scope_config': {
                    'depth': self.scope_depth,
                    'top_k_secondary': self.top_k_secondary
                },
                'total_analyzed': len(self.results),
                'total_errors': len(self.errors),
                'elapsed_time': elapsed,
                'results': self.results,
                'errors': self.errors
            }, f, indent=2, default=str)

        print(f"💾 Results saved: {json_file}")

        # Save CSV summary
        csv_file = self.output_dir / f"{prefix}_summary_{timestamp}.csv"
        self._save_csv_summary(csv_file)
        print(f"💾 CSV summary saved: {csv_file}")

        # Generate summary
        summary = {
            'output_file': str(json_file),
            'csv_file': str(csv_file),
            'total_analyzed': len(self.results),
            'total_errors': len(self.errors),
            'elapsed_time': elapsed,
            'avg_time_per_instance': elapsed / len(self.results) if self.results else 0
        }

        # Print summary
        print("\n" + "="*70)
        print("ANALYSIS COMPLETE")
        print("="*70)
        print(f"✅ Total analyzed: {summary['total_analyzed']}")
        print(f"❌ Total errors: {summary['total_errors']}")
        print(f"⏱️  Total time: {elapsed:.2f}s")
        print(f"⏱️  Avg per instance: {summary['avg_time_per_instance']:.2f}s")
        print(f"📁 Results: {json_file}")
        print(f"📁 CSV: {csv_file}")
        print("="*70)

        return summary

    def _save_csv_summary(self, csv_file: Path):
        """Save results as CSV for easy analysis"""
        import csv

        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'instance_id', 'repo_name', 'num_changed_files',
                'scope_size', 'primary_files', 'secondary_files', 'direct_imports',
                'num_files_analyzed', 'num_context_files',
                'dfg_ged_sum', 'dfg_ged_avg', 'dfg_ged_max',
                'ast_ged_sum', 'ast_ged_avg', 'ast_ged_max',
                'cfg_ged_sum', 'cfg_ged_avg', 'cfg_ged_max',
                'lines_added', 'lines_deleted', 'hunks_count',
                'analysis_time', 'has_errors'
            ])

            # Data rows
            for result in self.results:
                instance_id = result.get('instance_id', 'unknown')
                repo_name = result.get('repo_name', 'unknown')
                num_changed = result.get('num_changed_files', 0)

                # Scope info
                scope = result.get('scope', {})
                scope_size = scope.get('total_size', 0)
                primary_size = len(scope.get('primary', []))
                secondary_size = len(scope.get('secondary', []))
                imports_size = len(scope.get('direct_imports', []))

                # Metrics
                metrics = result.get('metrics', {})
                num_analyzed = metrics.get('num_files_analyzed', 0)
                num_context = metrics.get('num_context_files', 0)

                # Extract key GED metrics from overall metrics
                overall = metrics.get('overall_metrics', {})
                summary = overall.get('summary', {})

                # DFG-GED
                dfg_ged = summary.get('graph', {}).get('DFG_GED', {})
                dfg_sum = dfg_ged.get('sum', 0)
                dfg_avg = dfg_ged.get('avg', 0)
                dfg_max = dfg_ged.get('max', 0)

                # AST-GED
                ast_ged = summary.get('ast', {}).get('AST_GED', {})
                ast_sum = ast_ged.get('sum', 0)
                ast_avg = ast_ged.get('avg', 0)
                ast_max = ast_ged.get('max', 0)

                # CFG-GED
                cfg_ged = summary.get('graph', {}).get('CFG_GED', {})
                cfg_sum = cfg_ged.get('sum', 0)
                cfg_avg = cfg_ged.get('avg', 0)
                cfg_max = cfg_ged.get('max', 0)

                # Lines Added, Lines Deleted, Hunks Count (sum across all analyzed files)
                basic_summary = overall.get('summary', {}).get('basic', {})
                lines_added = basic_summary.get('Lines_Added', {}).get('sum', 0)
                lines_deleted = basic_summary.get('Lines_Deleted', {}).get('sum', 0)
                hunks_count = basic_summary.get('Hunks_Count', {}).get('sum', 0)

                analysis_time = result.get('analysis_time', 0)
                has_errors = len(result.get('errors', [])) > 0

                writer.writerow([
                    instance_id, repo_name, num_changed,
                    scope_size, primary_size, secondary_size, imports_size,
                    num_analyzed, num_context,
                    dfg_sum, dfg_avg, dfg_max,
                    ast_sum, ast_avg, ast_max,
                    cfg_sum, cfg_avg, cfg_max,
                    lines_added, lines_deleted, hunks_count,
                    analysis_time, has_errors
                ])

    def _create_mock_dataset(self, n: int = 10) -> List[Dict[str, Any]]:
        """Create mock dataset for testing"""
        mock_instances = []

        for i in range(n):
            mock_instances.append({
                'instance_id': f'mock-{i:03d}',
                'repo': 'https://github.com/octocat/Hello-World',
                'base_commit': 'master',
                'patch': f"""
diff --git a/test_{i}.py b/test_{i}.py
index 1234567..abcdefg 100644
--- a/test_{i}.py
+++ b/test_{i}.py
@@ -1,3 +1,4 @@
+# Modified line {i}
 def test_{i}():
     pass
""",
                'problem_statement': f'Mock problem statement {i}'
            })

        return mock_instances


def main():
    """Main entry point"""
    import argparse
    from swebench_loader import REGISTRY

    dataset_choices = list(REGISTRY.keys())
    dataset_help = ', '.join(
        f"{alias} ({info['total_instances']} instances)"
        for alias, info in REGISTRY.items()
    )

    parser = argparse.ArgumentParser(
        description='Analyze a benchmark dataset with V3 (module-level scope analysis)'
    )
    parser.add_argument('--dataset', type=str, default='verified',
                       choices=dataset_choices,
                       help=f'Dataset to analyze. Available: {dataset_help} (default: verified)')
    parser.add_argument('--limit', type=int, help='Limit number of instances')
    parser.add_argument('--start-from', type=int, default=0, help='Start from instance index')
    parser.add_argument('--mock', action='store_true', help='Use mock data')
    parser.add_argument('--no-hybrid', action='store_true', help='Disable hybrid GED')
    parser.add_argument('--repo-cache', default='repo_cache', help='Repository cache directory')
    parser.add_argument('--output-dir', default='outputs', help='Output directory for results')
    parser.add_argument('--scope-depth', type=int, default=3,
                       help='Module depth for primary files (1-5, default: 3)')
    parser.add_argument('--top-k', type=int, default=5,
                       help='Number of secondary module files (1-20, default: 5)')

    args = parser.parse_args()

    # Validate parameters
    if args.scope_depth < 1 or args.scope_depth > 5:
        print("⚠️  Warning: scope-depth should be 1-5, using default 3")
        args.scope_depth = 3

    if args.top_k < 1 or args.top_k > 20:
        print("⚠️  Warning: top-k should be 1-20, using default 5")
        args.top_k = 5

    # Create pipeline
    pipeline = SWEBenchPipelineV3(
        output_dir=args.output_dir,
        repo_cache_dir=args.repo_cache,
        use_hybrid_ged=not args.no_hybrid,
        scope_depth=args.scope_depth,
        top_k_secondary=args.top_k,
        dataset_type=args.dataset
    )

    # Run analysis
    summary = pipeline.run_analysis(
        limit=args.limit,
        start_from=args.start_from,
        use_mock=args.mock
    )

    print("\n✅ V3 Pipeline complete!")
    print(f"📁 Results: {summary['output_file']}")


if __name__ == '__main__':
    main()
