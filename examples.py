#!/usr/bin/env python3
"""
Usage Examples for Bug Difficulty Analyzer
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from metrics.graph_metrics import GraphMetrics
from metrics.basic_metrics import BasicMetrics
from metrics.ast_metrics import ASTMetrics


def example1_simple_comparison():
    """Example 1: Compare two simple code versions"""
    print("\n" + "="*60)
    print("Example 1: Simple Code Comparison")
    print("="*60)
    
    code_before = """
def calculate(x, y):
    return x + y
"""
    
    code_after = """
def calculate(x, y):
    if y == 0:
        return 0
    return x / y
"""
    
    # Compute all graph metrics
    metrics = GraphMetrics()
    results = metrics.compute_all_graph_metrics(code_before, code_after)
    
    print("\n✓ Results:")
    print(f"  DFG-GED (Main Hypothesis): {results['DFG_GED']['dfg_ged']:.2f}")
    print(f"  CFG-GED: {results['CFG_GED']['cfg_ged']:.2f}")
    print(f"  PDG-GED: {results['PDG_GED']['pdg_ged']:.2f}")


def example2_basic_metrics():
    """Example 2: Compute basic metrics"""
    print("\n" + "="*60)
    print("Example 2: Basic Metrics")
    print("="*60)
    
    code_before = "x = 1\ny = 2"
    code_after = "x = 1\ny = 2\nz = x + y"
    
    # Token distance
    token_dist = BasicMetrics.compute_token_edit_distance(code_before, code_after)
    print(f"\n✓ Token Edit Distance: {token_dist['token_distance']}")
    
    # Cyclomatic complexity
    cc_delta = BasicMetrics.compute_cyclomatic_delta(code_before, code_after)
    print(f"✓ Cyclomatic Complexity Δ: {cc_delta['delta_total']}")
    
    # Halstead
    h_delta = BasicMetrics.compute_halstead_delta(code_before, code_after)
    print(f"✓ Halstead Difficulty Δ: {h_delta['delta_difficulty']:.2f}")


def example3_dfg_analysis():
    """Example 3: Detailed DFG analysis"""
    print("\n" + "="*60)
    print("Example 3: Detailed DFG Analysis")
    print("="*60)
    
    from core.dfg_builder import DFGBuilder
    
    code = """
def process(data):
    result = data * 2
    temp = result + 10
    return temp

x = 5
y = process(x)
z = y + 1
"""
    
    builder = DFGBuilder()
    dfg = builder.build(code)
    
    print(f"\n✓ DFG Statistics:")
    print(f"  Nodes: {len(dfg.nodes)}")
    print(f"  Edges: {len(dfg.edges)}")
    print(f"  Variables: {len(dfg.definitions)}")
    print(f"  Def-Use Chains: {len(dfg.get_def_use_chains())}")
    
    print(f"\n✓ Variables:")
    for var in list(dfg.definitions.keys())[:5]:
        defs = len(dfg.definitions.get(var, []))
        uses = len(dfg.uses.get(var, []))
        print(f"  {var}: {defs} definitions, {uses} uses")


def example4_full_comparison():
    """Example 4: Full metrics comparison"""
    print("\n" + "="*60)
    print("Example 4: Full Metrics Comparison")
    print("="*60)
    
    code_before = """
def foo(x):
    if x > 0:
        return x * 2
    return 0
"""
    
    code_after = """
def foo(x):
    if x > 0:
        result = x * 2
        if result > 100:
            return 100
        return result
    elif x == 0:
        return 1
    else:
        return -1
"""
    
    print("\nComputing all metrics...")
    
    # Basic metrics
    basic = BasicMetrics()
    token_dist = basic.compute_token_edit_distance(code_before, code_after)
    
    # AST metrics
    ast_metrics = ASTMetrics()
    ast_ged = ast_metrics.compute_ast_ged(code_before, code_after)
    
    # Graph metrics
    graph = GraphMetrics()
    graph_results = graph.compute_all_graph_metrics(code_before, code_after)
    
    print("\n✓ Summary of All Metrics:")
    print(f"\n  Basic:")
    print(f"    Token Distance: {token_dist['token_distance']}")
    
    print(f"\n  AST-based:")
    print(f"    AST-GED: {ast_ged['ast_ged']}")
    print(f"    Normalized: {ast_ged['normalized_ged']:.3f}")
    
    print(f"\n  Graph-based:")
    print(f"    DFG-GED ⭐: {graph_results['DFG_GED']['dfg_ged']:.2f}")
    print(f"    CFG-GED: {graph_results['CFG_GED']['cfg_ged']:.2f}")
    print(f"    PDG-GED: {graph_results['PDG_GED']['pdg_ged']:.2f}")
    print(f"    Call Graph-GED: {graph_results['Call_Graph_GED']['callgraph_ged']:.2f}")
    print(f"    CPG-GED: {graph_results['CPG_GED']['cpg_ged']:.2f}")


def example5_real_bug():
    """Example 5: Simulate real bug analysis"""
    print("\n" + "="*60)
    print("Example 5: Real Bug Simulation")
    print("="*60)
    
    # Bug: Division by zero not handled
    code_before = """
def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    return total / count
"""
    
    # Fix: Add zero check
    code_after = """
def calculate_average(numbers):
    if not numbers:
        return 0
    total = sum(numbers)
    count = len(numbers)
    return total / count
"""
    
    print("\nBug: Division by zero not handled")
    print("Fix: Add empty list check")
    
    metrics = GraphMetrics()
    results = metrics.compute_all_graph_metrics(code_before, code_after)
    
    print("\n✓ Bug Difficulty Metrics:")
    print(f"  DFG-GED (data flow change): {results['DFG_GED']['dfg_ged']:.2f}")
    print(f"  CFG-GED (control flow change): {results['CFG_GED']['cfg_ged']:.2f}")
    
    # Interpretation
    dfg = results['DFG_GED']['dfg_ged']
    cfg = results['CFG_GED']['cfg_ged']
    
    print("\n✓ Interpretation:")
    if cfg > dfg:
        print("  → Control flow dominated (if statement added)")
    else:
        print("  → Data flow dominated (variable dependencies changed)")
    
    print(f"  → Estimated LLM repair difficulty: {'Easy' if cfg + dfg < 5 else 'Hard'}")


if __name__ == '__main__':
    print("\n" + "#"*60)
    print("# Bug Difficulty Analyzer - Usage Examples")
    print("#"*60)
    
    example1_simple_comparison()
    example2_basic_metrics()
    example3_dfg_analysis()
    example4_full_comparison()
    example5_real_bug()
    
    print("\n" + "#"*60)
    print("# ✓ All examples completed!")
    print("#"*60)
    print()
