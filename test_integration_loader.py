#!/usr/bin/env python3
"""
Integration test for SWEBenchLoader with the analysis pipeline.
Tests the auto-download behavior in a realistic scenario.
"""

import tempfile
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from swebench_loader import SWEBenchLoader


def test_pipeline_integration():
    """
    Test that mimics how the analysis pipeline uses SWEBenchLoader.
    This simulates what happens in run_swebench_analysis_v3.py
    """
    print("="*70)
    print("Integration Test: Pipeline Usage Pattern")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\nUsing temporary dataset dir: {tmpdir}")
        
        # This is how the pipeline initializes the loader
        loader = SWEBenchLoader(dataset_dir=tmpdir)
        
        print(f"Cache file path: {loader.cache_file}")
        print(f"Cache exists before load: {loader.is_cached()}")
        
        # Mock the download to avoid actual download
        def mock_download():
            import json
            print("\n[Mocking download for test...]")
            print("=" * 70)
            print("📥 Downloading SWE-bench Verified from Hugging Face...")
            print(f"   This may take 2-5 minutes on first run")
            print(f"   Cache location: {loader.cache_file}")
            print("=" * 70)
            
            # Create realistic mock data
            mock_data = []
            for i in range(1, 11):
                mock_data.append({
                    'instance_id': f'test-instance-{i:03d}',
                    'repo': 'https://github.com/test/repo',
                    'base_commit': 'abc123',
                    'patch': f'mock patch {i}',
                    'problem_statement': f'Mock problem {i}'
                })
            
            print(f"✅ Downloaded {len(mock_data)} instances")
            print("🔄 Converting to JSON format...")
            print(f"💾 Saving to cache: {loader.cache_file}")
            
            with open(loader.cache_file, 'w') as f:
                json.dump(mock_data, f, indent=2, ensure_ascii=False)
            
            file_size_kb = loader.cache_file.stat().st_size / 1024
            print(f"✅ Cache saved successfully")
            print(f"📊 File size: {file_size_kb:.2f} KB")
            print("=" * 70)
            
            return loader.cache_file
        
        loader.download_dataset = mock_download
        
        # This is the key call from the pipeline
        print("\n--- Simulating pipeline's load_dataset() call ---")
        try:
            print("\nTrying to load dataset (no cache exists)...")
            dataset = loader.load_dataset()
            
            print(f"\n✅ SUCCESS: Auto-download triggered and completed")
            print(f"   Loaded {len(dataset)} instances")
            print(f"   First instance: {dataset[0]['instance_id']}")
            print(f"   Last instance: {dataset[-1]['instance_id']}")
            
            # Verify the structure
            required_fields = ['instance_id', 'repo', 'base_commit', 'patch', 'problem_statement']
            for field in required_fields:
                assert field in dataset[0], f"Missing required field: {field}"
            
            print(f"\n✅ All required fields present in dataset")
            
        except Exception as e:
            print(f"\n❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test subsequent load (should use cache)
        print("\n--- Testing subsequent load (should use cache) ---")
        dataset2 = loader.load_dataset()
        print(f"✅ Second load completed: {len(dataset2)} instances")
        
        assert len(dataset) == len(dataset2), "Second load returned different data"
        print("✅ Cache is being reused correctly")
        
    print("\n" + "="*70)
    print("✅ Integration test passed!")
    print("="*70)
    return True


def test_fallback_behavior():
    """
    Test what happens in the analysis pipeline when there's an error.
    This mimics the try-except in run_swebench_analysis_v3.py
    """
    print("\n" + "="*70)
    print("Integration Test: Error Fallback Behavior")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = SWEBenchLoader(dataset_dir=tmpdir)
        
        # Simulate a download failure
        def failing_download():
            raise Exception("Simulated network failure")
        
        loader.download_dataset = failing_download
        
        print("\nSimulating network failure during auto-download...")
        try:
            dataset = loader.load_dataset()
            print("❌ Should have raised an exception")
            return False
        except Exception as e:
            print(f"✅ Exception caught as expected: {type(e).__name__}")
            print(f"   Message: {str(e)}")
            
            # In the real pipeline, this would fall back to mock data
            print("\n💡 Pipeline would fall back to mock dataset here")
            mock_dataset = loader.create_mock_dataset(n=5)
            print(f"✅ Mock dataset created: {len(mock_dataset)} instances")
    
    print("\n" + "="*70)
    print("✅ Fallback behavior test passed!")
    print("="*70)
    return True


if __name__ == '__main__':
    print("\n" + "="*70)
    print("SWEBenchLoader Integration Tests")
    print("="*70)
    
    success = True
    
    try:
        if not test_pipeline_integration():
            success = False
        
        if not test_fallback_behavior():
            success = False
        
        if success:
            print("\n" + "="*70)
            print("🎉 All integration tests passed!")
            print("="*70)
        else:
            print("\n❌ Some integration tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
