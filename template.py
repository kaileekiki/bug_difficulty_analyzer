#!/usr/bin/env python3
"""
최소한의 사용 예시 - 이 템플릿을 복사해서 사용하세요!
"""

from production_analyzer import ProductionBugAnalyzer

# Initialize
analyzer = ProductionBugAnalyzer(beam_width=10)

# Your patch
patch = """
diff --git a/your_file.py b/your_file.py
--- a/your_file.py
+++ b/your_file.py
@@ -1,2 +1,3 @@
 def foo():
+    print("new line")
     pass
"""

# Analyze
result = analyzer.analyze_patch(patch, "my-bug-001")

# Get DFG-GED (Main Hypothesis!)
dfg = result['metrics']['aggregated']['graph']['DFG_GED'][0]

print(f"DFG-GED: {dfg['dfg_ged']:.2f}")
print(f"Method: {dfg['method']}")
print(f"Beam width: {dfg['beam_width']}")

# Save to JSON
import json
with open('results.json', 'w') as f:
    json.dump(result, f, indent=2)
print("\n✓ Results saved to results.json")
