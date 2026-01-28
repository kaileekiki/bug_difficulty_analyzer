#!/bin/bash
# V3 Module-Level Scope Analysis Demo

echo "=============================================="
echo "V3 Module-Level Scope Analysis Demo"
echo "=============================================="
echo ""

echo "1. Testing V3 Scope Extractor..."
python3 core/scope_extractor.py 2>&1 | grep -A 5 "FINAL SCOPE"
echo ""

echo "2. Testing V3 Unit Tests..."
python3 test_v3_scope.py 2>&1 | grep -E "(TEST:|PASSED|✓)"
echo ""

echo "3. Testing V3 Pipeline with Mock Data..."
timeout 60 python3 run_swebench_analysis_v3.py --mock --limit 2 2>&1 | grep -E "(ANALYZING|✓|Total scope|CSV)"
echo ""

echo "4. Checking V3 CLI Help..."
python3 run_swebench_analysis_v3.py --help | grep -E "(scope-depth|top-k)"
echo ""

echo "=============================================="
echo "✓ V3 Demo Complete!"
echo "=============================================="
