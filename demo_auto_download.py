#!/usr/bin/env python3
"""
Manual demonstration of auto-download functionality.
This test shows the behavior with and without cache.
"""

import tempfile
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from swebench_loader import SWEBenchLoader


def demo_with_cache():
    """Demo when cache exists"""
    print("="*70)
    print("DEMO 1: Loading with existing cache")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = SWEBenchLoader(cache_dir=tmpdir)
        
        # Create a mock cache file
        import json
        mock_data = [
            {'instance_id': 'demo-001', 'repo': 'test/repo', 'patch': 'demo patch 1'},
            {'instance_id': 'demo-002', 'repo': 'test/repo', 'patch': 'demo patch 2'},
        ]
        with open(loader.cache_file, 'w') as f:
            json.dump(mock_data, f)
        
        # Load dataset - should use cache
        print("\nCalling load_dataset()...")
        dataset = loader.load_dataset()
        
        print(f"\nResult: Loaded {len(dataset)} instances from cache")
        print(f"First instance: {dataset[0]['instance_id']}")
    
    print("\n")


def demo_without_cache():
    """Demo when cache doesn't exist (simulated auto-download)"""
    print("="*70)
    print("DEMO 2: Loading without cache (auto-download simulation)")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = SWEBenchLoader(cache_dir=tmpdir)
        
        # Verify no cache exists
        print(f"\nCache exists: {loader.is_cached()}")
        
        # Override download to simulate without actual download
        original_download = loader.download_dataset
        
        def mock_download():
            print("\n[Simulating actual download from Hugging Face...]")
            print("=" * 70)
            print("📥 Downloading SWE-bench Verified from Hugging Face...")
            print(f"   This may take 2-5 minutes on first run")
            print(f"   Cache location: {loader.cache_file}")
            print("=" * 70)
            print("🔄 Fetching dataset from princeton-nlp/SWE-bench_Verified...")
            
            # Create mock downloaded data
            import json
            mock_data = [
                {'instance_id': f'downloaded-{i:03d}', 'repo': 'test/repo', 'patch': f'patch {i}'}
                for i in range(1, 6)
            ]
            
            print(f"✅ Downloaded {len(mock_data)} instances")
            print("🔄 Converting to JSON format...")
            print(f"💾 Saving to cache: {loader.cache_file}")
            
            with open(loader.cache_file, 'w') as f:
                json.dump(mock_data, f)
            
            file_size = loader.cache_file.stat().st_size / 1024
            print(f"✅ Cache saved successfully")
            print(f"📊 File size: {file_size:.2f} KB")
            print("=" * 70)
            
            return loader.cache_file
        
        loader.download_dataset = mock_download
        
        # Load dataset - should trigger auto-download
        print("\nCalling load_dataset()...")
        dataset = loader.load_dataset()
        
        print(f"\nResult: Loaded {len(dataset)} instances after auto-download")
        print(f"First instance: {dataset[0]['instance_id']}")
        print(f"Last instance: {dataset[-1]['instance_id']}")
    
    print("\n")


def demo_subsequent_load():
    """Demo subsequent loads use cache"""
    print("="*70)
    print("DEMO 3: Subsequent loads reuse cache")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = SWEBenchLoader(cache_dir=tmpdir)
        
        # Create initial cache
        import json
        mock_data = [
            {'instance_id': 'cached-001', 'repo': 'test/repo', 'patch': 'patch 1'},
            {'instance_id': 'cached-002', 'repo': 'test/repo', 'patch': 'patch 2'},
        ]
        with open(loader.cache_file, 'w') as f:
            json.dump(mock_data, f)
        
        # First load
        print("\n--- First load ---")
        dataset1 = loader.load_dataset()
        print(f"Loaded {len(dataset1)} instances")
        
        # Second load (should be faster, no download)
        print("\n--- Second load (should reuse cache) ---")
        dataset2 = loader.load_dataset()
        print(f"Loaded {len(dataset2)} instances")
        
        print("\n✅ Both loads used the same cache successfully")
    
    print("\n")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("SWEBenchLoader Auto-Download Feature Demo")
    print("="*70)
    print()
    
    demo_with_cache()
    demo_without_cache()
    demo_subsequent_load()
    
    print("="*70)
    print("Demo complete! All scenarios work as expected.")
    print("="*70)
