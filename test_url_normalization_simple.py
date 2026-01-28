#!/usr/bin/env python3
"""
Simple unit tests for repository URL normalization.
Tests only the normalize_repo_url method without cloning.
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
        # (input, expected_url, expected_name, description)
        ("sympy/sympy", "https://github.com/sympy/sympy.git", "sympy_sympy", "Basic identifier"),
        ("django/django", "https://github.com/django/django.git", "django_django", "Basic identifier"),
        ("astropy/astropy", "https://github.com/astropy/astropy.git", "astropy_astropy", "Basic identifier"),
        ("scikit-learn/scikit-learn", "https://github.com/scikit-learn/scikit-learn.git", "scikit-learn_scikit-learn", "Hyphenated identifier"),
        
        # Full URLs without .git
        ("https://github.com/sympy/sympy", "https://github.com/sympy/sympy.git", "sympy_sympy", "URL without .git"),
        ("https://github.com/django/django", "https://github.com/django/django.git", "django_django", "URL without .git"),
        ("https://github.com/astropy/astropy", "https://github.com/astropy/astropy.git", "astropy_astropy", "URL without .git"),
        
        # Full URLs with .git
        ("https://github.com/sympy/sympy.git", "https://github.com/sympy/sympy.git", "sympy_sympy", "URL with .git"),
        ("https://github.com/django/django.git", "https://github.com/django/django.git", "django_django", "URL with .git"),
        ("https://github.com/scikit-learn/scikit-learn.git", "https://github.com/scikit-learn/scikit-learn.git", "scikit-learn_scikit-learn", "URL with .git"),
        
        # URLs with trailing slashes
        ("https://github.com/django/django/", "https://github.com/django/django.git", "django_django", "URL with trailing slash"),
        ("https://github.com/astropy/astropy/", "https://github.com/astropy/astropy.git", "astropy_astropy", "URL with trailing slash"),
        
        # Edge cases with spaces (should be trimmed)
        (" sympy/sympy ", "https://github.com/sympy/sympy.git", "sympy_sympy", "Identifier with spaces"),
        (" https://github.com/django/django ", "https://github.com/django/django.git", "django_django", "URL with spaces"),
    ]
    
    passed = 0
    failed = 0
    
    print("\nTesting ProductionBugAnalyzerV2.normalize_repo_url():")
    print("-" * 70)
    
    for input_str, expected_url, expected_name, description in test_cases:
        try:
            url, name = ProductionBugAnalyzerV2.normalize_repo_url(input_str)
            
            if url == expected_url and name == expected_name:
                print(f"✓ {description}: '{input_str}'")
                passed += 1
            else:
                print(f"✗ {description}: '{input_str}'")
                if url != expected_url:
                    print(f"  Expected URL: {expected_url}")
                    print(f"  Got URL:      {url}")
                if name != expected_name:
                    print(f"  Expected Name: {expected_name}")
                    print(f"  Got Name:      {name}")
                failed += 1
        except Exception as e:
            print(f"✗ {description}: '{input_str}' - Exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "-" * 70)
    print(f"V2 Results: {passed}/{len(test_cases)} passed")
    
    # Also test V3 (should inherit the method)
    print("\n" + "-" * 70)
    print("Testing ProductionBugAnalyzerV3.normalize_repo_url():")
    print("-" * 70)
    
    v3_passed = 0
    v3_failed = 0
    
    for input_str, expected_url, expected_name, description in test_cases[:3]:  # Just test a few
        try:
            url, name = ProductionBugAnalyzerV3.normalize_repo_url(input_str)
            
            if url == expected_url and name == expected_name:
                print(f"✓ {description}: '{input_str}'")
                v3_passed += 1
            else:
                print(f"✗ {description}: '{input_str}'")
                v3_failed += 1
        except Exception as e:
            print(f"✗ {description}: '{input_str}' - Exception: {e}")
            v3_failed += 1
    
    print("\n" + "-" * 70)
    print(f"V3 Results: {v3_passed}/3 passed")
    
    print("\n" + "="*70)
    if failed == 0 and v3_failed == 0:
        print("🎉 ALL URL NORMALIZATION TESTS PASSED!")
    else:
        print(f"❌ TESTS FAILED: V2={failed}, V3={v3_failed}")
    print("="*70)
    
    return failed == 0 and v3_failed == 0


def main():
    """Run all tests"""
    try:
        if test_normalize_repo_url():
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
