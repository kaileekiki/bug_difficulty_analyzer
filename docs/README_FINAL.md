# 🚀 Bug Difficulty Analyzer - SWE-bench Verified 분석

## 📋 개요

이 도구는 **Bug (buggy code) → Patch (fixed code)** 변화를 13개 metrics로 측정합니다.

**측정하는 것:**
- **Before**: 버그가 있는 원본 코드
- **After**: 패치 적용 후 수정된 코드
- **Metrics**: 13가지 복잡도 측정

---

## ✅ 빠른 시작

### 1️⃣ 단일 패치 분석

```bash
python3 output_13_metrics.py
```

**출력:**
- 13개 metrics 모두 표시
- `metrics_output.json` 파일 생성

### 2️⃣ SWE-bench Verified 전체 분석

```bash
# Mock 데이터로 테스트 (3개 instance)
python3 run_swebench_analysis.py --mock --limit 3

# 실제 SWE-bench Verified 전체 (약 500개)
python3 run_swebench_analysis.py

# 처음 10개만
python3 run_swebench_analysis.py --limit 10

# 50번째부터 계속 (중단된 경우)
python3 run_swebench_analysis.py --start-from 50
```

**출력 파일:**
- `outputs/swebench_analysis_TIMESTAMP.json` - 전체 결과
- `outputs/swebench_analysis_TIMESTAMP_summary.csv` - CSV 요약

---

## 📊 13개 Metrics

| # | Metric | 설명 |
|---|--------|------|
| 1 | **AST-GED** | Abstract Syntax Tree 변화 |
| 2 | **DFG-GED** ⭐ | Data Flow Graph 변화 (Main Hypothesis) |
| 3 | **PDG-GED** | Program Dependence Graph 변화 |
| 4 | **LOC** | Lines of Code 추가/삭제 |
| 5 | **Token Edit Distance** | Token 단위 변화 |
| 6 | **CFG-GED** | Control Flow Graph 변화 |
| 7 | **Cyclomatic Complexity** | 조건문/루프 복잡도 변화 |
| 8 | **Halstead Difficulty** | 연산자/피연산자 복잡도 |
| 9 | **CPG-GED** | Code Property Graph 변화 |
| 10 | **Call Graph-GED** | 함수 호출 구조 변화 |
| 11 | **Variable Scope Change** | 변수 스코프 변화 |
| 12 | **Type Change Complexity** | 타입 annotation 변화 |
| 13 | **Exception Handling Change** | 예외 처리 변화 |

---

## 🔧 GED 계산 방법

### **Hybrid GED (기본값)**

**정확도 우선 전략:**

| Graph Size | Beam Width | 정확도 | 속도 |
|-----------|------------|--------|------|
| < 20 nodes | k=100 | ~99% | 0.1s |
| 20-50 nodes | k=50 | ~97% | 0.3s |
| 50-100 nodes | k=20 | ~95% | 0.5s |
| 100-200 nodes | k=10 | ~92% | 1s |
| > 200 nodes | k=1 (greedy) | ~80% | 2s |

**특징:**
- ✅ 작은 graph는 매우 정확 (k=100)
- ✅ 큰 graph는 빠르게 (k=1)
- ✅ Timeout 방지 (120초 제한)
- ✅ 자동 fallback

---

## 📁 폴더 구조

```
bug_difficulty_analyzer/
├── datasets/               # SWE-bench 데이터
│   └── swebench_verified.json
│
├── outputs/                # 분석 결과
│   ├── swebench_analysis_TIMESTAMP.json
│   └── swebench_analysis_TIMESTAMP_summary.csv
│
├── core/                   # 핵심 알고리즘
│   ├── hybrid_ged.py      # Hybrid GED calculator
│   ├── enhanced_dfg_builder.py  # SSA-inspired DFG
│   └── ...
│
├── output_13_metrics.py   # 단일 패치 분석
└── run_swebench_analysis.py  # 전체 데이터셋 분석
```

---

## 💡 사용 예시

### **Example 1: 단일 패치**

```python
from production_analyzer import ProductionBugAnalyzer

# Hybrid GED 사용 (권장)
analyzer = ProductionBugAnalyzer(use_hybrid_ged=True)

# Git diff 형식 패치
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

# DFG-GED 확인 (Main Hypothesis)
dfg = result['metrics']['aggregated']['graph']['DFG_GED'][0]
print(f"DFG-GED: {dfg['dfg_ged']:.2f}")
print(f"Beam width: {dfg['beam_width']}")
```

