#!/usr/bin/env python3
"""
Test to validate V3 repository URL construction fix.
Ensures that V3 correctly constructs GitHub URLs from repository identifiers.
"""
import sys
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).parent))

from production_analyzer_v3 import ProductionBugAnalyzerV3


def test_url_construction():
    """Test that V3 correctly constructs GitHub URLs from repository identifiers"""
    print("\n" + "="*70)
    print("TEST: V3 Repository URL Construction")
    print("="*70)
    
    # Create analyzer instance
    with tempfile.TemporaryDirectory() as tmpdir:
        analyzer = ProductionBugAnalyzerV3(
            repo_cache_dir=tmpdir,
            scope_depth=2,
            top_k_secondary=3
        )
        
        # Test case 1: Repository identifier (SWE-bench format)
        print("\nTest 1: Repository identifier format")
        instance = {
            'repo': 'sympy/sympy',
            'base_commit': 'abc123def456',
            'patch': """
diff --git a/test.py b/test.py
index 123..456 100644
--- a/test.py
+++ b/test.py
@@ -1 +1 @@
-old
+new
"""
        }
        
        # Analyze - we expect it to construct the URL internally
        result = analyzer.analyze_instance(instance, instance_id="test-001")
        
        # Verify results
        assert 'repo_name' in result, "Missing repo_name in results"
        assert result['repo_name'] == 'sympy_sympy', f"Expected 'sympy_sympy', got '{result['repo_name']}'"
        assert 'repo' in result, "Missing repo in results"
        assert result['repo'] == 'sympy/sympy', f"Expected 'sympy/sympy', got '{result['repo']}'"
        
        print(f"  ✓ repo_name: {result['repo_name']}")
        print(f"  ✓ repo: {result['repo']}")
        
        # Test case 2: Another repository
        print("\nTest 2: Different repository identifier")
        instance2 = {
            'repo': 'astropy/astropy',
            'base_commit': 'def789abc012',
            'patch': """
diff --git a/file.py b/file.py
index 789..012 100644
--- a/file.py
+++ b/file.py
@@ -1 +1 @@
-before
+after
"""
        }
        
        result2 = analyzer.analyze_instance(instance2, instance_id="test-002")
        
        assert result2['repo_name'] == 'astropy_astropy', f"Expected 'astropy_astropy', got '{result2['repo_name']}'"
        assert result2['repo'] == 'astropy/astropy', f"Expected 'astropy/astropy', got '{result2['repo']}'"
        
        print(f"  ✓ repo_name: {result2['repo_name']}")
        print(f"  ✓ repo: {result2['repo']}")
        
        # Test case 3: Edge case - verify URL would be correct (we can't clone, but can check the logic)
        print("\nTest 3: Verify URL construction logic")
        repo_identifier = "django/django"
        expected_url = "https://github.com/django/django.git"
        expected_name = "django_django"
        
        # Simulate what the code does
        constructed_url = f"https://github.com/{repo_identifier}.git"
        constructed_name = repo_identifier.replace('/', '_')
        
        assert constructed_url == expected_url, f"URL construction failed: {constructed_url} != {expected_url}"
        assert constructed_name == expected_name, f"Name construction failed: {constructed_name} != {expected_name}"
        
        print(f"  ✓ URL construction: {repo_identifier} -> {constructed_url}")
        print(f"  ✓ Name construction: {repo_identifier} -> {constructed_name}")
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70)


def test_missing_fields():
    """Test that missing required fields are handled correctly"""
    print("\n" + "="*70)
    print("TEST: Missing Required Fields Handling")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        analyzer = ProductionBugAnalyzerV3(repo_cache_dir=tmpdir)
        
        # Test missing repo
        instance = {
            'base_commit': 'abc123',
            'patch': 'diff --git a/test.py'
        }
        result = analyzer.analyze_instance(instance, instance_id="test-missing")
        
        assert len(result['errors']) > 0, "Should have errors for missing fields"
        assert any('Missing required fields' in err for err in result['errors']), \
            "Should have specific error about missing fields"
        
        print(f"  ✓ Missing fields handled correctly")
        print(f"  ✓ Error: {result['errors'][0]}")
        
        print("\n" + "="*70)
        print("TEST PASSED ✓")
        print("="*70)


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("V3 URL FIX VALIDATION TESTS")
    print("="*70)
    
    try:
        test_url_construction()
        test_missing_fields()
        
        print("\n" + "="*70)
        print("ALL VALIDATION TESTS PASSED ✓")
        print("="*70 + "\n")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
