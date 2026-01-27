# Bug Difficulty Analyzer - 실행 가이드

## 📦 다운로드 & 설치

```bash
# 1. 압축 해제
tar -xzf bug_difficulty_analyzer_final.tar.gz
cd bug_difficulty_analyzer

# 2. 필요한 것: Python 3.12+ 만!
python3 --version  # 3.12 이상 확인
```

## 🚀 빠른 시작 (3가지 방법)

### 방법 1: 예시 실행
```bash
# 5가지 사용 예시 실행 (가장 추천!)
python3 examples.py

# 출력:
# - Example 1: 간단한 코드 비교
# - Example 2: 기본 metrics
# - Example 3: DFG 상세 분석
# - Example 4: 전체 metrics 비교
# - Example 5: 실제 버그 시뮬레이션
```

### 방법 2: 빠른 시작 스크립트
```bash
python3 quickstart.py

# 4가지 사용 패턴:
# - 코드 버전 비교
# - 개별 metric 계산
# - 그래프 빌드
# - 패치 분석
```

### 방법 3: 직접 사용
```python
python3
>>> from metrics.graph_metrics import GraphMetrics
>>> 
>>> code_before = "def foo(x): return x + 1"
>>> code_after = "def foo(x): return x * 2"
>>> 
>>> metrics = GraphMetrics()
>>> results = metrics.compute_all_graph_metrics(code_before, code_after)
>>> 
>>> # Main Hypothesis Metric!
>>> print(results['DFG_GED']['dfg_ged'])
```

## 🧪 개별 컴포넌트 테스트

```bash
# 각 컴포넌트를 독립적으로 테스트
python3 core/graphs.py              # Graph 자료구조
python3 core/cfg_builder.py         # CFG Builder
python3 core/dfg_builder.py         # DFG Builder ⭐
python3 core/callgraph_builder.py   # Call Graph Builder
python3 core/ged_approximation.py   # GED Algorithm
python3 metrics/basic_metrics.py    # Basic Metrics
python3 metrics/ast_metrics.py      # AST Metrics
python3 metrics/graph_metrics.py    # Graph Metrics
python3 main.py                     # 전체 통합
```

## 📊 13개 Metrics 사용법

### Tier 1: Basic Metrics (5개)
```python
from metrics.basic_metrics import BasicMetrics

# LOC
loc = BasicMetrics.compute_loc(patch_diff)
print(f"Lines changed: {loc['modified']}")

# Token Edit Distance
token_dist = BasicMetrics.compute_token_edit_distance(code1, code2)
print(f"Token distance: {token_dist['token_distance']}")

# Cyclomatic Complexity
cc = BasicMetrics.compute_cyclomatic_delta(code1, code2)
print(f"Complexity change: {cc['delta_total']}")

# Halstead Difficulty
halstead = BasicMetrics.compute_halstead_delta(code1, code2)
print(f"Halstead Δ: {halstead['delta_difficulty']}")

# Variable Scope Changes
scope = BasicMetrics.analyze_variable_scope_changes(code1, code2)
print(f"Scope changes: {scope['total_scope_changes']}")
```

### Tier 2: AST Metrics (3개)
```python
from metrics.ast_metrics import ASTMetrics

# AST-GED
ast_ged = ASTMetrics.compute_ast_ged(code1, code2)
print(f"AST-GED: {ast_ged['ast_ged']}")

# Exception Handling
exceptions = ASTMetrics.analyze_exception_handling(code1, code2)
print(f"Exception changes: {exceptions['total_exception_changes']}")

# Type Changes
types = ASTMetrics.analyze_type_changes(code1, code2)
print(f"Type changes: {types['total_type_changes']}")
```

### Tier 3: Graph Metrics (5개) ⭐
```python
from metrics.graph_metrics import GraphMetrics

metrics = GraphMetrics()
results = metrics.compute_all_graph_metrics(code1, code2)

# Main Hypothesis Metric!
print(f"DFG-GED: {results['DFG_GED']['dfg_ged']}")

# Other graph metrics
print(f"CFG-GED: {results['CFG_GED']['cfg_ged']}")
print(f"PDG-GED: {results['PDG_GED']['pdg_ged']}")
print(f"Call Graph-GED: {results['Call_Graph_GED']['callgraph_ged']}")
print(f"CPG-GED: {results['CPG_GED']['cpg_ged']}")
```

## 🎯 Use Cases

### Use Case 1: 버그 난이도 예측
```python
from metrics.graph_metrics import GraphMetrics

# 버그 패치 분석
bug_code = "..."
fixed_code = "..."

metrics = GraphMetrics()
results = metrics.compute_all_graph_metrics(bug_code, fixed_code)

# Hypothesis: DFG-GED가 가장 강력한 predictor
dfg_ged = results['DFG_GED']['dfg_ged']
difficulty = "Hard" if dfg_ged > 10 else "Easy"
print(f"Predicted difficulty: {difficulty}")
```