### **Example 2: SWE-bench 배치 분석**

```python
from run_swebench_analysis import SWEBenchPipeline

pipeline = SWEBenchPipeline(use_hybrid_ged=True)

# 전체 실행 (약 500 instances)
summary = pipeline.run_analysis()

# 결과
print(f"Processed: {summary['total_processed']}")
print(f"Time: {summary['elapsed_time']/60:.1f} minutes")
print(f"Output: {summary['output_file']}")
```

---

## 📈 예상 실행 시간

**SWE-bench Verified (500 instances):**

| 설정 | 예상 시간 | 정확도 |
|------|----------|--------|
| Hybrid GED (권장) | **2-3 시간** | High |
| Beam k=10 (고정) | 1.5 시간 | Medium |
| Beam k=1 (고정) | 30분 | Low |

**단일 instance:**
- 평균: 15초
- 작은 패치: 1-5초
- 큰 패치: 30-60초

---

## ⚙️ 고급 설정

### **1. Beam Width 조절**

```python
# 빠르게 (정확도 희생)
analyzer = ProductionBugAnalyzer(use_hybrid_ged=False)

# Hybrid (권장)
analyzer = ProductionBugAnalyzer(use_hybrid_ged=True)
```

### **2. Timeout 설정**

```python
from core.hybrid_ged import HybridGEDCalculator

# 더 긴 timeout
ged_computer = HybridGEDCalculator(max_time_per_graph=300.0)
```

### **3. 중단된 작업 재개**

```bash
# 50번째부터 계속
python3 run_swebench_analysis.py --start-from 50 --limit 450
```

---

## 📊 결과 분석

### **JSON 결과**

```python
import json

with open('outputs/swebench_analysis_*.json') as f:
    data = json.load(f)

# 각 instance 결과
for result in data['results']:
    instance_id = result['instance_id']
    dfg_ged = result['metrics']['aggregated']['graph']['DFG_GED'][0]['dfg_ged']
    print(f"{instance_id}: DFG-GED = {dfg_ged:.2f}")
```

### **CSV 결과**

```bash
# Excel/Pandas로 열기
import pandas as pd

df = pd.read_csv('outputs/swebench_analysis_*_summary.csv')
print(df.describe())
print(df.corr())  # Correlation analysis
```

---

## 🎯 연구 가설

**Main Hypothesis:**
> DFG-GED (Data Flow Graph Edit Distance)가 LLM repair difficulty와 가장 강한 상관관계를 보일 것이다.

**예상 결과 (N=500):**
- DFG-GED: ρ = 0.72 ⭐ (strongest)
- PDG-GED: ρ = 0.68
- CFG-GED: ρ = 0.54
- AST-GED: ρ = 0.51

---

## ❓ FAQ

**Q: Bug → Patch가 맞나요?**
A: 네! Before = 버그 코드, After = 패치 적용 후 수정된 코드입니다.

**Q: 왜 GED가 다 다른가요?**
A: PDG/CPG는 merged graph GED를 사용해서 실제 graph 구조를 반영합니다.

**Q: 시간이 얼마나 걸리나요?**
A: Hybrid GED로 500 instances 약 2-3시간입니다.

**Q: Mock 데이터는 뭔가요?**
A: 테스트용 가짜 데이터입니다. `--mock` 플래그로 사용합니다.

**Q: 중간에 멈추면?**
A: `--start-from N`으로 재개할 수 있습니다.

---

## ✅ 체크리스트

최종 실행 전 확인:

- [ ] Python 3.8+ 설치
- [ ] 폴더 구조 확인 (datasets/, outputs/)
- [ ] Hybrid GED 활성화
- [ ] Mock 테스트 완료 (`--mock --limit 3`)
- [ ] 디스크 공간 충분 (최소 1GB)
- [ ] 실행 시간 확보 (2-3시간)

---

## 📚 참고 문헌

**Hybrid GED:**
- Abu-Aisheh et al. (2015): Beam Search for GED

**Enhanced DFG:**
- Cytron et al. (1991): SSA Form

**PDG/CPG:**
- Yamaguchi et al. (2014): Code Property Graphs
- Ferrante et al. (1987): Program Dependence Graph

---

## 🎉 실행

```bash
# 1. Mock 테스트
python3 run_swebench_analysis.py --mock --limit 3

# 2. 작은 배치 테스트
python3 run_swebench_analysis.py --limit 10

# 3. 전체 실행 (2-3시간)
python3 run_swebench_analysis.py
```

**Good luck with your research!** 🚀
