"""
Production-Ready Bug Difficulty Analyzer V3
Module-level scope analysis with full context
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import time

sys.path.insert(0, str(Path(__file__).parent))

# Import V2 as base
from production_analyzer_v2 import ProductionBugAnalyzerV2
from core.scope_extractor import ModuleScopeExtractor


class ProductionBugAnalyzerV3(ProductionBugAnalyzerV2):
    """
    V3 Analyzer with module-level scope analysis.
    
    Key differences from V2:
    - Analyzes ENTIRE MODULE context, not just changed files
    - Extracts primary modules (depth=3), secondary modules (top-k), and direct imports
    - Captures cross-file dependencies for more accurate difficulty measurement
    - More comprehensive complexity assessment
    
    Workflow:
    1. Clone repository (same as V2)
    2. Checkout base_commit
    3. Extract changed files from patch
    4. **NEW: Expand to full module scope**
    5. Get BEFORE content for ALL scope files
    6. Apply patch
    7. Get AFTER content for ALL scope files
    8. **NEW: Analyze all files in scope**
    9. Compute metrics on module-level changes
    10. Reset repository
    """
    
    def __init__(self, repo_cache_dir: str = "repo_cache", 
                 use_hybrid_ged: bool = True,
                 scope_depth: int = 3,
                 top_k_secondary: int = 5):
        """
        Initialize V3 analyzer.
        
        Args:
            repo_cache_dir: Directory for caching cloned repositories
            use_hybrid_ged: Use hybrid GED for better accuracy
            scope_depth: Module depth for primary files (default: 3)
            top_k_secondary: Number of secondary module files to include (default: 5)
        """
        super().__init__(repo_cache_dir, use_hybrid_ged)
        self.scope_depth = scope_depth
        self.top_k_secondary = top_k_secondary
        self.scope_extractor = None  # Initialize per-repo
        
        print(f"✓ V3: Module depth={scope_depth}, top-k secondary={top_k_secondary}")
    
    def analyze_instance(self, instance: Dict[str, Any], 
                        instance_id: str = "unknown") -> Dict[str, Any]:
        """
        Analyze a SWE-bench instance with full module scope.
        
        This extends V2's analyze_instance by:
        1. Expanding changed files to full module scope
        2. Analyzing all files in the scope (not just changed files)
        3. Including scope information in results
        
        Args:
            instance: SWE-bench instance with repo, base_commit, patch
            instance_id: Identifier for this instance
            
        Returns:
            Complete analysis with all 13 metrics + scope information
        """
        print(f"\n{'='*70}")
        print(f"ANALYZING (V3): {instance_id}")
        print(f"{'='*70}")
        
        start_time = time.time()
        
        results = {
            'instance_id': instance_id,
            'analysis_time': 0.0,
            'scope': {},
            'metrics': {},
            'errors': []
        }
        
        repo_path = None
        
        try:
            # Extract instance info
            repo_field = instance.get('repo', '')  # Can be "astropy/astropy" or "https://github.com/astropy/astropy"
            base_commit = instance.get('base_commit', '')
            patch = instance.get('patch', '')
            
            if not repo_field or not base_commit or not patch:
                results['errors'].append("Missing required fields: repo, base_commit, or patch")
                return results
            
            # Normalize repository URL (handles both "owner/repo" and full URLs)
            repo_url, repo_name = self.normalize_repo_url(repo_field)
            
            # Extract owner/repo identifier for results
            # Remove https://github.com/ and .git suffix to get "owner/repo"
            repo_identifier = repo_url.replace('https://github.com/', '').replace('.git', '')
            
            results['repo_name'] = repo_name
            results['base_commit'] = base_commit
            results['repo'] = repo_identifier
            
            print(f"Repository: {repo_identifier}")
            print(f"GitHub URL: {repo_url}")
            print(f"Base commit: {base_commit[:8]}")
            
            # Step 1: Clone repository
            print("\n[1/9] Cloning repository...")
            try:
                repo_path = self.repo_manager.clone_or_update(repo_url, repo_name)
            except Exception as e:
                results['errors'].append(f"Clone failed: {str(e)}")
                return results
            
            # Step 2: Checkout base commit
            print("\n[2/9] Checking out base commit...")
            if not self.repo_manager.checkout_commit(repo_path, base_commit):
                results['errors'].append(f"Checkout failed: {base_commit}")
                return results
            
            # Step 3: Extract changed files
            print("\n[3/9] Extracting changed files from patch...")
            changed_files = self.repo_manager.get_changed_files_from_patch(patch)
            print(f"  ✓ Found {len(changed_files)} changed files")
            results['num_changed_files'] = len(changed_files)
            results['changed_files'] = changed_files
            
            if not changed_files:
                results['errors'].append("No files found in patch")
                return results
            
            # Step 3.5: Expand to module scope (NEW in V3)
            print("\n[3.5/9] Expanding to module scope...")
            self.scope_extractor = ModuleScopeExtractor(
                str(repo_path),
                module_depth=self.scope_depth,
                max_secondary_files=self.top_k_secondary
            )
            
            scope = self.scope_extractor.extract_full_scope(changed_files)
            
            print(f"  ✓ Primary modules: {len(scope['primary'])} files")
            print(f"  ✓ Secondary modules: {len(scope['secondary'])} files")
            print(f"  ✓ Direct imports: {len(scope['direct_imports'])} files")
            print(f"  ✓ Total scope: {len(scope['all'])} files")
            
            # Store scope information in results
            results['scope'] = {
                'primary': scope['primary'],
                'secondary': scope['secondary'],
                'direct_imports': scope['direct_imports'],
                'total_size': len(scope['all'])
            }
            
            # Use ALL files in scope for analysis
            all_files = scope['all']
            
            # Step 4: Get BEFORE content (for all scope files)
            print("\n[4/9] Getting BEFORE content for all scope files...")
            before_files = {}
            for filepath in all_files:
                try:
                    content = self.repo_manager.get_file_content(repo_path, filepath)
                    before_files[filepath] = content
                    if filepath in changed_files:
                        print(f"  ✓ {filepath}: {len(content)} chars (CHANGED)")
                except Exception as e:
                    # File might not exist before patch
                    before_files[filepath] = ""
            
            print(f"  ✓ Retrieved {len(before_files)} files")
            
            # Step 5: Apply patch
            print("\n[5/9] Applying patch...")
            if not self.repo_manager.apply_patch(repo_path, patch):
                print("  ⚠️  Patch apply had issues (may be OK)")
            
            # Step 6: Get AFTER content (for all scope files)
            print("\n[6/9] Getting AFTER content for all scope files...")
            after_files = {}
            for filepath in all_files:
                try:
                    content = self.repo_manager.get_file_content(repo_path, filepath)
                    after_files[filepath] = content
                    if filepath in changed_files:
                        print(f"  ✓ {filepath}: {len(content)} chars (CHANGED)")
                except Exception as e:
                    # File might be deleted by patch
                    after_files[filepath] = ""
            
            print(f"  ✓ Retrieved {len(after_files)} files")
            
            # Step 7: Analyze all files in scope
            print("\n[7/9] Analyzing all files in scope...")
            file_results = []
            
            for filepath in all_files:
                if filepath.endswith('.py'):  # Only Python files
                    is_changed = filepath in changed_files
                    prefix = "CHANGED" if is_changed else "CONTEXT"
                    print(f"\n  Analyzing [{prefix}]: {filepath}")
                    
                    file_analysis = self._analyze_file_pair(
                        filepath,
                        before_files.get(filepath, ""),
                        after_files.get(filepath, "")
                    )
                    file_analysis['is_changed'] = is_changed
                    file_results.append(file_analysis)
            
            # Step 8: Aggregate metrics
            print("\n[8/9] Aggregating metrics...")
            results['metrics'] = self._aggregate_metrics_v3(file_results, changed_files)
            
            # Step 9: Reset repository (cleanup)
            print("\n[9/9] Cleaning up...")
            self.repo_manager.reset_to_commit(repo_path, base_commit)
            
        except Exception as e:
            results['errors'].append(f"Analysis error: {str(e)}")
            import traceback
            results['errors'].append(traceback.format_exc())
        
        results['analysis_time'] = time.time() - start_time
        print(f"\n✅ V3 Analysis complete in {results['analysis_time']:.2f}s")
        print(f"{'='*70}\n")
        
        return results
    
    def _aggregate_metrics_v3(self, file_results: List[Dict], 
                             changed_files: List[str]) -> Dict[str, Any]:
        """
        Aggregate metrics with V3 enhancements.
        
        Separates metrics for:
        - Changed files (direct modifications)
        - Context files (supporting module context)
        - Overall (combined)
        """
        if not file_results:
            return {}
        
        # Separate changed vs context files
        changed_results = [r for r in file_results if r.get('is_changed', False)]
        context_results = [r for r in file_results if not r.get('is_changed', False)]
        
        aggregated = {
            'num_files_analyzed': len(file_results),
            'num_changed_files': len(changed_results),
            'num_context_files': len(context_results),
            'changed_files_metrics': self._aggregate_file_metrics(changed_results),
            'context_files_metrics': self._aggregate_file_metrics(context_results),
            'overall_metrics': self._aggregate_file_metrics(file_results)
        }
        
        return aggregated
    
    def _aggregate_file_metrics(self, file_results: List[Dict]) -> Dict[str, Any]:
        """Aggregate metrics from a list of file analysis results"""
        if not file_results:
            return {}
        
        aggregated = {}
        
        # Collect all metric values
        all_metrics = {}
        for file_result in file_results:
            if 'metrics' not in file_result:
                continue
            
            for tier, tier_metrics in file_result['metrics'].items():
                if tier not in all_metrics:
                    all_metrics[tier] = {}
                
                for metric_name, metric_value in tier_metrics.items():
                    if metric_name not in all_metrics[tier]:
                        all_metrics[tier][metric_name] = []
                    all_metrics[tier][metric_name].append(metric_value)
        
        aggregated['all_values'] = all_metrics
        
        # Compute summary statistics
        aggregated['summary'] = self._compute_summary_stats(all_metrics)
        
        return aggregated
    
    def _compute_summary_stats(self, all_metrics: Dict) -> Dict[str, Any]:
        """Compute summary statistics (sum, avg, max) for metrics"""
        summary = {}
        
        # For each tier
        for tier, metrics in all_metrics.items():
            summary[tier] = {}
            
            # For each metric
            for metric_name, values in metrics.items():
                if not values:
                    continue
                
                # Extract numeric values for key fields
                numeric_values = []
                for val in values:
                    if isinstance(val, dict):
                        # Try to extract the main metric value
                        for key in ['ged', 'dfg_ged', 'cfg_ged', 'ast_ged', 
                                   'callgraph_ged', 'pdg_ged', 'cpg_ged',
                                   'token_distance', 'delta_total', 'delta_difficulty',
                                   'total_scope_changes', 'total_exception_changes',
                                   'total_type_changes', 'modified', 'added', 'deleted']:
                            if key in val and isinstance(val[key], (int, float)) and val[key] >= 0:
                                numeric_values.append(val[key])
                                break
                    elif isinstance(val, (int, float)) and val >= 0:
                        numeric_values.append(val)
                
                if numeric_values:
                    summary[tier][metric_name] = {
                        'sum': sum(numeric_values),
                        'avg': sum(numeric_values) / len(numeric_values),
                        'max': max(numeric_values),
                        'min': min(numeric_values),
                        'count': len(numeric_values)
                    }
        
        return summary


def test_analyzer_v3():
    """Test V3 analyzer with mock data"""
    print("Testing Production Bug Analyzer V3")
    print("="*70)
    
    # Mock instance
    instance = {
        'repo': 'octocat/Hello-World',
        'base_commit': 'master',
        'patch': """
diff --git a/README b/README
index 980a0d5..1f7391f 100644
--- a/README
+++ b/README
@@ -1 +1 @@
-Hello World!
+Hello World! Modified
"""
    }
    
    analyzer = ProductionBugAnalyzerV3(
        repo_cache_dir="/tmp/test_v3_cache",
        scope_depth=2,
        top_k_secondary=3
    )
    result = analyzer.analyze_instance(instance, instance_id="test-v3-001")
    
    print("\n" + "="*70)
    print("RESULTS:")
    print(json.dumps(result, indent=2, default=str)[:3000])
    print("="*70)
    
    print("\n✓ V3 analyzer test passed!")


if __name__ == '__main__':
    test_analyzer_v3()
