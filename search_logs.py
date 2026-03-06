#!/usr/bin/env python3
"""
로그 검색 및 분석 도구
"""

import sys
import re
import glob
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict
import argparse

class LogSearcher:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        
    def search(self, pattern: str, case_sensitive: bool = False, 
               context_lines: int = 0) -> List[Dict]:
        """로그에서 패턴 검색"""
        results = []
        flags = 0 if case_sensitive else re.IGNORECASE
        
        for log_file in sorted(self.log_dir.glob("*.log")):
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines):
                if re.search(pattern, line, flags):
                    context_before = []
                    context_after = []
                    
                    if context_lines > 0:
                        start = max(0, i - context_lines)
                        end = min(len(lines), i + context_lines + 1)
                        context_before = lines[start:i]
                        context_after = lines[i+1:end]
                    
                    results.append({
                        'file': str(log_file),
                        'line_num': i + 1,
                        'line': line.rstrip(),
                        'context_before': [l.rstrip() for l in context_before],
                        'context_after': [l.rstrip() for l in context_after]
                    })
        
        return results
    
    def find_errors(self) -> List[Dict]:
        """모든 에러 찾기"""
        return self.search(r'❌|ERROR|Error|error|failed|Failed')
    
    def find_instance(self, instance_id: str) -> List[Dict]:
        """특정 인스턴스 로그 찾기"""
        return self.search(instance_id, case_sensitive=True)
    
    def find_repo(self, repo_name: str) -> List[Dict]:
        """특정 저장소 관련 로그 찾기"""
        return self.search(repo_name, case_sensitive=False)
    
    def get_progress(self) -> Dict:
        """진행 상황 분석"""
        stats = {
            'total_analyzed': 0,
            'total_errors': 0,
            'errors_by_type': defaultdict(int),
            'by_batch': {},
            'by_repo': defaultdict(lambda: {'total': 0, 'errors': 0})
        }
        
        for log_file in self.log_dir.glob("*.log"):
            batch_name = log_file.stem
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 배치별 통계
            total_match = re.search(r'Total analyzed:\s*(\d+)', content)
            error_match = re.search(r'Total errors:\s*(\d+)', content)
            
            if total_match and error_match:
                total = int(total_match.group(1))
                errors = int(error_match.group(1))
                
                stats['total_analyzed'] += total
                stats['total_errors'] += errors
                stats['by_batch'][batch_name] = {
                    'total': total,
                    'errors': errors,
                    'success': total - errors
                }
            
            # 에러 유형별 분류
            if 'Checkout failed' in content:
                stats['errors_by_type']['Checkout failed'] += content.count('Checkout failed')
            if 'Clone failed' in content:
                stats['errors_by_type']['Clone failed'] += content.count('Clone failed')
            if 'Patch apply' in content:
                stats['errors_by_type']['Patch apply failed'] += content.count('Patch apply')
            
            # 저장소별 통계
            repo_pattern = r'Repository:\s*([^\s]+)'
            for match in re.finditer(repo_pattern, content):
                repo = match.group(1)
                stats['by_repo'][repo]['total'] += 1
                
            error_pattern = r'Repository:\s*([^\s]+).*?❌'
            for match in re.finditer(error_pattern, content, re.DOTALL):
                repo = match.group(1)
                stats['by_repo'][repo]['errors'] += 1
        
        return stats
    
    def get_successful_instances(self) -> List[str]:
        """성공한 인스턴스 목록"""
        successful = []
        
        for log_file in self.log_dir.glob("*.log"):
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 분석 완료된 인스턴스 찾기
            pattern = r'ANALYZING \(V3\):\s*([^\n]+).*?✅.*?Analysis complete'
            for match in re.finditer(pattern, content, re.DOTALL):
                instance = match.group(1).strip()
                successful.append(instance)
        
        return successful
    
    def get_failed_instances(self) -> List[Dict]:
        """실패한 인스턴스 목록 및 에러 원인"""
        failed = []
        
        for log_file in self.log_dir.glob("*.log"):
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 실패한 인스턴스 찾기
            pattern = r'ANALYZING \(V3\):\s*([^\n]+).*?❌.*?Instance had errors:\s*\[([^\]]+)\]'
            for match in re.finditer(pattern, content, re.DOTALL):
                instance = match.group(1).strip()
                error = match.group(2).strip()
                failed.append({
                    'instance': instance,
                    'error': error,
                    'file': str(log_file)
                })
        
        return failed


def print_search_results(results: List[Dict], max_results: int = 50):
    """검색 결과 출력"""
    if not results:
        print("❌ 검색 결과 없음")
        return
    
    print(f"\n✅ {len(results)}개 결과 발견")
    if len(results) > max_results:
        print(f"   (처음 {max_results}개만 표시)\n")
        results = results[:max_results]
    else:
        print()
    
    for i, result in enumerate(results, 1):
        print(f"{'='*70}")
        print(f"[{i}] {result['file']}:{result['line_num']}")
        print(f"{'='*70}")
        
        # Context before
        if result.get('context_before'):
            for line in result['context_before']:
                print(f"  {line}")
        
        # Matching line (highlight)
        print(f"▶ {result['line']}")
        
        # Context after
        if result.get('context_after'):
            for line in result['context_after']:
                print(f"  {line}")
        
        print()


