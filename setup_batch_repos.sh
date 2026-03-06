#!/bin/bash
# 각 배치마다 독립적인 저장소 복사본 생성

set -e

NUM_BATCHES=28
REPO_CACHE="repo_cache"
BATCH_REPOS="batch_repos"

echo "=========================================="
echo "배치별 저장소 복사본 생성"
echo "=========================================="
echo "배치 수: $NUM_BATCHES"
echo ""

# 원본 저장소 확인
if [ ! -d "$REPO_CACHE" ]; then
    echo "❌ repo_cache가 없습니다. 먼저 ./pre_clone_repos.sh를 실행하세요."
    exit 1
fi

# 원본 저장소 목록
REPOS=$(ls -1 "$REPO_CACHE")
REPO_COUNT=$(echo "$REPOS" | wc -l)

echo "✓ 원본 저장소: $REPO_COUNT 개"
echo ""

# batch_repos 디렉토리 생성
mkdir -p "$BATCH_REPOS"

# 각 저장소에 대해
CURRENT_REPO=0
for REPO in $REPOS; do
    CURRENT_REPO=$((CURRENT_REPO + 1))
    
    echo "=========================================="
    echo "[$CURRENT_REPO/$REPO_COUNT] $REPO"
    echo "=========================================="
    
    # 각 배치에 대해 복사
    for BATCH_ID in $(seq 0 $((NUM_BATCHES - 1))); do
        BATCH_DIR="$BATCH_REPOS/batch$BATCH_ID"
        TARGET="$BATCH_DIR/$REPO"
        
        mkdir -p "$BATCH_DIR"
        
        # 이미 존재하는지 확인
        if [ -d "$TARGET" ]; then
            echo "  ✓ Batch $BATCH_ID: 이미 존재 (건너뜀)"
            continue
        fi
        
        echo "  📋 Batch $BATCH_ID: 복사 중..."
        
        # Hard link를 사용한 빠른 복사 (같은 파일시스템일 경우)
        # 실제 디스크 공간을 크게 절약하면서 독립적인 working tree 제공
        cp -al "$REPO_CACHE/$REPO" "$TARGET" 2>/dev/null || \
            cp -a "$REPO_CACHE/$REPO" "$TARGET"
        
        echo "  ✓ Batch $BATCH_ID: 완료"
    done
    echo ""
done

echo "=========================================="
echo "✅ 모든 배치별 저장소 준비 완료!"
echo "=========================================="
echo ""

# 디스크 사용량 확인
echo "📊 디스크 사용량:"
du -sh "$BATCH_REPOS"
echo ""

echo "📁 배치별 디렉토리:"
ls -lh "$BATCH_REPOS" | grep "^d"
echo ""

echo "🚀 이제 분석을 시작하세요:"
echo "   ./run_parallel_tmux.sh"
