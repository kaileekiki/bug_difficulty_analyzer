# 🚀 13개 Metrics 출력 - 사용 가이드

## 📦 압축 해제

```bash
tar -xzf bug_analyzer_production.tar.gz
cd bug_difficulty_analyzer
```

## ✅ 바로 실행

```bash
python3 output_13_metrics.py
```

## 📊 출력 예시

```
[1] AST-GED
----------------------------------------------------------------------
  ast_ged: 26
  ast_size_before: 23
  ast_size_after: 49
  ast_size_delta: 26
  normalized_ged: 0.5306

[2] DFG-GED ⭐ (Main Hypothesis)
----------------------------------------------------------------------
  dfg_ged: 4.5000
  dfg_nodes_before: 8
  dfg_nodes_after: 10
  dfg_edges_before: 4
  dfg_edges_after: 5
  dfg_normalized: 0.4500
  dfg_def_use_chains_before: 8
  dfg_def_use_chains_after: 10
  method: beam_search
  beam_width: 10

[3] PDG-GED
----------------------------------------------------------------------
  pdg_ged: 4.5000
  pdg_nodes_before: 12
  pdg_nodes_after: 14
  pdg_edges_before: 7
  pdg_edges_after: 8
  pdg_normalized: 0.3214
  method: cfg+dfg_approximation

... (계속 13개까지)
```

## 🔧 자신의 패치로 수정

### 방법 1: 파일 직접 수정

```bash
# 파일 열기
nano output_13_metrics.py

# patch 변수 찾아서 수정 (line 200 근처)
patch = """
diff --git a/your_file.py b/your_file.py
--- a/your_file.py
+++ b/your_file.py
@@ -1,2 +1,3 @@
 # 여기에 자신의 git diff 붙여넣기
"""

# 저장 후 실행
python3 output_13_metrics.py
```

### 방법 2: Python에서 import

```python
from output_13_metrics import format_metric_output
from production_analyzer import ProductionBugAnalyzer

# 자신의 patch
my_patch = """
diff --git a/code.py b/code.py
...
"""

# 분석
analyzer = ProductionBugAnalyzer(beam_width=10)
result = analyzer.analyze_patch(my_patch, "my-bug-id")

# 13개 metrics 출력
format_metric_output(result)
```

## 📁 출력 파일

실행하면 2가지 출력:

1. **화면 출력**: 13개 metrics 모두 표시
2. **JSON 파일**: `metrics_output.json` (전체 데이터)

## 🎯 GED 재계산

나중에 더 나은 GED 계산 방법을 찾으면:

```python
import json

# JSON 로드
with open('metrics_output.json', 'r') as f:
    data = json.load(f)

# GED 계산 요소 추출
dfg_data = data['metrics']['aggregated']['graph']['DFG_GED'][0]

nodes_before = dfg_data['dfg_nodes_before']
nodes_after = dfg_data['dfg_nodes_after']
edges_before = dfg_data['dfg_edges_before']
edges_after = dfg_data['dfg_edges_after']

# 새로운 GED 계산 방법 적용
new_ged = your_new_calculation(nodes_before, nodes_after, 
                                edges_before, edges_after)
```

## 📊 13개 Metrics 리스트

1. **AST-GED** - Abstract Syntax Tree
2. **DFG-GED** ⭐ - Data Flow Graph (Main Hypothesis!)
3. **PDG-GED** - Program Dependence Graph
4. **LOC** - Lines of Code
5. **Token Edit Distance** - Lexical changes
6. **CFG-GED** - Control Flow Graph
7. **Cyclomatic Complexity** - Decision points
8. **Halstead Difficulty** - Operator/operand complexity
9. **CPG-GED** - Code Property Graph
10. **Call Graph-GED** - Function calls
11. **Variable Scope Change** - Scope transitions
12. **Type Change Complexity** - Type annotations
13. **Exception Handling Change** - Try-except modifications

## 🔍 GED 계산 요소 (모두 포함!)

각 GED metric마다:
- `*_ged`: GED 값
- `nodes_before`: Before 노드 수
- `nodes_after`: After 노드 수
- `edges_before`: Before 엣지 수
- `edges_after`: After 엣지 수
- `normalized`: Normalized GED
- `method`: 계산 방법

## ⚙️ 설정 변경

**Beam width 조절** (속도 vs 정확도):

```python
# 빠르게 (k=1)
analyzer = ProductionBugAnalyzer(beam_width=1)

# 기본 (k=10) - 추천
analyzer = ProductionBugAnalyzer(beam_width=10)

# 정확하게 (k=20)
analyzer = ProductionBugAnalyzer(beam_width=20)
```

## ✅ 완료!

```bash
python3 output_13_metrics.py
```

**출력:**
- 화면에 13개 metrics
- `metrics_output.json` 파일 생성
- 모든 GED 계산 요소 포함!
