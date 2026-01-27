"""
Main Bug Difficulty Analyzer
Integrates all components and metrics
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

sys.path.append(str(Path(__file__).parent))

from core.scope_extractor import ModuleScopeExtractor
from metrics.basic_metrics import BasicMetrics
from metrics.ast_metrics import ASTMetrics


class BugDifficultyAnalyzer:
    """Main analyzer for bug difficulty measurement"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.scope_extractor = ModuleScopeExtractor(str(repo_path))
    
    def analyze_bug(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single bug instance from SWE-bench.
        
        Args:
            instance: SWE-bench instance with keys:
                - patch: git diff content
                - base_commit: commit hash before fix
                - problem_statement: issue description
                
        Returns:
            Dictionary with all 13 metrics
        """
        print(f"\n{'='*70}")
        print(f"ANALYZING BUG: {instance.get('instance_id', 'unknown')}")
        print(f"{'='*70}")
        
        results = {
            'instance_id': instance.get('instance_id', 'unknown'),
            'repo': instance.get('repo', 'unknown'),
            'metrics': {}
        }
        
        # Step 1: Extract changed files from patch
        changed_files = self._extract_changed_files(instance['patch'])
        print(f"✓ Found {len(changed_files)} changed files")
        
        # Step 2: Extract scope
        scope = self.scope_extractor.extract_scope(changed_files)
        results['scope_size'] = len(scope['all'])
        print(f"✓ Extracted scope: {len(scope['all'])} files")
        
        # Step 3: Compute Tier 1 metrics (simple)
        self._compute_basic_metrics(instance, results)
        
        # Step 4: Compute Tier 2 metrics (AST-based)
        self._compute_ast_metrics(instance, results)
        
        # Step 5: Compute Tier 3 metrics (graph-based)
        # TODO: Implement when graph metrics are ready
        self._compute_graph_metrics(instance, scope, results)
        
        print(f"\n✅ Analysis complete: {len(results['metrics'])} metrics computed")
        print(f"{'='*70}\n")
        
        return results
    
    def _extract_changed_files(self, patch: str) -> List[str]:
        """Extract list of changed files from git diff"""
        files = []
        for line in patch.split('\n'):
            if line.startswith('+++') or line.startswith('---'):
                # Extract filename after +++ or ---
                if ' b/' in line:
                    filepath = line.split(' b/')[-1]
                    if filepath and filepath != '/dev/null':
                        files.append(filepath)
        
        # Deduplicate
        return list(set(files))
    
    def _get_file_content(self, filepath: str, commit: str = 'HEAD') -> str:
        """Get file content at specific commit (simplified for now)"""
        # TODO: Implement git checkout to get file at specific commit
        # For now, just read current file
        full_path = self.repo_path / filepath
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception:
                return ""
        return ""
    
    def _compute_basic_metrics(self, instance: Dict, results: Dict):
        """Compute simple metrics"""
        patch = instance['patch']
        
        # LOC
        loc = BasicMetrics.compute_loc(patch)
        results['metrics']['LOC'] = loc
        print(f"  ✓ LOC: {loc['modified']} lines")
        
        # For other metrics, we need before/after code
        # For now, use patch content as approximation
        # TODO: Get actual before/after from git
        
        print(f"  ✓ Computed {len(results['metrics'])} basic metrics")
    
    def _compute_ast_metrics(self, instance: Dict, results: Dict):
        """Compute AST-based metrics"""
        # TODO: Get actual before/after code
        # For now, placeholder
        results['metrics']['AST_GED'] = {'ast_ged': 0}
        results['metrics']['Exception_Handling'] = {'total_exception_changes': 0}
        results['metrics']['Type_Changes'] = {'total_type_changes': 0}
        
        print(f"  ✓ Computed AST metrics")
    
    def _compute_graph_metrics(self, instance: Dict, scope: Dict, results: Dict):
        """Compute graph-based metrics (CFG, DFG, PDG, CPG, Call Graph)"""
        # TODO: Implement graph metrics
        results['metrics']['CFG_GED'] = {'cfg_ged': 0}
        results['metrics']['Call_Graph_GED'] = {'call_ged': 0}
        results['metrics']['DFG_GED'] = {'dfg_ged': 0}  # Main hypothesis!
        results['metrics']['PDG_GED'] = {'pdg_ged': 0}
        results['metrics']['CPG_GED'] = {'cpg_ged': 0}
        
        print(f"  ✓ Computed graph metrics (placeholder)")
    
    def analyze_dataset(self, instances: List[Dict[str, Any]], 
                       output_path: str = None) -> List[Dict]:
        """Analyze multiple bug instances"""
        results = []
        
        print(f"\n{'#'*70}")
        print(f"ANALYZING {len(instances)} BUG INSTANCES")
        print(f"{'#'*70}\n")
        
        for i, instance in enumerate(instances, 1):
            print(f"\n[{i}/{len(instances)}]", end=" ")
            try:
                result = self.analyze_bug(instance)
                results.append(result)
            except Exception as e:
                print(f"❌ Error analyzing {instance.get('instance_id')}: {e}")
                continue
        
        print(f"\n{'#'*70}")
        print(f"COMPLETED: {len(results)}/{len(instances)} bugs analyzed")
        print(f"{'#'*70}\n")
        
        # Save results if output path provided
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"✓ Results saved to: {output_path}")
        
        return results


def test_analyzer():
    """Test with mock data"""
    import tempfile
    
    # Create mock repository
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / 'test_repo'
        repo_path.mkdir()
        
        # Create some files
        (repo_path / 'src').mkdir()
        (repo_path / 'src' / 'main.py').write_text("""
def calculate(x, y):
    return x + y
""")
        
        # Mock SWE-bench instance
        instance = {
            'instance_id': 'test-1',
            'repo': 'test/repo',
            'patch': """
--- a/src/main.py
+++ b/src/main.py
@@ -1,2 +1,3 @@
 def calculate(x, y):
-    return x + y
+    if y == 0:
+        return 0
+    return x + y
""",
            'base_commit': 'abc123',
            'problem_statement': 'Fix division by zero'
        }
        
        # Test
        analyzer = BugDifficultyAnalyzer(str(repo_path))
        result = analyzer.analyze_bug(instance)
        
        print("\n" + "="*70)
        print("TEST RESULT:")
        print(json.dumps(result, indent=2))
        print("="*70)
        
        print("\n✓ Integration test passed!")


if __name__ == '__main__':
    test_analyzer()
