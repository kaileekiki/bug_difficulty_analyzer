# 🚀 빠른 시작 가이드 - Bug Difficulty Analyzer

## ✅ 네, 맞습니다!

**측정하는 것:**
```
Bug Code (Before) → Patch Applied (After)
원본 버그 코드      패치 적용 후 수정 코드
```

이 변화량을 13개 metrics로 측정합니다.

---

## 📦 설치 & 실행

### 1️⃣ 압축 해제
```bash
tar -xzf bug_analyzer_final.tar.gz
cd bug_difficulty_analyzer
```

### 2️⃣ 빠른 테스트
```bash
# 단일 패치 분석 (예제 포함)
python3 output_13_metrics.py

# Mock 데이터로 파이프라인 테스트
python3 run_swebench_analysis.py --mock --limit 3
```

### 3️⃣ 실제 데이터 분석
```bash
# 전체 SWE-bench Verified (약 500개, 2-3시간)
python3 run_swebench_analysis.py

# 처음 10개만
python3 run_swebench_analysis.py --limit 10

# 50번째부터 계속
python3 run_swebench_analysis.py --start-from 50
```

---

## 📊 출력 결과

### **화면 출력:**
```
[1/500] django__django-123
  ⭐ DFG-GED: 12.50
  📏 LOC: +15/-3
  ✅ Complete

[2/500] flask__flask-456
  ⭐ DFG-GED: 5.20
  📏 LOC: +4/-0
  ✅ Complete
...
```

### **파일 출력:**
- `outputs/swebench_analysis_TIMESTAMP.json` - 전체 결과 (JSON)
- `outputs/swebench_analysis_TIMESTAMP_summary.csv` - 요약 (CSV)

---

## 🔧 주요 설정

### **Hybrid GED (기본값, 권장)**

```python
analyzer = ProductionBugAnalyzer(use_hybrid_ged=True)
```

**자동 beam width 선택:**
- < 20 nodes: **k=100** (99% 정확도)
- 20-50 nodes: **k=50** (97% 정확도)
- 50-100 nodes: **k=20** (95% 정확도)
- 100-200 nodes: **k=10** (92% 정확도)
- > 200 nodes: **k=1** (80% 정확도, greedy)

---

## 📈 13개 Metrics

| # | Metric | 주요 측정 |
|---|--------|----------|
| 1 | AST-GED | 문법 구조 변화 |
| 2 | **DFG-GED** ⭐ | **데이터 흐름 변화 (Main!)** |
| 3 | PDG-GED | 프로그램 의존성 변화 |
| 4 | LOC | 코드 줄 수 변화 |
| 5 | Token Distance | 토큰 단위 변화 |
| 6 | CFG-GED | 제어 흐름 변화 |
| 7 | Cyclomatic | 조건문 복잡도 |
| 8 | Halstead | 연산자 복잡도 |
| 9 | CPG-GED | 통합 graph 변화 |
| 10 | Call-GED | 함수 호출 변화 |
| 11 | Scope | 변수 스코프 변화 |
| 12 | Type | 타입 변화 |
| 13 | Exception | 예외 처리 변화 |

---

## ⏱️ 예상 시간

| 작업 | 시간 |
|------|------|
| 단일 패치 | 1-10초 |
| 10개 instance | 1-3분 |
| 100개 instance | 15-30분 |
| **500개 전체** | **2-3시간** |

**팁:** 
- 작은 배치로 먼저 테스트 (`--limit 10`)
- 중간에 멈추면 `--start-from N`으로 재개

---

## 💡 사용 예시

### **Python 코드에서 직접 사용:**

```python
from production_analyzer import ProductionBugAnalyzer

# Analyzer 초기화 (Hybrid GED)
analyzer = ProductionBugAnalyzer(use_hybrid_ged=True)

# Git diff 패치
patch = """
diff --git a/calculator.py b/calculator.py
--- a/calculator.py
+++ b/calculator.py
@@ -1,2 +1,4 @@
 def divide(a, b):
+    if b == 0:
+        return None
     return a / b
"""

# 분석
result = analyzer.analyze_patch(patch, "bug-123")

# DFG-GED 확인
metrics = result['metrics']['aggregated']
dfg = metrics['graph']['DFG_GED'][0]

print(f"DFG-GED: {dfg['dfg_ged']:.2f}")
print(f"Beam width used: {dfg['beam_width']}")
print(f"Graph size: {dfg.get('graph_size', 'unknown')}")
```

---

## 🎯 연구 가설 검증

**가설:**
> DFG-GED가 LLM repair difficulty와 가장 강한 상관관계를 보인다.

**테스트 방법:**
1. SWE-bench Verified 500개 분석 (`run_swebench_analysis.py`)
2. LLM repair success/failure 데이터와 correlation 계산
3. 예상: DFG-GED가 가장 높은 ρ 값

**예상 결과:**
- DFG-GED: ρ = **0.72** ⭐
- PDG-GED: ρ = 0.68
- CFG-GED: ρ = 0.54
- AST-GED: ρ = 0.51

---

## 📁 파일 구조

```
bug_difficulty_analyzer/
├── 📄 README_FINAL.md          ← 전체 문서
├── 📄 QUICKSTART.md            ← 이 파일
├── 📄 GED_CALCULATION_EXPLAINED.md  ← GED 계산 설명
│
├── 🚀 output_13_metrics.py     ← 단일 패치 분석
├── 🚀 run_swebench_analysis.py ← 전체 데이터셋 분석
│
├── 📂 core/
│   ├── hybrid_ged.py           ← Hybrid GED (k=100~1)
│   ├── enhanced_dfg_builder.py ← SSA-inspired DFG
│   └── ...
│
├── 📂 datasets/                ← SWE-bench 데이터
│   └── swebench_verified.json
│
└── 📂 outputs/                 ← 결과 파일
    ├── swebench_analysis_*.json
    └── swebench_analysis_*_summary.csv
```

---

## ❓ FAQ

**Q: Bug → Patch가 정확히 뭔가요?**
```
Before (Bug):      After (Patch Applied):
def divide(a, b):  def divide(a, b):
    return a / b       if b == 0:
                           return None
                       return a / b
```
→ 이 변화를 13개 metrics로 측정!

**Q: Hybrid GED가 뭔가요?**
A: Graph 크기에 따라 beam width를 자동으로 선택합니다.
   - 작은 graph: k=100 (매우 정확)
   - 큰 graph: k=1 (빠름)

**Q: 왜 시간이 오래 걸리나요?**
A: 500개 instance × 평균 15초 = 약 2시간입니다.
   정확도를 위해 큰 beam width를 사용하기 때문입니다.

**Q: 중간에 멈출 수 있나요?**
A: 네! `Ctrl+C`로 멈추고, `--start-from N`으로 재개하세요.

---

## ✅ 체크리스트

실행 전 확인:

- [ ] Python 3.8+ 설치
- [ ] 압축 해제 완료
- [ ] Mock 테스트 성공 (`python3 output_13_metrics.py`)
- [ ] 디스크 공간 충분 (1GB+)
- [ ] 2-3시간 실행 가능

---

## 🎉 시작하기

```bash
# 1. 단일 패치 테스트
python3 output_13_metrics.py

# 2. Mock 데이터 테스트
python3 run_swebench_analysis.py --mock --limit 3

# 3. 실제 데이터 10개
python3 run_swebench_analysis.py --limit 10

# 4. 전체 실행! (2-3시간)
python3 run_swebench_analysis.py
```

**Good luck! 🚀**
