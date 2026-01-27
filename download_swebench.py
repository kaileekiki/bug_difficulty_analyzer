#!/usr/bin/env python3
"""
SWE-bench Verified 데이터셋 다운로드
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from swebench_loader import SWEBenchLoader

def main():
    print("=" * 70)
    print("SWE-BENCH VERIFIED 데이터셋 다운로드")
    print("=" * 70)
    print()
    
    loader = SWEBenchLoader()
    
    # 이미 캐시되어 있는지 확인
    if loader.is_cached():
        print("⚠️  데이터셋 파일이 이미 존재합니다.")
        response = input("다시 다운로드하시겠습니까? (y/N): ").strip().lower()
        force = response == 'y'
    else:
        force = False
    
    try:
        # 다운로드
        dataset_file = loader.download_dataset(force=force)
        
        print()
        print("=" * 70)
        
        # 로드 및 검증
        data = loader.load_dataset()
        
        print()
        print("✅ 다운로드 성공!")
        print(f"📁 파일: {dataset_file}")
        print(f"📊 총 인스턴스: {len(data)}개")
        
        # 처음 3개 인스턴스 확인
        print()
        print("📋 처음 3개 인스턴스:")
        for i, inst in enumerate(data[:3], 1):
            instance_id = inst.get('instance_id', 'N/A')
            repo = inst.get('repo', 'N/A')
            patch_len = len(inst.get('patch', ''))
            problem_len = len(inst.get('problem_statement', ''))
            
            print(f"\n  {i}. {instance_id}")
            print(f"     저장소: {repo}")
            print(f"     패치 길이: {patch_len} 문자")
            print(f"     문제 설명: {problem_len} 문자")
        
        print()
        print("=" * 70)
        print("✅ 준비 완료!")
        print()
        print("다음 단계:")
        print("  python3 run_swebench_analysis.py --limit 10")
        print("=" * 70)
        
        return 0
        
    except ImportError:
        print()
        print("=" * 70)
        print("❌ 필수 라이브러리 누락")
        print("=" * 70)
        print()
        print("다음 명령어로 설치하세요:")
        print("  pip install datasets")
        print()
        return 1
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ 다운로드 실패")
        print("=" * 70)
        print()
        print(f"오류: {e}")
        print()
        print("💡 수동 다운로드 방법:")
        print("  1. https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified")
        print("  2. 데이터셋 다운로드")
        print("  3. datasets/swebench_verified.json 으로 저장")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())