### Use Case 2: 코드 변경 복잡도 측정
```python
from metrics.graph_metrics import GraphMetrics
from metrics.basic_metrics import BasicMetrics

# Before/After 코드
code_v1 = "..."
code_v2 = "..."

# 모든 metric 계산
graph_metrics = GraphMetrics()
graph_results = graph_metrics.compute_all_graph_metrics(code_v1, code_v2)

token_dist = BasicMetrics.compute_token_edit_distance(code_v1, code_v2)

# 종합 분석
print(f"Syntactic change: {token_dist['token_distance']}")
print(f"Semantic change: {graph_results['DFG_GED']['dfg_ged']}")
```

### Use Case 3: 그래프 시각화 준비
```python
from core.dfg_builder import DFGBuilder

code = "..."

# DFG 빌드
builder = DFGBuilder()
dfg = builder.build(code)

# 그래프 정보 추출
print(f"Nodes: {len(dfg.nodes)}")
print(f"Edges: {len(dfg.edges)}")

# 노드/엣지 정보 (시각화 도구로 전달 가능)
for node_id, node in dfg.nodes.items():
    print(f"{node_id}: {node.label}")

for edge in dfg.edges:
    print(f"{edge.source} -> {edge.target}")
```

## 🔍 트러블슈팅

### 문제: Import 에러
```bash
# 해결: 실행 디렉토리 확인
cd bug_difficulty_analyzer
python3 examples.py  # ✓ 올바름
python3 core/dfg_builder.py  # ✓ 올바름
```

### 문제: SyntaxError
```python
# 이유: Python 3.12+ 필요
python3 --version  # 3.12 이상 확인

# 해결: Python 업그레이드 또는
# Python 3.8+에서도 대부분 작동 (일부 기능 제한)
```

### 문제: 느린 실행
```python
# 큰 코드 파일 (>1000 lines)의 경우:
from core.ged_approximation import GEDApproximation

# Max iterations 조정
ged = GEDApproximation(max_iterations=1000)  # 기본 5000
```

## 📈 기대 성능

| 코드 크기 | DFG 빌드 | GED 계산 | 총 시간 |
|----------|----------|----------|---------|
| <100 lines | <0.1s | ~1s | ~1s |
| 100-500 lines | ~0.5s | ~5s | ~6s |
| 500-1000 lines | ~2s | ~20s | ~22s |
| >1000 lines | ~5s | ~60s (greedy) | ~65s |

## 📚 파일 구조

```
bug_difficulty_analyzer/
├── README.md              # 프로젝트 개요
├── quickstart.py          # 빠른 시작 가이드
├── examples.py            # 5가지 예시
├── main.py                # 메인 analyzer
│
├── core/                  # 핵심 엔진
│   ├── graphs.py          # 그래프 자료구조
│   ├── scope_extractor.py # Module-based scope
│   ├── cfg_builder.py     # CFG Builder
│   ├── dfg_builder.py     # DFG Builder ⭐
│   ├── callgraph_builder.py # Call Graph
│   └── ged_approximation.py # GED Algorithm
│
└── metrics/               # 13개 metrics
    ├── basic_metrics.py   # LOC, Token, CC, Halstead, Scope
    ├── ast_metrics.py     # AST-GED, Exception, Type
    └── graph_metrics.py   # CFG, DFG, PDG, Call, CPG
```

## ✅ 체크리스트

실행하기 전:
- [ ] Python 3.12+ 설치됨
- [ ] bug_difficulty_analyzer 디렉토리에 있음
- [ ] examples.py 실행 성공

개발에 사용:
- [ ] quickstart.py로 사용법 확인
- [ ] 개별 metrics 테스트 완료
- [ ] 자신의 코드에 적용

연구에 사용:
- [ ] 13개 metrics 이해
- [ ] DFG-GED main hypothesis 이해
- [ ] GED approximation 정당화 이해

## 🎓 다음 단계

1. **examples.py 실행** → 5가지 예시로 기능 이해
2. **quickstart.py 실행** → 4가지 사용 패턴 학습
3. **자신의 코드 분석** → 실제 버그/패치에 적용
4. **SWE-bench 통합** → 대규모 데이터셋 분석
5. **논문 작성** → ASE 2026 제출!

## 🙋 FAQ

**Q: 외부 라이브러리 필요한가요?**
A: 아니요! Python 표준 라이브러리만 사용합니다.

**Q: tree-sitter나 Joern 왜 안 쓰나요?**
A: Python의 `ast` 모듈이 Python 분석에 더 정확하고 빠릅니다.

**Q: GED는 exact algorithm인가요?**
A: 아니요, A* approximation입니다. 하지만 논문에서 정당화 가능합니다.

**Q: 어떤 Python 버전을 지원하나요?**
A: Python 3.8+ (권장: 3.12+)

**Q: 상업적으로 사용 가능한가요?**
A: 네, MIT License입니다.

## 📞 문의

- GitHub: (추후 업로드)
- Email: (your email)
- Paper: ASE 2026 submission

---

**행운을 빕니다! 🚀**
