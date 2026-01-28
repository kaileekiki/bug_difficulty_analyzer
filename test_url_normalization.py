#!/usr/bin/env python3
"""
Unit tests for repository URL normalization.
Tests the normalize_repo_url method in production analyzers.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from production_analyzer_v2 import ProductionBugAnalyzerV2
from production_analyzer_v3 import ProductionBugAnalyzerV3


def test_normalize_repo_url():
    """Test URL normalization with various input formats"""
    print("\n" + "="*70)
    print("TEST: Repository URL Normalization")
    print("="*70)
    
    test_cases = [
        # (input, expected_url, expected_name)
        ("sympy/sympy", "https://github.com/sympy/sympy.git", "sympy_sympy"),
        ("django/django", "https://github.com/django/django.git", "django_django"),
        ("astropy/astropy", "https://github.com/astropy/astropy.git", "astropy_astropy"),
        ("scikit-learn/scikit-learn", "https://github.com/scikit-learn/scikit-learn.git", "scikit-learn_scikit-learn"),
        
        # Full URLs without .git
        ("https://github.com/sympy/sympy", "https://github.com/sympy/sympy.git", "sympy_sympy"),
        ("https://github.com/django/django", "https://github.com/django/django.git", "django_django"),
        ("https://github.com/astropy/astropy", "https://github.com/astropy/astropy.git", "astropy_astropy"),
        
        # Full URLs with .git
        ("https://github.com/sympy/sympy.git", "https://github.com/sympy/sympy.git", "sympy_sympy"),
        ("https://github.com/django/django.git", "https://github.com/django/django.git", "django_django"),
        ("https://github.com/scikit-learn/scikit-learn.git", "https://github.com/scikit-learn/scikit-learn.git", "scikit-learn_scikit-learn"),
        
        # URLs with trailing slashes
        ("https://github.com/django/django/", "https://github.com/django/django.git", "django_django"),
        ("https://github.com/astropy/astropy/", "https://github.com/astropy/astropy.git", "astropy_astropy"),
        
        # Edge cases with spaces (should be trimmed)
        (" sympy/sympy ", "https://github.com/sympy/sympy.git", "sympy_sympy"),
        (" https://github.com/django/django ", "https://github.com/django/django.git", "django_django"),
    ]
    
    passed = 0
    failed = 0
    
    for input_str, expected_url, expected_name in test_cases:
        try:
            url, name = ProductionBugAnalyzerV2.normalize_repo_url(input_str)
            
            if url == expected_url and name == expected_name:
                print(f"✓ '{input_str}'")
                print(f"  -> URL: {url}")
                print(f"  -> Name: {name}")
                passed += 1
            else:
                print(f"✗ '{input_str}'")
                print(f"  Expected URL: {expected_url}, Got: {url}")
                print(f"  Expected Name: {expected_name}, Got: {name}")
                failed += 1
        except Exception as e:
            print(f"✗ '{input_str}' - Exception: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"Results: {passed}/{len(test_cases)} passed, {failed} failed")
    print("="*70)
    
    return failed == 0


def test_v2_with_different_formats():
    """Test V2 analyzer with different repo formats"""
    print("\n" + "="*70)
    print("TEST: V2 Analyzer with Different Repo Formats")
    print("="*70)
    
    import tempfile
    
    test_cases = [
        ("sympy/sympy", "sympy_sympy", "sympy/sympy"),
        ("https://github.com/django/django", "django_django", "django/django"),
        ("https://github.com/astropy/astropy.git", "astropy_astropy", "astropy/astropy"),
    ]
    
    passed = 0
    failed = 0
    
    for repo_input, expected_name, expected_identifier in test_cases:
        print(f"\nTesting: {repo_input}")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = ProductionBugAnalyzerV2(repo_cache_dir=tmpdir)
            
            instance = {
                'repo': repo_input,
                'base_commit': 'abc123def456',
                'patch': """
diff --git a/test.py b/test.py
index 123..456 100644
--- a/test.py
+++ b/test.py
@@ -1,1 +1,1 @@
-old
+new
"""
            }
            
            result = analyzer.analyze_instance(instance, instance_id="test")
            
            # Check that normalize_repo_url was used correctly
            if 'repo_name' in result and result['repo_name'] == expected_name:
                print(f"  ✓ repo_name: {result['repo_name']}")
                if 'repo' in result and result['repo'] == expected_identifier:
                    print(f"  ✓ repo: {result['repo']}")
                    passed += 1
                else:
                    print(f"  ✗ repo: expected '{expected_identifier}', got '{result.get('repo')}'")
                    failed += 1
            else:
                print(f"  ✗ repo_name: expected '{expected_name}', got '{result.get('repo_name')}'")
                failed += 1
    
    print("\n" + "="*70)
    print(f"Results: {passed}/{len(test_cases)} passed, {failed} failed")
    print("="*70)
    
    return failed == 0


def test_v3_with_different_formats():
    """Test V3 analyzer with different repo formats"""
    print("\n" + "="*70)
    print("TEST: V3 Analyzer with Different Repo Formats")
    print("="*70)
    
    import tempfile
    
    test_cases = [
        ("sympy/sympy", "sympy_sympy", "sympy/sympy"),
        ("https://github.com/django/django", "django_django", "django/django"),
        ("https://github.com/astropy/astropy.git", "astropy_astropy", "astropy/astropy"),
    ]
    
    passed = 0
    failed = 0
    
    for repo_input, expected_name, expected_identifier in test_cases:
        print(f"\nTesting: {repo_input}")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = ProductionBugAnalyzerV3(repo_cache_dir=tmpdir)
            
            instance = {
                'repo': repo_input,
                'base_commit': 'abc123def456',
                'patch': """
diff --git a/test.py b/test.py
index 123..456 100644
--- a/test.py
+++ b/test.py
@@ -1,1 +1,1 @@
-old
+new
"""
            }
            
            result = analyzer.analyze_instance(instance, instance_id="test")
            
            # Check that normalize_repo_url was used correctly
            if 'repo_name' in result and result['repo_name'] == expected_name:
                print(f"  ✓ repo_name: {result['repo_name']}")
                if 'repo' in result and result['repo'] == expected_identifier:
                    print(f"  ✓ repo: {result['repo']}")
                    passed += 1
                else:
                    print(f"  ✗ repo: expected '{expected_identifier}', got '{result.get('repo')}'")
                    failed += 1
            else:
                print(f"  ✗ repo_name: expected '{expected_name}', got '{result.get('repo_name')}'")
                failed += 1
    
    print("\n" + "="*70)
    print(f"Results: {passed}/{len(test_cases)} passed, {failed} failed")
    print("="*70)
    
    return failed == 0


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("URL NORMALIZATION TEST SUITE")
    print("="*70)
    
    all_passed = True
    
    try:
        if not test_normalize_repo_url():
            all_passed = False
        
        if not test_v2_with_different_formats():
            all_passed = False
        
        if not test_v3_with_different_formats():
            all_passed = False
        
        if all_passed:
            print("\n" + "="*70)
            print("🎉 ALL TESTS PASSED!")
            print("="*70 + "\n")
            return 0
        else:
            print("\n" + "="*70)
            print("❌ SOME TESTS FAILED")
            print("="*70 + "\n")
            return 1
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
