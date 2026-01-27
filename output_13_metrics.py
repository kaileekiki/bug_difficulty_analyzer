#!/usr/bin/env python3
"""
Complete 13 Metrics Output
Outputs all metrics with detailed GED components for re-calculation
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from production_analyzer import ProductionBugAnalyzer

def format_metric_output(result):
    """Format all 13 metrics with detailed GED components"""
    
    if 'metrics' not in result or 'aggregated' not in result['metrics']:
        print("❌ No metrics found in result")
        return
    
    aggregated = result['metrics']['aggregated']
    
    print("\n" + "="*70)
    print("13 METRICS COMPLETE OUTPUT")
    print("="*70)
    
    # 1. AST-GED
    print("\n[1] AST-GED")
    print("-" * 70)
    if 'ast' in aggregated and 'AST_GED' in aggregated['ast']:
        ast_ged = aggregated['ast']['AST_GED'][0]
        print(f"  ast_ged: {ast_ged.get('ast_ged', -1)}")
        print(f"  ast_size_before: {ast_ged.get('ast_size_before', -1)}")
        print(f"  ast_size_after: {ast_ged.get('ast_size_after', -1)}")
        print(f"  ast_size_delta: {ast_ged.get('ast_size_delta', -1)}")
        print(f"  normalized_ged: {ast_ged.get('normalized_ged', -1):.4f}")
    else:
        print("  ❌ Not available")
    
    # 2. DFG-GED (Main Hypothesis!)
    print("\n[2] DFG-GED ⭐ (Main Hypothesis)")
    print("-" * 70)
    if 'graph' in aggregated and 'DFG_GED' in aggregated['graph']:
        dfg = aggregated['graph']['DFG_GED'][0]
        print(f"  dfg_ged: {dfg.get('dfg_ged', -1):.4f}")
        print(f"  dfg_nodes_before: {dfg.get('nodes_before', -1)}")
        print(f"  dfg_nodes_after: {dfg.get('nodes_after', -1)}")
        print(f"  dfg_edges_before: {dfg.get('edges_before', -1)}")
        print(f"  dfg_edges_after: {dfg.get('edges_after', -1)}")
        print(f"  dfg_normalized: {dfg.get('normalized', -1):.4f}")
        print(f"  dfg_def_use_chains_before: {dfg.get('def_use_chains_before', -1)}")
        print(f"  dfg_def_use_chains_after: {dfg.get('def_use_chains_after', -1)}")
        print(f"  method: {dfg.get('method', 'unknown')}")
        print(f"  beam_width: {dfg.get('beam_width', -1)}")
    else:
        print("  ❌ Not available")
    
    # 3. PDG-GED
    print("\n[3] PDG-GED")
    print("-" * 70)
    if 'graph' in aggregated and 'PDG_GED' in aggregated['graph']:
        pdg = aggregated['graph']['PDG_GED'][0]
        print(f"  pdg_ged: {pdg.get('pdg_ged', -1):.4f}")
        print(f"  pdg_nodes_before: {pdg.get('nodes_before', -1)}")
        print(f"  pdg_nodes_after: {pdg.get('nodes_after', -1)}")
        print(f"  pdg_edges_before: {pdg.get('edges_before', -1)}")
        print(f"  pdg_edges_after: {pdg.get('edges_after', -1)}")
        print(f"  pdg_normalized: {pdg.get('normalized', -1):.4f}")
        print(f"  method: {pdg.get('method', 'unknown')}")
    else:
        print("  ❌ Not available")
    
    # 4. LOC
    print("\n[4] LOC (Lines of Code)")
    print("-" * 70)
    if 'basic' in aggregated and 'LOC' in aggregated['basic']:
        loc = aggregated['basic']['LOC'][0]
        print(f"  added: {loc.get('added', -1)}")
        print(f"  deleted: {loc.get('deleted', -1)}")
        print(f"  modified: {loc.get('modified', -1)}")
    else:
        print("  ❌ Not available")
    
    # 5. Token Edit Distance
    print("\n[5] Token Edit Distance")
    print("-" * 70)
    if 'basic' in aggregated and 'Token_Edit_Distance' in aggregated['basic']:
        token = aggregated['basic']['Token_Edit_Distance'][0]
        print(f"  token_distance: {token.get('token_distance', -1)}")
        print(f"  tokens_before: {token.get('tokens_before', -1)}")
        print(f"  tokens_after: {token.get('tokens_after', -1)}")
        print(f"  token_change_ratio: {token.get('token_change_ratio', -1):.4f}")
    else:
        print("  ❌ Not available")
    
    # 6. CFG-GED
    print("\n[6] CFG-GED")
    print("-" * 70)
    if 'graph' in aggregated and 'CFG_GED' in aggregated['graph']:
        cfg = aggregated['graph']['CFG_GED'][0]
        print(f"  cfg_ged: {cfg.get('cfg_ged', -1):.4f}")
        print(f"  cfg_nodes_before: {cfg.get('nodes_before', -1)}")
        print(f"  cfg_nodes_after: {cfg.get('nodes_after', -1)}")
        print(f"  cfg_edges_before: {cfg.get('edges_before', -1)}")
        print(f"  cfg_edges_after: {cfg.get('edges_after', -1)}")
        print(f"  cfg_normalized: {cfg.get('normalized', -1):.4f}")
    else:
        print("  ❌ Not available")
    
    # 7. Cyclomatic Complexity
    print("\n[7] Cyclomatic Complexity")
    print("-" * 70)
    if 'basic' in aggregated and 'Cyclomatic_Complexity' in aggregated['basic']:
        cc = aggregated['basic']['Cyclomatic_Complexity'][0]
        print(f"  delta_average: {cc.get('delta_average', -1):.4f}")
        print(f"  delta_max: {cc.get('delta_max', -1)}")
        print(f"  delta_total: {cc.get('delta_total', -1)}")
    else:
        print("  ❌ Not available")
    
    # 8. Halstead Difficulty
    print("\n[8] Halstead Difficulty")
    print("-" * 70)
    if 'basic' in aggregated and 'Halstead_Difficulty' in aggregated['basic']:
        halstead = aggregated['basic']['Halstead_Difficulty'][0]
        print(f"  delta_difficulty: {halstead.get('delta_difficulty', -1):.4f}")
        print(f"  delta_volume: {halstead.get('delta_volume', -1):.4f}")
        print(f"  delta_effort: {halstead.get('delta_effort', -1):.4f}")
    else:
        print("  ❌ Not available")
    
    # 9. CPG-GED
    print("\n[9] CPG-GED")
    print("-" * 70)
    if 'graph' in aggregated and 'CPG_GED' in aggregated['graph']:
        cpg = aggregated['graph']['CPG_GED'][0]
        print(f"  cpg_ged: {cpg.get('cpg_ged', -1):.4f}")
        print(f"  cpg_nodes_before: {cpg.get('nodes_before', -1)}")
        print(f"  cpg_nodes_after: {cpg.get('nodes_after', -1)}")
        print(f"  cpg_edges_before: {cpg.get('edges_before', -1)}")
        print(f"  cpg_edges_after: {cpg.get('edges_after', -1)}")
        print(f"  cpg_normalized: {cpg.get('normalized', -1):.4f}")
        print(f"  method: {cpg.get('method', 'unknown')}")
    else:
        print("  ❌ Not available")
    
    # 10. Call Graph-GED
    print("\n[10] Call Graph-GED")
    print("-" * 70)
    if 'graph' in aggregated and 'Call_Graph_GED' in aggregated['graph']:
        cg = aggregated['graph']['Call_Graph_GED'][0]
        print(f"  callgraph_ged: {cg.get('callgraph_ged', -1):.4f}")
        print(f"  callgraph_functions_before: {cg.get('functions_before', -1)}")
        print(f"  callgraph_functions_after: {cg.get('functions_after', -1)}")
        print(f"  callgraph_calls_before: {cg.get('calls_before', -1)}")
        print(f"  callgraph_calls_after: {cg.get('calls_after', -1)}")
        print(f"  callgraph_normalized: {cg.get('normalized', -1):.4f}")
    else:
        print("  ❌ Not available")
    
    # 11. Variable Scope Change
    print("\n[11] Variable Scope Change")
    print("-" * 70)
    if 'basic' in aggregated and 'Variable_Scope' in aggregated['basic']:
        scope = aggregated['basic']['Variable_Scope'][0]
        print(f"  local_to_global: {scope.get('local_to_global', -1)}")
        print(f"  global_to_local: {scope.get('global_to_local', -1)}")
        print(f"  local_to_nonlocal: {scope.get('local_to_nonlocal', -1)}")
        print(f"  new_globals: {scope.get('new_globals', -1)}")
        print(f"  removed_globals: {scope.get('removed_globals', -1)}")
        print(f"  total_scope_changes: {scope.get('total_scope_changes', -1)}")
    else:
        print("  ❌ Not available")
    
    # 12. Type Change Complexity
    print("\n[12] Type Change Complexity")
    print("-" * 70)
    if 'ast' in aggregated and 'Type_Changes' in aggregated['ast']:
        types = aggregated['ast']['Type_Changes'][0]
        print(f"  annotated_args_delta: {types.get('annotated_args_delta', -1)}")
        print(f"  return_annotations_delta: {types.get('return_annotations_delta', -1)}")
        print(f"  variable_annotations_delta: {types.get('variable_annotations_delta', -1)}")
        print(f"  new_types: {types.get('new_types', [])}")
        print(f"  removed_types: {types.get('removed_types', [])}")
        print(f"  total_type_changes: {types.get('total_type_changes', -1)}")
    else:
        print("  ❌ Not available")
    
    # 13. Exception Handling Change
    print("\n[13] Exception Handling Change")
    print("-" * 70)
    if 'ast' in aggregated and 'Exception_Handling' in aggregated['ast']:
        exc = aggregated['ast']['Exception_Handling'][0]
        print(f"  try_blocks_delta: {exc.get('try_blocks_delta', -1)}")
        print(f"  except_handlers_delta: {exc.get('except_handlers_delta', -1)}")
        print(f"  new_exception_types: {exc.get('new_exception_types', [])}")
        print(f"  removed_exception_types: {exc.get('removed_exception_types', [])}")
        print(f"  exception_specificity_change: {exc.get('exception_specificity_change', -1)}")
        print(f"  finally_blocks_delta: {exc.get('finally_blocks_delta', -1)}")
        print(f"  raise_statements_delta: {exc.get('raise_statements_delta', -1)}")
        print(f"  total_exception_changes: {exc.get('total_exception_changes', -1)}")
    else:
        print("  ❌ Not available")
    
    print("\n" + "="*70)


def main():
    """Main function"""
    
    # Example patch
    patch = """
diff --git a/calculator.py b/calculator.py
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
    
    print("="*70)
    print("BUG DIFFICULTY ANALYZER - 13 METRICS OUTPUT")
    print("="*70)
    
    # Initialize analyzer with Hybrid GED
    analyzer = ProductionBugAnalyzer(use_hybrid_ged=True)
    
    # Analyze
    result = analyzer.analyze_patch(patch, instance_id="example-001")
    
    # Format output
    format_metric_output(result)
    
    # Save to JSON
    output_file = 'metrics_output.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✓ Full results saved to: {output_file}")
    print("="*70)


if __name__ == '__main__':
    main()
