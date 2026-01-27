#!/usr/bin/env python3
"""
Hugging Face에서 SWE-bench Verified 데이터셋 로드
"""

import json
from pathlib import Path
from typing import List, Dict, Any

class SWEBenchLoader:
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
        """Hugging Face에서 SWE-bench Verified 다운로드"""
        if self.cache_file.exists() and not force:
            print(f"✅ 데이터셋이 이미 캐시됨: {self.cache_file}")
            return self.cache_file
        
        print("📥 Hugging Face에서 SWE-bench Verified 다운로드 중...")
        print(f"   저장 위치: {self.cache_file}")
        
        try:
            from datasets import load_dataset
            
            # Hugging Face에서 로드
            dataset = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
            
            print(f"✅ {len(dataset)}개 인스턴스 로드 완료")
            
            # dict 리스트로 변환
            data = [dict(item) for item in dataset]
            
            # 캐시에 저장
            print("💾 JSON 파일로 저장 중...")
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            file_size_mb = self.cache_file.stat().st_size / 1024 / 1024
            print(f"✅ 저장 완료: {self.cache_file}")
            print(f"📊 파일 크기: {file_size_mb:.2f} MB")
            
            return self.cache_file
            
        except ImportError:
            print("❌ 'datasets' 라이브러리가 없습니다")
            print("   설치 명령어: pip install datasets")
            raise
        except Exception as e:
            print(f"❌ 다운로드 실패: {e}")
            print("\n💡 대안: 수동으로 다운로드")
            print("   https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified")
            raise
    
    def load_dataset(self) -> List[Dict[str, Any]]:
        """캐시된 데이터셋 로드"""
        if not self.cache_file.exists():
            raise FileNotFoundError(
                f"데이터셋을 찾을 수 없음: {self.cache_file}\n"
                f"먼저 download_dataset()을 실행하세요"
            )
        
        print(f"📂 데이터셋 로딩 중: {self.cache_file}")
        with open(self.cache_file, encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ {len(data)}개 인스턴스 로드됨")
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