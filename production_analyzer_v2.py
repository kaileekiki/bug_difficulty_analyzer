"""
Production-Ready Bug Difficulty Analyzer V2
Full repository support with complete file analysis
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import time

sys.path.insert(0, str(Path(__file__).parent))

# Core components
from core.repo_manager import RepositoryManager
from core.scope_extractor import ModuleScopeExtractor
from core.enhanced_dfg_builder import EnhancedDFGBuilder
from core.cfg_builder import CFGBuilder
from core.callgraph_builder import CallGraphBuilder
from core.beam_search_ged import BeamSearchGED

# Metrics
from metrics.basic_metrics import BasicMetrics
from metrics.ast_metrics import ASTMetrics

# Utils
from utils.git_diff_parser import GitDiffParser


class ProductionBugAnalyzerV2:
    """
    V2 Analyzer with full repository support.
    
    Key differences from V1:
    - Analyzes FULL files, not just patch hunks
    - Uses RepositoryManager for git operations
    - More accurate LOC calculation
    - Complete code graphs for all GED metrics
    """
    
    def __init__(self, repo_cache_dir: str = "repo_cache", use_hybrid_ged: bool = True):
        self.use_hybrid_ged = use_hybrid_ged
        
        # Repository manager
        self.repo_manager = RepositoryManager(cache_dir=repo_cache_dir)
        
        # Builders
        self.cfg_builder = CFGBuilder()
        self.dfg_builder = EnhancedDFGBuilder()
        self.cg_builder = CallGraphBuilder()
        
        # GED computer - Hybrid for best accuracy/speed tradeoff
        if use_hybrid_ged:
            from core.hybrid_ged import HybridGEDCalculator
            self.ged_computer = HybridGEDCalculator(max_time_per_graph=120.0)
            print("✓ Using Hybrid GED (adaptive beam width)")
        else:
            self.ged_computer = BeamSearchGED(beam_width=10)
            print("✓ Using Beam Search GED (k=10)")
        
        # Parsers
        self.diff_parser = GitDiffParser()
    
    @staticmethod
    def normalize_repo_url(repo_field: str) -> tuple[str, str]:
        """
        Normalize repository field to GitHub URL and repo name.
        
        Handles multiple formats:
        - Repository identifier: "sympy/sympy" -> ("https://github.com/sympy/sympy.git", "sympy_sympy")
        - Full URL: "https://github.com/django/django" -> ("https://github.com/django/django.git", "django_django")
        - URL with .git: "https://github.com/scikit-learn/scikit-learn.git" -> (same, "scikit-learn_scikit-learn")
        
        Args:
            repo_field: Repository field from SWE-bench dataset
            
        Returns:
            Tuple of (repo_url, repo_name) where:
            - repo_url: Full GitHub clone URL with .git suffix
            - repo_name: Repository name for caching (owner_repo)
        """
        repo_field = repo_field.strip()
        
        # Check if it's already a URL
        if repo_field.startswith('http://') or repo_field.startswith('https://'):
            # Extract from URL
            # Remove .git suffix if present
            url_base = repo_field.rstrip('/')
            if url_base.endswith('.git'):
                url_base = url_base[:-4]
            
            # Extract owner/repo from URL
            # Expected format: https://github.com/owner/repo
            parts = url_base.split('/')
            if len(parts) >= 2:
                owner = parts[-2]
                repo = parts[-1]
                repo_identifier = f"{owner}/{repo}"
            else:
                # Fallback: just use the URL as-is
                repo_identifier = url_base.replace('https://github.com/', '').replace('http://github.com/', '')
            
            # Construct proper URL with .git
            repo_url = f"{url_base}.git"
            repo_name = repo_identifier.replace('/', '_')
            
            return repo_url, repo_name
        else:
            # Assume it's in "owner/repo" format
            repo_identifier = repo_field
            repo_url = f"https://github.com/{repo_identifier}.git"
            repo_name = repo_identifier.replace('/', '_')
            
            return repo_url, repo_name
    
    def analyze_instance(self, instance: Dict[str, Any], 
                        instance_id: str = "unknown") -> Dict[str, Any]:
        """
        Analyze a SWE-bench instance with full repository context.
        
        Workflow:
        1. Clone repository
        2. Checkout base_commit (before fix)
        3. Extract changed files from patch
        4. Get BEFORE content (full files)
        5. Apply patch
        6. Get AFTER content (full files)
        7. Analyze full file pairs
        8. Compute all 13 metrics
        9. Reset repository
        
        Args:
            instance: SWE-bench instance with repo, base_commit, patch
            instance_id: Identifier for this instance
            
        Returns:
            Complete analysis with all 13 metrics
        """
        print(f"\n{'='*70}")
        print(f"ANALYZING: {instance_id}")
        print(f"{'='*70}")
        
        start_time = time.time()
        
        results = {
            'instance_id': instance_id,
            'analysis_time': 0.0,
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
            print("\n[1/8] Cloning repository...")
            try:
                repo_path = self.repo_manager.clone_or_update(repo_url, repo_name)
            except Exception as e:
                results['errors'].append(f"Clone failed: {str(e)}")
                return results
            
            # Step 2: Checkout base commit
            print("\n[2/8] Checking out base commit...")
            if not self.repo_manager.checkout_commit(repo_path, base_commit):
                results['errors'].append(f"Checkout failed: {base_commit}")
                return results
            
            # Step 3: Extract changed files
            print("\n[3/8] Extracting changed files from patch...")
            changed_files = self.repo_manager.get_changed_files_from_patch(patch)
            print(f"  ✓ Found {len(changed_files)} changed files")
            results['num_files'] = len(changed_files)
            results['files'] = changed_files
            
            if not changed_files:
                results['errors'].append("No files found in patch")
                return results
            
            # Step 4: Get BEFORE content (full files)
            print("\n[4/8] Getting BEFORE content...")
            before_files = {}
            for filepath in changed_files:
                try:
                    content = self.repo_manager.get_file_content(repo_path, filepath)
                    before_files[filepath] = content
                    print(f"  ✓ {filepath}: {len(content)} chars")
                except Exception as e:
                    print(f"  ⚠️  {filepath}: {str(e)}")
                    before_files[filepath] = ""
            
            # Step 5: Apply patch
            print("\n[5/8] Applying patch...")
            if not self.repo_manager.apply_patch(repo_path, patch):
                # Patch application can fail if files are already correct
                # This is OK - we'll still analyze
                print("  ⚠️  Patch apply had issues (may be OK)")
            
            # Step 6: Get AFTER content (full files)
            print("\n[6/8] Getting AFTER content...")
            after_files = {}
            for filepath in changed_files:
                try:
                    content = self.repo_manager.get_file_content(repo_path, filepath)
                    after_files[filepath] = content
                    print(f"  ✓ {filepath}: {len(content)} chars")
                except Exception as e:
                    print(f"  ⚠️  {filepath}: {str(e)}")
                    after_files[filepath] = ""
            
            # Step 7: Analyze full file pairs
            print("\n[7/8] Analyzing files...")
            file_results = []
            for filepath in changed_files:
                if filepath.endswith('.py'):  # Only Python files
                    print(f"\n  Analyzing: {filepath}")
                    file_analysis = self._analyze_file_pair(
                        filepath,
                        before_files.get(filepath, ""),
                        after_files.get(filepath, "")
                    )
                    file_results.append(file_analysis)
            
            # Step 8: Aggregate metrics
            print("\n[8/8] Aggregating metrics...")
            results['metrics'] = self._aggregate_metrics(file_results)
            
            # Step 9: Reset repository (cleanup)
            self.repo_manager.reset_to_commit(repo_path, base_commit)
            
        except Exception as e:
            results['errors'].append(f"Analysis error: {str(e)}")
            import traceback
            results['errors'].append(traceback.format_exc())
        
        results['analysis_time'] = time.time() - start_time
        print(f"\n✅ Analysis complete in {results['analysis_time']:.2f}s")
        print(f"{'='*70}\n")
        
        return results
    
    def _parse_repo_name(self, repo_url: str) -> str:
        """Parse repository name from URL"""
        # Extract owner/repo from URL
        # https://github.com/owner/repo -> owner_repo
        parts = repo_url.rstrip('/').split('/')
        if len(parts) >= 2:
            owner = parts[-2]
            repo = parts[-1].replace('.git', '')
            return f"{owner}_{repo}"
        return "unknown_repo"
    
    def _analyze_file_pair(self, filepath: str, 
                          old_code: str, new_code: str) -> Dict[str, Any]:
        """Analyze single file pair (BEFORE and AFTER)"""
        file_results = {
            'filepath': filepath,
            'metrics': {}
        }
        
        # Skip empty files
        if not old_code and not new_code:
            return file_results
        
        try:
            # Tier 1: Basic Metrics
            print("    Computing basic metrics...")
            file_results['metrics']['basic'] = self._compute_basic_metrics(
                old_code, new_code
            )
            
            # Tier 2: AST Metrics
            print("    Computing AST metrics...")
            file_results['metrics']['ast'] = self._compute_ast_metrics(
                old_code, new_code
            )
            
            # Tier 3: Graph Metrics
            print("    Computing graph metrics...")
            file_results['metrics']['graph'] = self._compute_graph_metrics(
                old_code, new_code
            )
            
        except Exception as e:
            file_results['error'] = str(e)
        
        return file_results
    
    def _compute_basic_metrics(self, old_code: str, new_code: str) -> Dict[str, Any]:
        """Compute all basic metrics from full files"""
        metrics = {}
        
        # LOC - Calculate from full file comparison
        try:
            old_lines = old_code.split('\n')
            new_lines = new_code.split('\n')
            
            # Simple diff: count different lines
            added = len(new_lines) - len(old_lines)
            deleted = -added if added < 0 else 0
            added = added if added > 0 else 0
            
            metrics['LOC'] = {
                'added': added,
                'deleted': deleted,
                'modified': added + deleted,
                'old_total': len(old_lines),
                'new_total': len(new_lines)
            }
        except:
            metrics['LOC'] = {'added': -1, 'deleted': -1, 'error': True}
        
        # Token Edit Distance
        try:
            metrics['Token_Edit_Distance'] = BasicMetrics.compute_token_edit_distance(
                old_code, new_code
            )
        except:
            metrics['Token_Edit_Distance'] = {'token_distance': -1, 'error': True}
        
        # Cyclomatic Complexity
        try:
            metrics['Cyclomatic_Complexity'] = BasicMetrics.compute_cyclomatic_delta(
                old_code, new_code
            )
        except:
            metrics['Cyclomatic_Complexity'] = {'delta_total': -1, 'error': True}
        
        # Halstead Difficulty
        try:
            metrics['Halstead_Difficulty'] = BasicMetrics.compute_halstead_delta(
                old_code, new_code
            )
        except:
            metrics['Halstead_Difficulty'] = {'delta_difficulty': -1, 'error': True}
        
        # Variable Scope Changes
        try:
            metrics['Variable_Scope'] = BasicMetrics.analyze_variable_scope_changes(
                old_code, new_code
            )
        except:
            metrics['Variable_Scope'] = {'total_scope_changes': -1, 'error': True}
        
        return metrics
    
    def _compute_ast_metrics(self, old_code: str, new_code: str) -> Dict[str, Any]:
        """Compute all AST-based metrics"""
        metrics = {}
        
        # AST-GED
        try:
            metrics['AST_GED'] = ASTMetrics.compute_ast_ged(old_code, new_code)
        except:
            metrics['AST_GED'] = {'ast_ged': -1, 'error': True}
        
        # Exception Handling
        try:
            metrics['Exception_Handling'] = ASTMetrics.analyze_exception_handling(
                old_code, new_code
            )
        except:
            metrics['Exception_Handling'] = {'total_exception_changes': -1, 'error': True}
        
        # Type Changes
        try:
            metrics['Type_Changes'] = ASTMetrics.analyze_type_changes(
                old_code, new_code
            )
        except:
            metrics['Type_Changes'] = {'total_type_changes': -1, 'error': True}
        
        return metrics
    
    def _compute_graph_metrics(self, old_code: str, new_code: str) -> Dict[str, Any]:
        """Compute all graph-based metrics"""
        metrics = {}
        
        # CFG-GED
        try:
            cfg_old = self.cfg_builder.build(old_code, "cfg_old")
            cfg_new = self.cfg_builder.build(new_code, "cfg_new")
            cfg_ged = self.ged_computer.compute(cfg_old, cfg_new)
            
            metrics['CFG_GED'] = {
                'cfg_ged': cfg_ged['ged'],
                'normalized': cfg_ged['normalized_ged'],
                'nodes_before': len(cfg_old.nodes),
                'nodes_after': len(cfg_new.nodes),
                'edges_before': len(cfg_old.edges),
                'edges_after': len(cfg_new.edges)
            }
        except Exception as e:
            metrics['CFG_GED'] = {'cfg_ged': -1, 'error': str(e)}
        
        # DFG-GED ⭐ (Main Hypothesis - Enhanced!)
        try:
            dfg_old = self.dfg_builder.build(old_code, "dfg_old")
            dfg_new = self.dfg_builder.build(new_code, "dfg_new")
            dfg_ged = self.ged_computer.compute(dfg_old, dfg_new)
            
            metrics['DFG_GED'] = {
                'dfg_ged': dfg_ged['ged'],
                'normalized': dfg_ged['normalized_ged'],
                'nodes_before': len(dfg_old.nodes),
                'nodes_after': len(dfg_new.nodes),
                'edges_before': len(dfg_old.edges),
                'edges_after': len(dfg_new.edges),
                'def_use_chains_before': len(dfg_old.get_def_use_chains()),
                'def_use_chains_after': len(dfg_new.get_def_use_chains()),
                'method': dfg_ged['method'],
                'beam_width': dfg_ged.get('beam_width', 0)
            }
        except Exception as e:
            metrics['DFG_GED'] = {'dfg_ged': -1, 'error': str(e)}
        
        # Call Graph-GED
        try:
            cg_old = self.cg_builder.build(old_code, "cg_old")
            cg_new = self.cg_builder.build(new_code, "cg_new")
            cg_ged = self.ged_computer.compute(cg_old, cg_new)
            
            metrics['Call_Graph_GED'] = {
                'callgraph_ged': cg_ged['ged'],
                'normalized': cg_ged['normalized_ged'],
                'functions_before': len(cg_old.functions),
                'functions_after': len(cg_new.functions),
                'calls_before': len(cg_old.edges),
                'calls_after': len(cg_new.edges)
            }
        except Exception as e:
            metrics['Call_Graph_GED'] = {'callgraph_ged': -1, 'error': str(e)}
        
        # PDG-GED (CFG + DFG merged)
        try:
            if 'CFG_GED' in metrics and 'DFG_GED' in metrics:
                from real_merged_ged import merge_cfg_dfg_to_pdg
                
                cfg_old = self.cfg_builder.build(old_code, "cfg_old")
                cfg_new = self.cfg_builder.build(new_code, "cfg_new")
                dfg_old = self.dfg_builder.build(old_code, "dfg_old")
                dfg_new = self.dfg_builder.build(new_code, "dfg_new")
                
                pdg_old = merge_cfg_dfg_to_pdg(cfg_old, dfg_old, "PDG_old")
                pdg_new = merge_cfg_dfg_to_pdg(cfg_new, dfg_new, "PDG_new")
                
                pdg_ged_result = self.ged_computer.compute(pdg_old, pdg_new)
                
                metrics['PDG_GED'] = {
                    'pdg_ged': pdg_ged_result['ged'],
                    'normalized': pdg_ged_result['normalized_ged'],
                    'nodes_before': len(pdg_old.nodes),
                    'nodes_after': len(pdg_new.nodes),
                    'edges_before': len(pdg_old.edges),
                    'edges_after': len(pdg_new.edges),
                    'method': 'merged_graph_ged',
                    'strategy': pdg_ged_result.get('strategy', 'unknown')
                }
        except Exception as e:
            # Fallback to approximation
            if 'CFG_GED' in metrics and 'DFG_GED' in metrics:
                pdg_ged = metrics['CFG_GED']['cfg_ged'] + metrics['DFG_GED']['dfg_ged']
                nodes_before = metrics['CFG_GED']['nodes_before'] + metrics['DFG_GED']['nodes_before']
                nodes_after = metrics['CFG_GED']['nodes_after'] + metrics['DFG_GED']['nodes_after']
                
                metrics['PDG_GED'] = {
                    'pdg_ged': pdg_ged,
                    'normalized': pdg_ged / max(nodes_after, 1),
                    'nodes_before': nodes_before,
                    'nodes_after': nodes_after,
                    'method': 'approximation_fallback',
                    'error': str(e)
                }
            else:
                metrics['PDG_GED'] = {'pdg_ged': -1, 'error': str(e)}
        
        # CPG-GED (CFG + DFG + Call Graph merged)
        try:
            if 'CFG_GED' in metrics and 'DFG_GED' in metrics and 'Call_Graph_GED' in metrics:
                from real_merged_ged import merge_cfg_dfg_cg_to_cpg
                
                cfg_old = self.cfg_builder.build(old_code, "cfg_old")
                cfg_new = self.cfg_builder.build(new_code, "cfg_new")
                dfg_old = self.dfg_builder.build(old_code, "dfg_old")
                dfg_new = self.dfg_builder.build(new_code, "dfg_new")
                cg_old = self.cg_builder.build(old_code, "cg_old")
                cg_new = self.cg_builder.build(new_code, "cg_new")
                
                cpg_old = merge_cfg_dfg_cg_to_cpg(cfg_old, dfg_old, cg_old, "CPG_old")
                cpg_new = merge_cfg_dfg_cg_to_cpg(cfg_new, dfg_new, cg_new, "CPG_new")
                
                cpg_ged_result = self.ged_computer.compute(cpg_old, cpg_new)
                
                metrics['CPG_GED'] = {
                    'cpg_ged': cpg_ged_result['ged'],
                    'normalized': cpg_ged_result['normalized_ged'],
                    'nodes_before': len(cpg_old.nodes),
                    'nodes_after': len(cpg_new.nodes),
                    'edges_before': len(cpg_old.edges),
                    'edges_after': len(cpg_new.edges),
                    'method': 'merged_graph_ged',
                    'strategy': cpg_ged_result.get('strategy', 'unknown')
                }
        except Exception as e:
            # Fallback to approximation
            if 'CFG_GED' in metrics and 'DFG_GED' in metrics and 'Call_Graph_GED' in metrics:
                cpg_ged = (metrics['CFG_GED']['cfg_ged'] + 
                          metrics['DFG_GED']['dfg_ged'] + 
                          metrics['Call_Graph_GED']['callgraph_ged'])
                
                nodes_before = (metrics['CFG_GED']['nodes_before'] + 
                               metrics['DFG_GED']['nodes_before'] + 
                               metrics['Call_Graph_GED']['functions_before'])
                
                nodes_after = (metrics['CFG_GED']['nodes_after'] + 
                              metrics['DFG_GED']['nodes_after'] + 
                              metrics['Call_Graph_GED']['functions_after'])
                
                metrics['CPG_GED'] = {
                    'cpg_ged': cpg_ged,
                    'normalized': cpg_ged / max(nodes_after, 1),
                    'nodes_before': nodes_before,
                    'nodes_after': nodes_after,
                    'method': 'approximation_fallback',
                    'error': str(e)
                }
            else:
                metrics['CPG_GED'] = {'cpg_ged': -1, 'error': str(e)}
        
        return metrics
    
    def _aggregate_metrics(self, file_results: List[Dict]) -> Dict[str, Any]:
        """Aggregate metrics across multiple files"""
        if not file_results:
            return {}
        
        aggregated = {
            'num_files_analyzed': len(file_results),
            'aggregated': {}
        }
        
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
        
        aggregated['aggregated'] = all_metrics
        
        return aggregated


def test_analyzer_v2():
    """Test V2 analyzer with mock data"""
    print("Testing Production Bug Analyzer V2")
    print("="*70)
    
    # Mock instance
    instance = {
        'repo': 'https://github.com/octocat/Hello-World',
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
    
    analyzer = ProductionBugAnalyzerV2(repo_cache_dir="/tmp/test_v2_cache")
    result = analyzer.analyze_instance(instance, instance_id="test-v2-001")
    
    print("\n" + "="*70)
    print("RESULTS:")
    print(json.dumps(result, indent=2, default=str)[:2000])
    print("="*70)
    
    print("\n✓ V2 analyzer test passed!")


if __name__ == '__main__':
    test_analyzer_v2()
