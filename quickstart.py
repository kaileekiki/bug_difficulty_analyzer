#!/usr/bin/env python3
"""
Quick Start Guide - Bug Difficulty Analyzer
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from metrics.graph_metrics import GraphMetrics
from metrics.basic_metrics import BasicMetrics
from metrics.ast_metrics import ASTMetrics

# ============================================================
# USAGE 1: Compare two code versions
# ============================================================

code_before = """
def process_data(data):
    result = data * 2
    return result
"""

code_after = """
def process_data(data):
    if data < 0:
        return None
    result = data * 2
    validated = result + 10
    return validated
"""

# Initialize metrics computer
metrics = GraphMetrics()

# Compute all graph-based metrics
results = metrics.compute_all_graph_metrics(code_before, code_after)

# Access results
dfg_ged = results['DFG_GED']['dfg_ged']
cfg_ged = results['CFG_GED']['cfg_ged']

print(f"DFG-GED (Main Hypothesis): {dfg_ged}")
print(f"CFG-GED: {cfg_ged}")

# ============================================================
# USAGE 2: Compute specific metrics
# ============================================================

# Token distance
token_result = BasicMetrics.compute_token_edit_distance(code_before, code_after)
print(f"\nToken Distance: {token_result['token_distance']}")

# AST-GED
ast_result = ASTMetrics.compute_ast_ged(code_before, code_after)
print(f"AST-GED: {ast_result['ast_ged']}")

# Exception handling changes
exc_result = ASTMetrics.analyze_exception_handling(code_before, code_after)
print(f"Exception Changes: {exc_result['total_exception_changes']}")

# ============================================================
# USAGE 3: Build individual graphs
# ============================================================

from core.dfg_builder import DFGBuilder
from core.cfg_builder import CFGBuilder

# Build DFG
dfg_builder = DFGBuilder()
dfg = dfg_builder.build(code_after)
print(f"\nDFG has {len(dfg.nodes)} nodes and {len(dfg.edges)} edges")

# Build CFG
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code_after)
print(f"CFG has {len(cfg.nodes)} nodes and {len(cfg.edges)} edges")

# ============================================================
# USAGE 4: Analyze bug patch
# ============================================================

patch = """
--- a/calculator.py
+++ b/calculator.py
@@ -1,2 +1,4 @@
 def divide(a, b):
+    if b == 0:
+        return None
     return a / b
"""

# Extract LOC
loc = BasicMetrics.compute_loc(patch)
print(f"\nPatch LOC: {loc['modified']} lines changed")

print("\n✓ Quick start complete!")