def print_progress(stats: Dict):
    """진행 상황 출력"""
    print("\n" + "="*70)
    print("📊 전체 진행 상황")
    print("="*70)
    print(f"총 분석: {stats['total_analyzed']}")
    print(f"성공: {stats['total_analyzed'] - stats['total_errors']}")
    print(f"실패: {stats['total_errors']}")
    
    if stats['total_analyzed'] > 0:
        success_rate = (stats['total_analyzed'] - stats['total_errors']) / stats['total_analyzed'] * 100
        print(f"성공률: {success_rate:.1f}%")
    
    # 에러 유형별
    if stats['errors_by_type']:
        print(f"\n📋 에러 유형:")
        for error_type, count in sorted(stats['errors_by_type'].items(), 
                                       key=lambda x: x[1], reverse=True):
            print(f"  • {error_type}: {count}")
    
    # 배치별
    if stats['by_batch']:
        print(f"\n📦 배치별 상태:")
        for batch, data in sorted(stats['by_batch'].items()):
            success_rate = (data['success'] / data['total'] * 100) if data['total'] > 0 else 0
            status = "✅" if data['errors'] == 0 else "⚠️"
            print(f"  {status} {batch}: {data['success']}/{data['total']} ({success_rate:.0f}%)")
    
    # 저장소별
    if stats['by_repo']:
        print(f"\n🗂️  저장소별 상태:")
        for repo, data in sorted(stats['by_repo'].items(), 
                                key=lambda x: x[1]['errors'], reverse=True)[:10]:
            if data['total'] > 0:
                success_rate = ((data['total'] - data['errors']) / data['total'] * 100)
                status = "✅" if data['errors'] == 0 else "❌"
                print(f"  {status} {repo}: {data['total'] - data['errors']}/{data['total']} ({success_rate:.0f}%)")


def main():
    parser = argparse.ArgumentParser(description='SWE-bench 로그 검색 및 분석')
    parser.add_argument('--log-dir', default='logs', help='로그 디렉토리')
    
    subparsers = parser.add_subparsers(dest='command', help='명령어')
    
    # search 명령어
    search_parser = subparsers.add_parser('search', help='로그 검색')
    search_parser.add_argument('pattern', help='검색 패턴 (정규표현식)')
    search_parser.add_argument('-c', '--context', type=int, default=2, 
                              help='전후 컨텍스트 라인 수')
    search_parser.add_argument('-i', '--case-sensitive', action='store_true',
                              help='대소문자 구분')
    search_parser.add_argument('-n', '--max-results', type=int, default=50,
                              help='최대 결과 개수')
    
    # errors 명령어
    subparsers.add_parser('errors', help='모든 에러 찾기')
    
    # instance 명령어
    instance_parser = subparsers.add_parser('instance', help='특정 인스턴스 검색')
    instance_parser.add_argument('instance_id', help='인스턴스 ID')
    
    # repo 명령어
    repo_parser = subparsers.add_parser('repo', help='특정 저장소 검색')
    repo_parser.add_argument('repo_name', help='저장소 이름')
    
    # progress 명령어
    subparsers.add_parser('progress', help='진행 상황 보기')
    
    # success 명령어
    subparsers.add_parser('success', help='성공한 인스턴스 목록')
    
    # failed 명령어
    subparsers.add_parser('failed', help='실패한 인스턴스 목록')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    searcher = LogSearcher(args.log_dir)
    
    if args.command == 'search':
        results = searcher.search(args.pattern, args.case_sensitive, args.context)
        print_search_results(results, args.max_results)
        
    elif args.command == 'errors':
        results = searcher.find_errors()
        print_search_results(results, 100)
        
    elif args.command == 'instance':
        results = searcher.find_instance(args.instance_id)
        print_search_results(results, 100)
        
    elif args.command == 'repo':
        results = searcher.find_repo(args.repo_name)
        print_search_results(results, 100)
        
    elif args.command == 'progress':
        stats = searcher.get_progress()
        print_progress(stats)
        
    elif args.command == 'success':
        instances = searcher.get_successful_instances()
        print(f"\n✅ 성공한 인스턴스: {len(instances)}개\n")
        for inst in instances:
            print(f"  • {inst}")
            
    elif args.command == 'failed':
        failed = searcher.get_failed_instances()
        print(f"\n❌ 실패한 인스턴스: {len(failed)}개\n")
        for item in failed:
            print(f"  • {item['instance']}")
            print(f"    Error: {item['error']}")
            print(f"    Log: {item['file']}")
            print()


if __name__ == '__main__':
    main()
