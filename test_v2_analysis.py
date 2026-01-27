#!/usr/bin/env python3
"""
Test V2 full repository analysis with actual code changes
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from production_analyzer_v2 import ProductionBugAnalyzerV2
import json


def test_with_actual_python_files():
    """
    Test V2 analyzer by creating actual files in a test scenario.
    This demonstrates what the analyzer would do with real SWE-bench data.
    """
    print("\n" + "="*70)
    print("V2 ANALYZER TEST - Simulating Real Workflow")
    print("="*70)
    
    # Simulate what would happen with two versions of a Python file
    old_code = """
def calculate_area(radius):
    return 3.14 * radius * radius

def main():
    area = calculate_area(5)
    print(area)
"""
    
    new_code = """
import math

def calculate_area(radius):
    if radius < 0:
        raise ValueError("Radius cannot be negative")
    return math.pi * radius * radius

def calculate_circumference(radius):
    if radius < 0:
        raise ValueError("Radius cannot be negative")
    return 2 * math.pi * radius

def main():
    area = calculate_area(5)
    circumference = calculate_circumference(5)
    print(f"Area: {area}, Circumference: {circumference}")
"""
    
    # Create analyzer
    analyzer = ProductionBugAnalyzerV2(repo_cache_dir="/tmp/test_v2_cache")
    
    # Simulate analyzing a file pair
    print("\nSimulating analysis of geometry.py...")
    print(f"BEFORE code: {len(old_code)} chars")
    print(f"AFTER code: {len(new_code)} chars")
    
    file_analysis = analyzer._analyze_file_pair("geometry.py", old_code, new_code)
    
    print("\n" + "="*70)
    print("ANALYSIS RESULTS")
    print("="*70)
    
    # Pretty print results
    if 'metrics' in file_analysis:
        metrics = file_analysis['metrics']
        
        # Basic metrics
        if 'basic' in metrics:
            print("\n📊 BASIC METRICS:")
            basic = metrics['basic']
            
            if 'LOC' in basic:
                loc = basic['LOC']
                print(f"  LOC Changes:")
                print(f"    - Old lines: {loc.get('old_total', 'N/A')}")
                print(f"    - New lines: {loc.get('new_total', 'N/A')}")
                print(f"    - Added: +{loc.get('added', 'N/A')}")
                print(f"    - Deleted: -{loc.get('deleted', 'N/A')}")
            
            if 'Cyclomatic_Complexity' in basic:
                cc = basic['Cyclomatic_Complexity']
                if 'delta_total' in cc:
                    print(f"  Cyclomatic Complexity Delta: {cc['delta_total']}")
            
            if 'Token_Edit_Distance' in basic:
                ted = basic['Token_Edit_Distance']
                if 'token_distance' in ted:
                    print(f"  Token Edit Distance: {ted['token_distance']}")
        
        # AST metrics
        if 'ast' in metrics:
            print("\n🌳 AST METRICS:")
            ast = metrics['ast']
            
            if 'AST_GED' in ast:
                ast_ged = ast['AST_GED']
                if 'ast_ged' in ast_ged:
                    print(f"  AST-GED: {ast_ged['ast_ged']:.2f}")
            
            if 'Exception_Handling' in ast:
                eh = ast['Exception_Handling']
                if 'total_exception_changes' in eh:
                    print(f"  Exception Changes: {eh['total_exception_changes']}")
            
            if 'Type_Changes' in ast:
                tc = ast['Type_Changes']
                if 'total_type_changes' in tc:
                    print(f"  Type Changes: {tc['total_type_changes']}")
        
        # Graph metrics
        if 'graph' in metrics:
            print("\n📈 GRAPH METRICS:")
            graph = metrics['graph']
            
            if 'DFG_GED' in graph:
                dfg = graph['DFG_GED']
                if 'dfg_ged' in dfg and dfg['dfg_ged'] != -1:
                    print(f"  ⭐ DFG-GED: {dfg['dfg_ged']:.2f}")
                    print(f"     Nodes: {dfg.get('nodes_before', 0)} → {dfg.get('nodes_after', 0)}")
                    print(f"     Edges: {dfg.get('edges_before', 0)} → {dfg.get('edges_after', 0)}")
                else:
                    print(f"  ⭐ DFG-GED: {dfg.get('dfg_ged', 'ERROR')}")
            
            if 'CFG_GED' in graph:
                cfg = graph['CFG_GED']
                if 'cfg_ged' in cfg and cfg['cfg_ged'] != -1:
                    print(f"  CFG-GED: {cfg['cfg_ged']:.2f}")
                    print(f"     Nodes: {cfg.get('nodes_before', 0)} → {cfg.get('nodes_after', 0)}")
                else:
                    print(f"  CFG-GED: {cfg.get('cfg_ged', 'ERROR')}")
            
            if 'Call_Graph_GED' in graph:
                cg = graph['Call_Graph_GED']
                if 'callgraph_ged' in cg and cg['callgraph_ged'] != -1:
                    print(f"  Call Graph-GED: {cg['callgraph_ged']:.2f}")
                    print(f"     Functions: {cg.get('functions_before', 0)} → {cg.get('functions_after', 0)}")
                else:
                    print(f"  Call Graph-GED: {cg.get('callgraph_ged', 'ERROR')}")
            
            if 'PDG_GED' in graph:
                pdg = graph['PDG_GED']
                if 'pdg_ged' in pdg and pdg['pdg_ged'] != -1:
                    print(f"  PDG-GED: {pdg['pdg_ged']:.2f}")
                else:
                    print(f"  PDG-GED: {pdg.get('pdg_ged', 'ERROR')}")
            
            if 'CPG_GED' in graph:
                cpg = graph['CPG_GED']
                if 'cpg_ged' in cpg and cpg['cpg_ged'] != -1:
                    print(f"  CPG-GED: {cpg['cpg_ged']:.2f}")
                else:
                    print(f"  CPG-GED: {cpg.get('cpg_ged', 'ERROR')}")
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70)
    
    # Save full results
    output_file = "/tmp/v2_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(file_analysis, f, indent=2)
    print(f"\n📁 Full results saved to: {output_file}")
    
    return file_analysis


if __name__ == '__main__':
    test_with_actual_python_files()
