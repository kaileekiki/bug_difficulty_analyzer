#!/usr/bin/env python3
"""
Complete 13 Metrics Analyzer
Outputs all metrics in desired order with GED components
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from production_analyzer import ProductionBugAnalyzer


def analyze_and_print_all_metrics(patch_text: str, instance_id: str = "analysis"):
    """
    Analyze patch and print all 13 metrics with GED components.
    """
    print("\n" + "="*80)
    print(f"COMPLETE METRICS ANALYSIS: {instance_id}")
    print("="*80)
    
    # Initialize analyzer
    analyzer = ProductionBugAnalyzer(beam_width=10)
    
    # Run analysis
    result = analyzer.analyze_patch(patch_text, instance_id)
    
    if 'errors' in result and result['errors']:
        print("\n❌ ERRORS:")
        for error in result['errors']:
            print(f"  {error}")
        return result
    
    # Extract metrics
    metrics = result.get('metrics', {}).get('aggregated', {})
    
    print(f"\n⏱️  Analysis time: {result.get('analysis_time', 0):.3f}s")
    print(f"📁 Files analyzed: {result.get('num_files', 0)}")
    print("\n" + "="*80)
    print("13 METRICS")
    print("="*80)
    
    # 1. AST-GED
    print("\n1️⃣  AST-GED (Abstract Syntax Tree Graph Edit Distance)")
    print("-" * 80)
    if 'ast' in metrics and 'AST_GED' in metrics['ast']:
        ast_ged = metrics['ast']['AST_GED'][0]
        print(f"   GED value: {ast_ged.get('ast_ged', 'N/A')}")
        print(f"   Normalized GED: {ast_ged.get('normalized_ged', 'N/A'):.4f}")
        print(f"   AST size (before): {ast_ged.get('ast_size_before', 'N/A')} nodes")
        print(f"   AST size (after): {ast_ged.get('ast_size_after', 'N/A')} nodes")
        print(f"   AST size delta: {ast_ged.get('ast_size_delta', 'N/A')} nodes")
    else:
        print("   ⚠️  Not computed")
    
    # 2. DFG-GED ⭐ (Main Hypothesis)
    print("\n2️⃣  DFG-GED ⭐ (Data Flow Graph Edit Distance - MAIN HYPOTHESIS)")
    print("-" * 80)
    if 'graph' in metrics and 'DFG_GED' in metrics['graph']:
        dfg_ged = metrics['graph']['DFG_GED'][0]
        print(f"   GED value: {dfg_ged.get('dfg_ged', 'N/A')}")
        print(f"   Normalized GED: {dfg_ged.get('normalized', 'N/A'):.4f}")
        print(f"   DFG nodes (before): {dfg_ged.get('nodes_before', 'N/A')} nodes")
        print(f"   DFG nodes (after): {dfg_ged.get('nodes_after', 'N/A')} nodes")
        print(f"   DFG edges (before): {dfg_ged.get('edges_before', 'N/A')} edges")
        print(f"   DFG edges (after): {dfg_ged.get('edges_after', 'N/A')} edges")
        print(f"   Def-Use chains (before): {dfg_ged.get('def_use_chains_before', 'N/A')}")
        print(f"   Def-Use chains (after): {dfg_ged.get('def_use_chains_after', 'N/A')}")
        print(f"   Method: {dfg_ged.get('method', 'N/A')}")
        print(f"   Beam width: {dfg_ged.get('beam_width', 'N/A')}")
    else:
        print("   ⚠️  Not computed")
    
    # 3. PDG-GED
    print("\n3️⃣  PDG-GED (Program Dependence Graph Edit Distance)")
    print("-" * 80)
    if 'graph' in metrics and 'PDG_GED' in metrics['graph']:
        pdg_ged = metrics['graph']['PDG_GED'][0]
        print(f"   GED value: {pdg_ged.get('pdg_ged', 'N/A')}")
        print(f"   Normalized GED: {pdg_ged.get('normalized', 'N/A'):.4f}")
        print(f"   PDG nodes (before): {pdg_ged.get('nodes_before', 'N/A')} nodes")
        print(f"   PDG nodes (after): {pdg_ged.get('nodes_after', 'N/A')} nodes")
        print(f"   PDG edges (before): {pdg_ged.get('edges_before', 'N/A')} edges")
        print(f"   PDG edges (after): {pdg_ged.get('edges_after', 'N/A')} edges")
        print(f"   Method: {pdg_ged.get('method', 'N/A')}")
    else:
        print("   ⚠️  Not computed")
    
    # 4. LOC
    print("\n4️⃣  LOC (Lines of Code)")
    print("-" * 80)
    if 'basic' in metrics and 'LOC' in metrics['basic']:
        loc = metrics['basic']['LOC'][0]
        print(f"   Added: {loc.get('added', 'N/A')} lines")
        print(f"   Deleted: {loc.get('deleted', 'N/A')} lines")
        print(f"   Modified (total): {loc.get('modified', 'N/A')} lines")
    else:
        print("   ⚠️  Not computed")
    
    # 5. Token Edit Distance
    print("\n5️⃣  Token Edit Distance")
    print("-" * 80)
    if 'basic' in metrics and 'Token_Edit_Distance' in metrics['basic']:
        token = metrics['basic']['Token_Edit_Distance'][0]
        print(f"   Token distance: {token.get('token_distance', 'N/A')}")
        print(f"   Tokens (before): {token.get('tokens_before', 'N/A')}")
        print(f"   Tokens (after): {token.get('tokens_after', 'N/A')}")
        print(f"   Token change ratio: {token.get('token_change_ratio', 'N/A'):.4f}")
    else:
        print("   ⚠️  Not computed")
    
    # 6. CFG-GED
    print("\n6️⃣  CFG-GED (Control Flow Graph Edit Distance)")
    print("-" * 80)
    if 'graph' in metrics and 'CFG_GED' in metrics['graph']:
        cfg_ged = metrics['graph']['CFG_GED'][0]
        print(f"   GED value: {cfg_ged.get('cfg_ged', 'N/A')}")
        print(f"   Normalized GED: {cfg_ged.get('normalized', 'N/A'):.4f}")
        print(f"   CFG nodes (before): {cfg_ged.get('nodes_before', 'N/A')} nodes")
        print(f"   CFG nodes (after): {cfg_ged.get('nodes_after', 'N/A')} nodes")
        print(f"   CFG edges (before): {cfg_ged.get('edges_before', 'N/A')} edges")
        print(f"   CFG edges (after): {cfg_ged.get('edges_after', 'N/A')} edges")
    else:
        print("   ⚠️  Not computed")
    
    # 7. Cyclomatic Complexity
    print("\n7️⃣  Cyclomatic Complexity")
    print("-" * 80)
    if 'basic' in metrics and 'Cyclomatic_Complexity' in metrics['basic']:
        cc = metrics['basic']['Cyclomatic_Complexity'][0]
        print(f"   Delta (average): {cc.get('delta_average', 'N/A'):.4f}")
        print(f"   Delta (max): {cc.get('delta_max', 'N/A')}")
        print(f"   Delta (total): {cc.get('delta_total', 'N/A')}")
    else:
        print("   ⚠️  Not computed")
    
    # 8. Halstead Difficulty
    print("\n8️⃣  Halstead Difficulty")
    print("-" * 80)
    if 'basic' in metrics and 'Halstead_Difficulty' in metrics['basic']:
        halstead = metrics['basic']['Halstead_Difficulty'][0]
        print(f"   Delta difficulty: {halstead.get('delta_difficulty', 'N/A'):.4f}")
        print(f"   Delta volume: {halstead.get('delta_volume', 'N/A'):.4f}")
        print(f"   Delta effort: {halstead.get('delta_effort', 'N/A'):.4f}")
    else:
        print("   ⚠️  Not computed")
    
    # 9. CPG-GED
    print("\n9️⃣  CPG-GED (Code Property Graph Edit Distance)")
    print("-" * 80)
    if 'graph' in metrics and 'CPG_GED' in metrics['graph']:
        cpg_ged = metrics['graph']['CPG_GED'][0]
        print(f"   GED value: {cpg_ged.get('cpg_ged', 'N/A')}")
        print(f"   Normalized GED: {cpg_ged.get('normalized', 'N/A'):.4f}")
        print(f"   CPG nodes (before): {cpg_ged.get('nodes_before', 'N/A')} nodes")
        print(f"   CPG nodes (after): {cpg_ged.get('nodes_after', 'N/A')} nodes")
        print(f"   CPG edges (before): {cpg_ged.get('edges_before', 'N/A')} edges")
        print(f"   CPG edges (after): {cpg_ged.get('edges_after', 'N/A')} edges")
        print(f"   Method: {cpg_ged.get('method', 'N/A')}")
    else:
        print("   ⚠️  Not computed")
    
    # 10. Call Graph-GED
    print("\n🔟 Call Graph-GED")
    print("-" * 80)
    if 'graph' in metrics and 'Call_Graph_GED' in metrics['graph']:
        cg_ged = metrics['graph']['Call_Graph_GED'][0]
        print(f"   GED value: {cg_ged.get('callgraph_ged', 'N/A')}")
        print(f"   Normalized GED: {cg_ged.get('normalized', 'N/A'):.4f}")
        print(f"   Functions (before): {cg_ged.get('functions_before', 'N/A')}")
        print(f"   Functions (after): {cg_ged.get('functions_after', 'N/A')}")
        print(f"   Call edges (before): {cg_ged.get('calls_before', 'N/A')} calls")
        print(f"   Call edges (after): {cg_ged.get('calls_after', 'N/A')} calls")
    else:
        print("   ⚠️  Not computed")
    
    # 11. Variable Scope Change
    print("\n1️⃣1️⃣  Variable Scope Change")
    print("-" * 80)
    if 'basic' in metrics and 'Variable_Scope' in metrics['basic']:
        scope = metrics['basic']['Variable_Scope'][0]
        print(f"   Local → Global: {scope.get('local_to_global', 'N/A')}")
        print(f"   Global → Local: {scope.get('global_to_local', 'N/A')}")
        print(f"   Local → Nonlocal: {scope.get('local_to_nonlocal', 'N/A')}")
        print(f"   New globals: {scope.get('new_globals', 'N/A')}")
        print(f"   Removed globals: {scope.get('removed_globals', 'N/A')}")
        print(f"   Total scope changes: {scope.get('total_scope_changes', 'N/A')}")
    else:
        print("   ⚠️  Not computed")
    
    # 12. Type Change Complexity
    print("\n1️⃣2️⃣  Type Change Complexity")
    print("-" * 80)
    if 'ast' in metrics and 'Type_Changes' in metrics['ast']:
        types = metrics['ast']['Type_Changes'][0]
        print(f"   Annotated args delta: {types.get('annotated_args_delta', 'N/A')}")
        print(f"   Return annotations delta: {types.get('return_annotations_delta', 'N/A')}")
        print(f"   Variable annotations delta: {types.get('variable_annotations_delta', 'N/A')}")
        print(f"   New types: {types.get('new_types', [])}")
        print(f"   Removed types: {types.get('removed_types', [])}")
        print(f"   Total type changes: {types.get('total_type_changes', 'N/A')}")
    else:
        print("   ⚠️  Not computed")
    
    # 13. Exception Handling Change
    print("\n1️⃣3️⃣  Exception Handling Change")
    print("-" * 80)
    if 'ast' in metrics and 'Exception_Handling' in metrics['ast']:
        exc = metrics['ast']['Exception_Handling'][0]
        print(f"   Try blocks delta: {exc.get('try_blocks_delta', 'N/A')}")
        print(f"   Except handlers delta: {exc.get('except_handlers_delta', 'N/A')}")
        print(f"   New exception types: {exc.get('new_exception_types', [])}")
        print(f"   Removed exception types: {exc.get('removed_exception_types', [])}")
        print(f"   Exception specificity change: {exc.get('exception_specificity_change', 'N/A')}")
        print(f"   Finally blocks delta: {exc.get('finally_blocks_delta', 'N/A')}")
        print(f"   Raise statements delta: {exc.get('raise_statements_delta', 'N/A')}")
        print(f"   Total exception changes: {exc.get('total_exception_changes', 'N/A')}")
    else:
        print("   ⚠️  Not computed")
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE")
    print("="*80)
    
    # Save to JSON
    output_file = f"{instance_id}_metrics.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n💾 Full results saved to: {output_file}")
    
    return result


def main():
    """Main function with example patch"""
    
    # Example patch
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
    
    print("\n" + "🚀" * 40)
    print("Bug Difficulty Analyzer - Complete 13 Metrics")
    print("🚀" * 40)
    
    result = analyze_and_print_all_metrics(patch, "example-bug-001")
    
    print("\n" + "💡" * 40)
    print("HOW TO USE WITH YOUR OWN PATCH:")
    print("💡" * 40)
    print("""
1. Copy this file and modify the 'patch' variable
2. Or use it as a module:
   
   from analyze_all_metrics import analyze_and_print_all_metrics
   
   my_patch = "..." # Your git diff here
   result = analyze_and_print_all_metrics(my_patch, "my-bug-id")
""")


if __name__ == '__main__':
    main()
