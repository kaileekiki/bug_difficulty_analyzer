#!/usr/bin/env python3
"""
Comprehensive Test Suite for Production Bug Analyzer
"""

import sys
import time
from pathlib import Path

print("="*70)
print("BUG DIFFICULTY ANALYZER - PRODUCTION VERSION")
print("Comprehensive Test Suite")
print("="*70)

# Component tests
tests = [
    ("Graph Structures", "core/graphs.py"),
    ("CFG Builder", "core/cfg_builder.py"),
    ("Basic DFG Builder", "core/dfg_builder.py"),
    ("Enhanced DFG Builder (SSA)", "core/enhanced_dfg_builder.py"),
    ("Call Graph Builder", "core/callgraph_builder.py"),
    ("A* GED Approximation", "core/ged_approximation.py"),
    ("Beam Search GED", "core/beam_search_ged.py"),
    ("Basic Metrics", "metrics/basic_metrics.py"),
    ("AST Metrics", "metrics/ast_metrics.py"),
    ("Git Diff Parser", "utils/git_diff_parser.py"),
    ("Production Analyzer", "production_analyzer.py"),
]

passed = 0
failed = 0
errors = []

for name, script in tests:
    print(f"\n{'─'*70}")
    print(f"Testing: {name}")
    print(f"Script: {script}")
    print(f"{'─'*70}")
    
    start = time.time()
    
    try:
        # Run test
        import subprocess
        result = subprocess.run(
            ["python3", script],
            cwd=str(Path(__file__).parent),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        elapsed = time.time() - start
        
        if result.returncode == 0:
            print(f"✅ PASSED ({elapsed:.2f}s)")
            passed += 1
        else:
            print(f"❌ FAILED ({elapsed:.2f}s)")
            print(f"Error: {result.stderr[:200]}")
            failed += 1
            errors.append((name, result.stderr))
    
    except subprocess.TimeoutExpired:
        print(f"⏱️  TIMEOUT (>30s)")
        failed += 1
        errors.append((name, "Timeout"))
    
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        failed += 1
        errors.append((name, str(e)))

# Summary
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)
print(f"Total tests: {len(tests)}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")
print(f"Success rate: {passed/len(tests)*100:.1f}%")

if errors:
    print("\n" + "="*70)
    print("ERRORS")
    print("="*70)
    for name, error in errors:
        print(f"\n{name}:")
        print(f"  {error[:200]}")

print("\n" + "="*70)

if failed == 0:
    print("🎉 ALL TESTS PASSED!")
    print("Production analyzer is ready to use!")
else:
    print(f"⚠️  {failed} tests failed. See errors above.")

print("="*70)
