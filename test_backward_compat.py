#!/usr/bin/env python3
"""
Test backward compatibility with existing code.
Ensures that existing usage patterns still work.
"""

import tempfile
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from swebench_loader import SWEBenchLoader


def test_old_usage_pattern_with_cache():
    """Test the old usage pattern where cache exists"""
    print("="*70)
    print("Backward Compatibility Test 1: Old pattern with cache")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create cache like the old code would
        cache_dir = Path(tmpdir)
        cache_file = cache_dir / "swebench_verified.json"
        
        mock_data = [
            {'instance_id': 'compat-test-1', 'repo': 'test/repo', 'patch': 'test'}
        ]
        with open(cache_file, 'w') as f:
            json.dump(mock_data, f)
        
        # Old usage pattern
        loader = SWEBenchLoader(dataset_dir=tmpdir)
        
        # This should work without changes
        dataset = loader.load_dataset()
        
        assert len(dataset) == 1
        assert dataset[0]['instance_id'] == 'compat-test-1'
        
        print("✅ Old usage pattern works with existing cache")
        return True


def test_explicit_download_then_load():
    """Test the old pattern of explicit download followed by load"""
    print("\n" + "="*70)
    print("Backward Compatibility Test 2: Explicit download then load")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = SWEBenchLoader(cache_dir=tmpdir)
        
        # Mock download
        def mock_download(force=False):
            mock_data = [
                {'instance_id': 'explicit-1', 'repo': 'test/repo', 'patch': 'test'}
            ]
            with open(loader.cache_file, 'w') as f:
                json.dump(mock_data, f)
            return loader.cache_file
        
        loader.download_dataset = mock_download
        
        # Old pattern: explicit download
        cache_path = loader.download_dataset()
        print(f"Downloaded to: {cache_path}")
        
        # Then load
        dataset = loader.load_dataset()
        
        assert len(dataset) == 1
        assert dataset[0]['instance_id'] == 'explicit-1'
        
        print("✅ Explicit download then load pattern still works")
        return True


def test_is_cached_method():
    """Test that is_cached() still works"""
    print("\n" + "="*70)
    print("Backward Compatibility Test 3: is_cached() method")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = SWEBenchLoader(cache_dir=tmpdir)
        
        # Should not be cached initially
        assert not loader.is_cached()
        print("✅ is_cached() returns False for non-existent cache")
        
        # Create cache
        mock_data = [{'instance_id': 'test'}]
        with open(loader.cache_file, 'w') as f:
            json.dump(mock_data, f)
        
        # Should be cached now
        assert loader.is_cached()
        print("✅ is_cached() returns True for existing cache")
        
        return True


def test_get_cache_path():
    """Test that get_cache_path() still works"""
    print("\n" + "="*70)
    print("Backward Compatibility Test 4: get_cache_path() method")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = SWEBenchLoader(cache_dir=tmpdir)
        
        cache_path = loader.get_cache_path()
        expected_path = Path(tmpdir) / "swebench_verified.json"
        
        assert cache_path == expected_path
        print(f"✅ get_cache_path() returns correct path: {cache_path}")
        
        return True


def test_dataset_dir_parameter():
    """Test backward compatibility with dataset_dir parameter"""
    print("\n" + "="*70)
    print("Backward Compatibility Test 5: dataset_dir parameter")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Old code might use dataset_dir instead of cache_dir
        loader = SWEBenchLoader(dataset_dir=tmpdir)
        
        expected_path = Path(tmpdir) / "swebench_verified.json"
        assert loader.cache_file == expected_path
        
        print("✅ dataset_dir parameter still works (backward compatibility)")
        return True


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Backward Compatibility Tests")
    print("="*70)
    
    success = True
    
    try:
        if not test_old_usage_pattern_with_cache():
            success = False
        
        if not test_explicit_download_then_load():
            success = False
        
        if not test_is_cached_method():
            success = False
        
        if not test_get_cache_path():
            success = False
        
        if not test_dataset_dir_parameter():
            success = False
        
        if success:
            print("\n" + "="*70)
            print("🎉 All backward compatibility tests passed!")
            print("="*70)
        else:
            print("\n❌ Some backward compatibility tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
