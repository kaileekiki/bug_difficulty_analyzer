"""
Production-Ready Bug Difficulty Analyzer
Integrates all enhanced components
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

sys.path.insert(0, str(Path(__file__).parent))

# Core components
from core.scope_extractor import ModuleScopeExtractor
from core.enhanced_dfg_builder import EnhancedDFGBuilder
from core.cfg_builder import CFGBuilder
from core.callgraph_builder import CallGraphBuilder
from core.beam_search_ged import BeamSearchGED

# Metrics
from metrics.basic_metrics import BasicMetrics
from metrics.ast_metrics import ASTMetrics

# Utils
from utils.git_diff_parser import GitDiffParser, FilePatch


class ProductionBugAnalyzer:
    """
    Production-ready bug difficulty analyzer with:
    - Enhanced DFG (SSA-inspired)
    - Beam Search GED
    - Git diff parsing
    - Parallel processing
    - Comprehensive error handling
    """
    
    def __init__(self, repo_path: Optional[str] = None, use_hybrid_ged: bool = True):
        self.repo_path = Path(repo_path) if repo_path else None
        self.use_hybrid_ged = use_hybrid_ged
        
        # Builders
        self.cfg_builder = CFGBuilder()
        self.dfg_builder = EnhancedDFGBuilder()
        self.cg_builder = CallGraphBuilder()
        
        # GED computer - Hybrid for best accuracy/speed tradeoff
        if use_hybrid_ged:
            from core.hybrid_ged import HybridGEDCalculator
            self.ged_computer = HybridGEDCalculator(max_time_per_graph=120.0)
            print("✓ Using Hybrid GED (adaptive beam width: k=100 for tiny, k=50 for small)")
        else:
            self.ged_computer = BeamSearchGED(beam_width=10)
            print("✓ Using Beam Search GED (k=10)")
        
        # Parsers
        self.diff_parser = GitDiffParser()
        
        # Scope extractor (if repo provided)
        self.scope_extractor = (ModuleScopeExtractor(str(repo_path)) 
                               if repo_path else None)
    
    def analyze_patch(self, patch_text: str, 
                     instance_id: str = "unknown") -> Dict[str, Any]:
        """
        Analyze a git patch.
        
        Args:
            patch_text: Git diff text
            instance_id: Identifier for this bug
            
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
        
        try:
            # Parse patch
            files = self.diff_parser.parse_patch(patch_text)
            print(f"✓ Parsed {len(files)} files")
            
            results['num_files'] = len(files)
            results['files'] = list(files.keys())
            
            if not files:
                results['errors'].append("No files found in patch")
                return results
            
            # Analyze each file
            file_results = []
            for filepath, file_patch in files.items():
                print(f"\n  Analyzing: {filepath}")
                file_analysis = self._analyze_file(file_patch)
                file_results.append(file_analysis)
            
            # Aggregate metrics
            results['metrics'] = self._aggregate_metrics(file_results)
            
        except Exception as e:
            results['errors'].append(f"Analysis error: {str(e)}")
            import traceback
            results['errors'].append(traceback.format_exc())
        
        results['analysis_time'] = time.time() - start_time
        print(f"\n✅ Analysis complete in {results['analysis_time']:.2f}s")
        print(f"{'='*70}\n")
        
        return results
    
    def _analyze_file(self, file_patch: FilePatch) -> Dict[str, Any]:
        """Analyze single file patch"""
        file_results = {
            'filepath': file_patch.filepath,
            'metrics': {}
        }
        
        old_code = file_patch.old_content
        new_code = file_patch.new_content
        
        # Skip empty files
        if not old_code and not new_code:
            return file_results
        
        try:
            # Tier 1: Basic Metrics
            print("    Computing basic metrics...")
            file_results['metrics']['basic'] = self._compute_basic_metrics(
                file_patch, old_code, new_code
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
    
    def _compute_basic_metrics(self, file_patch: FilePatch,
                               old_code: str, new_code: str) -> Dict[str, Any]:
        """Compute all basic metrics"""
        metrics = {}
        
        # LOC (already computed from patch)
        metrics['LOC'] = {
            'added': file_patch.added_lines,
            'deleted': file_patch.deleted_lines,
            'modified': file_patch.added_lines + file_patch.deleted_lines
        }
        
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
                # Import merge function
                from real_merged_ged import merge_cfg_dfg_to_pdg
                
                # Build graphs
                cfg_old = self.cfg_builder.build(old_code, "cfg_old")
                cfg_new = self.cfg_builder.build(new_code, "cfg_new")
                dfg_old = self.dfg_builder.build(old_code, "dfg_old")
                dfg_new = self.dfg_builder.build(new_code, "dfg_new")
                
                # Merge into PDGs
                pdg_old = merge_cfg_dfg_to_pdg(cfg_old, dfg_old, "PDG_old")
                pdg_new = merge_cfg_dfg_to_pdg(cfg_new, dfg_new, "PDG_new")
                
                # Compute GED with hybrid strategy
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
                edges_before = metrics['CFG_GED']['edges_before'] + metrics['DFG_GED']['edges_before']
                edges_after = metrics['CFG_GED']['edges_after'] + metrics['DFG_GED']['edges_after']
                
                metrics['PDG_GED'] = {
                    'pdg_ged': pdg_ged,
                    'normalized': pdg_ged / max(nodes_after, 1),
                    'nodes_before': nodes_before,
                    'nodes_after': nodes_after,
                    'edges_before': edges_before,
                    'edges_after': edges_after,
                    'method': 'approximation_fallback',
                    'error': str(e)
                }
            else:
                metrics['PDG_GED'] = {'pdg_ged': -1, 'error': str(e)}
        
        # CPG-GED (comprehensive - CFG + DFG + Call Graph merged)
        try:
            if 'CFG_GED' in metrics and 'DFG_GED' in metrics and 'Call_Graph_GED' in metrics:
                # Import merge function
                from real_merged_ged import merge_cfg_dfg_cg_to_cpg
                
                # Build graphs
                cfg_old = self.cfg_builder.build(old_code, "cfg_old")
                cfg_new = self.cfg_builder.build(new_code, "cfg_new")
                dfg_old = self.dfg_builder.build(old_code, "dfg_old")
                dfg_new = self.dfg_builder.build(new_code, "dfg_new")
                cg_old = self.cg_builder.build(old_code, "cg_old")
                cg_new = self.cg_builder.build(new_code, "cg_new")
                
                # Merge into CPGs
                cpg_old = merge_cfg_dfg_cg_to_cpg(cfg_old, dfg_old, cg_old, "CPG_old")
                cpg_new = merge_cfg_dfg_cg_to_cpg(cfg_new, dfg_new, cg_new, "CPG_new")
                
                # Compute GED with hybrid strategy
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
                
                edges_before = (metrics['CFG_GED']['edges_before'] + 
                               metrics['DFG_GED']['edges_before'] + 
                               metrics['Call_Graph_GED']['calls_before'])
                
                edges_after = (metrics['CFG_GED']['edges_after'] + 
                              metrics['DFG_GED']['edges_after'] + 
                              metrics['Call_Graph_GED']['calls_after'])
                
                metrics['CPG_GED'] = {
                    'cpg_ged': cpg_ged,
                    'normalized': cpg_ged / max(nodes_after, 1),
                    'nodes_before': nodes_before,
                    'nodes_after': nodes_after,
                    'edges_before': edges_before,
                    'edges_after': edges_after,
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
        
        # For now, simple aggregation (sum/average)
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
    
    def analyze_dataset(self, patches: List[Dict[str, str]], 
                       output_path: Optional[str] = None,
                       parallel: bool = False) -> List[Dict]:
        """
        Analyze multiple patches.
        
        Args:
            patches: List of {instance_id, patch_text}
            output_path: Where to save results
            parallel: Use parallel processing
        """
        print(f"\n{'#'*70}")
        print(f"ANALYZING {len(patches)} PATCHES")
        print(f"{'#'*70}\n")
        
        results = []
        
        if parallel and len(patches) > 1:
            # Parallel processing
            with ProcessPoolExecutor() as executor:
                futures = {
                    executor.submit(
                        self.analyze_patch,
                        p['patch_text'],
                        p.get('instance_id', f'patch_{i}')
                    ): i
                    for i, p in enumerate(patches)
                }
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        print(f"Error in parallel processing: {e}")
        else:
            # Sequential processing
            for i, patch_data in enumerate(patches, 1):
                print(f"\n[{i}/{len(patches)}]")
                try:
                    result = self.analyze_patch(
                        patch_data['patch_text'],
                        patch_data.get('instance_id', f'patch_{i}')
                    )
                    results.append(result)
                except Exception as e:
                    print(f"❌ Error: {e}")
                    continue
        
        print(f"\n{'#'*70}")
        print(f"COMPLETED: {len(results)}/{len(patches)} patches analyzed")
        print(f"{'#'*70}\n")
        
        # Save if requested
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"✓ Results saved to: {output_path}")
        
        return results


def test_production_analyzer():
    """Test production analyzer"""
    patch = """
diff --git a/calculator.py b/calculator.py
index 1234567..abcdefg 100644
--- a/calculator.py
+++ b/calculator.py
@@ -1,6 +1,10 @@
 def divide(a, b):
+    if b == 0:
+        return None
     return a / b
 
 def multiply(a, b):
+    if a > 1000 or b > 1000:
+        raise ValueError("Numbers too large")
     return a * b
"""
    
    print("Testing Production Bug Analyzer...")
    print("="*70)
    
    analyzer = ProductionBugAnalyzer(beam_width=10)
    result = analyzer.analyze_patch(patch, instance_id="test-001")
    
    print("\n" + "="*70)
    print("RESULTS:")
    print(json.dumps(result, indent=2, default=str)[:2000])
    print("="*70)
    
    print("\n✓ Production analyzer test passed!")


if __name__ == '__main__':
    test_production_analyzer()
