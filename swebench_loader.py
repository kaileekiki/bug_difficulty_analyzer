#!/usr/bin/env python3
"""
Hugging Face에서 SWE-bench Verified 데이터셋 로드
"""

import json
from pathlib import Path
from typing import List, Dict, Any

class SWEBenchLoader:
    """
    Loader for SWE-bench Verified dataset from Hugging Face.
    
    Features:
    - Auto-downloads dataset on first use
    - Caches dataset locally as JSON
    - Reuses cache on subsequent runs
    
    Usage:
        loader = SWEBenchLoader(cache_dir="datasets")
        dataset = loader.load_dataset()  # Auto-downloads if needed
    """
    
    def __init__(self, cache_dir: str = "datasets", dataset_dir: str = None):
        """
        Args:
            cache_dir: 캐시 디렉토리 (기본값: "datasets")
            dataset_dir: 레거시 호환성을 위한 파라미터 (cache_dir와 동일)
        """
        # dataset_dir이 제공되면 우선 사용 (하위 호환성)
        if dataset_dir is not None:
            cache_dir = dataset_dir
            
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "swebench_verified.json"
    
    def download_dataset(self, force: bool = False) -> Path:
        """Download SWE-bench Verified from Hugging Face"""
        if self.cache_file.exists() and not force:
            print(f"✅ Dataset already cached: {self.cache_file}")
            return self.cache_file
        
        print("=" * 70)
        print("📥 Downloading SWE-bench Verified from Hugging Face...")
        print(f"   This may take 2-5 minutes on first run")
        print(f"   Cache location: {self.cache_file}")
        print("=" * 70)
        
        try:
            from datasets import load_dataset
            
            # Load from Hugging Face
            print("🔄 Fetching dataset from princeton-nlp/SWE-bench_Verified...")
            dataset = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
            
            print(f"✅ Downloaded {len(dataset)} instances")
            
            # Convert to list of dicts
            print("🔄 Converting to JSON format...")
            data = [dict(item) for item in dataset]
            
            # Save to cache
            print(f"💾 Saving to cache: {self.cache_file}")
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            file_size_mb = self.cache_file.stat().st_size / 1024 / 1024
            print(f"✅ Cache saved successfully")
            print(f"📊 File size: {file_size_mb:.2f} MB")
            print("=" * 70)
            
            return self.cache_file
            
        except ImportError:
            print("❌ ERROR: 'datasets' library not installed")
            print("   Install with: pip install datasets")
            raise
        except Exception as e:
            print(f"❌ Download failed: {e}")
            print("\n💡 Alternative: Manual download")
            print("   https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified")
            raise
    
    def load_dataset(self) -> List[Dict[str, Any]]:
        """
        Load SWE-bench dataset from cache or download if needed.
        
        Returns:
            List of dataset instances
        """
        # Auto-download if cache doesn't exist
        if not self.cache_file.exists():
            print(f"📥 Dataset cache not found, downloading automatically...")
            self.download_dataset()
        
        print(f"📂 Loading dataset from: {self.cache_file}")
        with open(self.cache_file, encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Loaded {len(data)} instances")
        return data
    
    def get_cache_path(self) -> Path:
        """캐시 파일 경로 반환"""
        return self.cache_file
    
    def is_cached(self) -> bool:
        """캐시 파일이 존재하는지 확인"""
        return self.cache_file.exists()
    
    def create_mock_dataset(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Create mock dataset for testing.
        
        Args:
            n: Number of mock instances
            
        Returns:
            List of mock instances
        """
        mock_instances = []
        
        for i in range(n):
            mock_instances.append({
                'instance_id': f'mock-{i+1:03d}',
                'repo': 'https://github.com/octocat/Hello-World',
                'base_commit': 'master',
                'patch': f"""
diff --git a/test_{i}.py b/test_{i}.py
index 1234567..abcdefg 100644
--- a/test_{i}.py
+++ b/test_{i}.py
@@ -1,3 +1,4 @@
+# Modified line {i}
 def test_{i}():
     pass
""",
                'problem_statement': f'Mock problem statement {i}'
            })
        
        return mock_instances