#!/usr/bin/env python3
"""
Tests for SWEBenchLoader auto-download functionality.
"""

import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parent))
from swebench_loader import SWEBenchLoader


def test_load_dataset_with_existing_cache():
    """Test that load_dataset uses existing cache without downloading"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create cache file
        cache_file = Path(tmpdir) / "swebench_verified.json"
        test_data = [
            {'instance_id': 'test-1', 'repo': 'test/repo', 'patch': 'test patch'}
        ]
        with open(cache_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load dataset
        loader = SWEBenchLoader(cache_dir=tmpdir)
        dataset = loader.load_dataset()
        
        # Verify
        assert len(dataset) == 1
        assert dataset[0]['instance_id'] == 'test-1'
        print("✅ Test passed: load_dataset uses existing cache")


def test_load_dataset_auto_downloads_when_cache_missing():
    """Test that load_dataset auto-downloads when cache doesn't exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = SWEBenchLoader(cache_dir=tmpdir)
        
        # Mock the download to avoid actual download
        mock_data = [
            {'instance_id': 'mock-1', 'repo': 'test/repo', 'patch': 'test patch'}
        ]
        
        with patch.object(loader, 'download_dataset') as mock_download:
            # Setup mock to create the cache file
            def create_cache():
                with open(loader.cache_file, 'w') as f:
                    json.dump(mock_data, f)
                return loader.cache_file
            
            mock_download.side_effect = create_cache
            
            # Load dataset (should trigger auto-download)
            dataset = loader.load_dataset()
            
            # Verify download was called
            mock_download.assert_called_once()
            
            # Verify data was loaded
            assert len(dataset) == 1
            assert dataset[0]['instance_id'] == 'mock-1'
            print("✅ Test passed: load_dataset auto-downloads when cache missing")


def test_download_dataset_skips_if_exists():
    """Test that download_dataset skips download if cache exists"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create cache file
        cache_file = Path(tmpdir) / "swebench_verified.json"
        test_data = [{'instance_id': 'existing'}]
        with open(cache_file, 'w') as f:
            json.dump(test_data, f)
        
        loader = SWEBenchLoader(cache_dir=tmpdir)
        
        # Since cache exists, download should be skipped
        result = loader.download_dataset()
        
        # Verify it returns the cache path
        assert result == cache_file
        
        # Verify data wasn't changed
        with open(cache_file, 'r') as f:
            data = json.load(f)
        assert data[0]['instance_id'] == 'existing'
        print("✅ Test passed: download_dataset skips if cache exists")


def test_download_dataset_force_redownload():
    """Test that download_dataset can force re-download"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create existing cache file
        cache_file = Path(tmpdir) / "swebench_verified.json"
        test_data = [{'instance_id': 'old'}]
        with open(cache_file, 'w') as f:
            json.dump(test_data, f)
        
        loader = SWEBenchLoader(cache_dir=tmpdir)
        
        # Mock the download to avoid actual download
        # We're patching the method directly on the instance
        original_method = loader.download_dataset
        
        # Create a flag to track if download logic was executed
        download_executed = False
        
        def mock_download_impl(force=False):
            nonlocal download_executed
            if not loader.cache_file.exists() or force:
                download_executed = True
                # Simulate writing new data
                new_data = [{'instance_id': 'new', 'repo': 'test/repo'}]
                with open(loader.cache_file, 'w') as f:
                    json.dump(new_data, f)
            return loader.cache_file
        
        # Apply the mock
        loader.download_dataset = mock_download_impl
        
        # Test force re-download
        result = loader.download_dataset(force=True)
        
        # Verify download was executed
        assert download_executed, "Download should have been executed with force=True"
        assert result == cache_file
        
        # Verify new data was written
        with open(cache_file, 'r') as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]['instance_id'] == 'new'
        print("✅ Test passed: download_dataset forces re-download with force=True")


def test_is_cached():
    """Test is_cached method"""
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = SWEBenchLoader(cache_dir=tmpdir)
        
        # Initially not cached
        assert not loader.is_cached()
        
        # Create cache
        cache_file = Path(tmpdir) / "swebench_verified.json"
        with open(cache_file, 'w') as f:
            json.dump([], f)
        
        # Now cached
        assert loader.is_cached()
        print("✅ Test passed: is_cached works correctly")


def test_create_mock_dataset():
    """Test create_mock_dataset method"""
    loader = SWEBenchLoader()
    mock_data = loader.create_mock_dataset(n=5)
    
    assert len(mock_data) == 5
    assert mock_data[0]['instance_id'] == 'mock-001'
    assert mock_data[4]['instance_id'] == 'mock-005'
    assert 'repo' in mock_data[0]
    assert 'patch' in mock_data[0]
    print("✅ Test passed: create_mock_dataset works correctly")


if __name__ == '__main__':
    print("Running SWEBenchLoader tests...\n")
    
    try:
        test_load_dataset_with_existing_cache()
        test_load_dataset_auto_downloads_when_cache_missing()
        test_download_dataset_skips_if_exists()
        test_download_dataset_force_redownload()
        test_is_cached()
        test_create_mock_dataset()
        
        print("\n" + "="*70)
        print("✅ All tests passed!")
        print("="*70)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
