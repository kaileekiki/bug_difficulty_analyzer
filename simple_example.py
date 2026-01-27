#!/usr/bin/env python3
"""
간단한 사용 예시 - 패치 분석
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from production_analyzer import ProductionBugAnalyzer

# 1. Analyzer 초기화
analyzer = ProductionBugAnalyzer(beam_width=10)

# 2. 분석할 패치
patch = """
diff --git a/calculator.py b/calculator.py
--- a/calculator.py
+++ b/calculator.py
@@ -1,3 +1,6 @@
 def divide(a, b):
+    if b == 0:
+        return None
     return a / b
"""

# 3. 분석 실행
print("🚀 Starting analysis...")
result = analyzer.analyze_patch(patch, instance_id="example-1")

# 4. 결과 출력
print("\n" + "="*70)
print("📊 ANALYSIS RESULTS")
print("="*70)

# Basic info
print(f"\nInstance ID: {result['instance_id']}")
print(f"Analysis time: {result['analysis_time']:.2f}s")
print(f"Files analyzed: {result.get('num_files', 0)}")

# Get metrics
if 'metrics' in result and 'aggregated' in result['metrics']:
    aggregated = result['metrics']['aggregated']
    
    # LOC
    if 'basic' in aggregated and 'LOC' in aggregated['basic']:
        loc = aggregated['basic']['LOC'][0]
        print(f"\n📝 LOC:")
        print(f"   Added: {loc['added']} lines")
        print(f"   Deleted: {loc['deleted']} lines")
    
    # DFG-GED (Main Hypothesis!)
    if 'graph' in aggregated and 'DFG_GED' in aggregated['graph']:
        dfg = aggregated['graph']['DFG_GED'][0]
        print(f"\n⭐ DFG-GED (Main Hypothesis):")
        print(f"   GED: {dfg['dfg_ged']:.2f}")
        print(f"   Normalized: {dfg['normalized']:.3f}")
        print(f"   Method: {dfg.get('method', 'unknown')}")
        print(f"   Beam width: {dfg.get('beam_width', 0)}")
    
    # CFG-GED
    if 'graph' in aggregated and 'CFG_GED' in aggregated['graph']:
        cfg = aggregated['graph']['CFG_GED'][0]
        print(f"\n🔀 CFG-GED:")
        print(f"   GED: {cfg['cfg_ged']:.2f}")
    
    # AST-GED
    if 'ast' in aggregated and 'AST_GED' in aggregated['ast']:
        ast_ged = aggregated['ast']['AST_GED'][0]
        print(f"\n🌳 AST-GED:")
        print(f"   GED: {ast_ged['ast_ged']}")
        print(f"   Normalized: {ast_ged['normalized_ged']:.3f}")

print("\n" + "="*70)
print("✅ Analysis complete!")
print("="*70)
