# 🚀 실행 가이드 - 초간단 버전

## ✅ 즉시 실행 (3단계)

### 1️⃣ 압축 해제
```bash
tar -xzf bug_analyzer_production.tar.gz
cd bug_difficulty_analyzer
```

### 2️⃣ 테스트 (하나만 실행)
```bash
# Option A: 가장 간단 (추천!)
python3 simple_example.py

# Option B: 비교 분석
python3 compare_dfg.py

# Option C: 전체 예시
python3 examples.py
```

### 3️⃣ 자신의 코드로 사용
```bash
# 템플릿 복사
cp template.py my_analysis.py

# 편집
nano my_analysis.py  # 또는 vim, code 등

# 실행
python3 my_analysis.py
```

---

## 📝 템플릿 수정 방법

**template.py 열기:**
```python
patch = """
# 여기에 자신의 git diff 붙여넣기!
"""
```

**예시:**
```python
patch = """
diff --git a/my_code.py b/my_code.py
--- a/my_code.py
+++ b/my_code.py
@@ -10,3 +10,5 @@
 def process(data):
+    if not data:
+        return None
     return data * 2
"""
```

---

## 🎯 결과 확인

실행 후 나오는 값:
```
DFG-GED: 4.50          ← 메인 metric (클수록 어려움)
Method: beam_search    ← 사용된 알고리즘
Beam width: 10         ← 정확도 설정
```

**해석:**
- DFG-GED < 5: 쉬운 버그
- DFG-GED 5-15: 중간 난이도
- DFG-GED > 15: 어려운 버그

---

## 🔍 파일 목록

```
bug_difficulty_analyzer/
├── simple_example.py       ⭐ 가장 간단한 예시 (바로 실행!)
├── template.py             ⭐ 복사해서 수정 (자신의 패치)
├── compare_dfg.py          📊 DFG 비교
├── examples.py             📚 5가지 예시
├── production_analyzer.py  🚀 메인 analyzer
├── quickstart.py           ⚡ 빠른 시작
└── README_PRODUCTION.md    📖 완전한 문서
```

---

## ⚡ 빠른 참고

### 성능 조절
```python
# 빠르게 (k=1)
analyzer = ProductionBugAnalyzer(beam_width=1)

# 기본 (k=10) - 추천
analyzer = ProductionBugAnalyzer(beam_width=10)

# 정확하게 (k=20)
analyzer = ProductionBugAnalyzer(beam_width=20)
```

### 여러 패치 분석
```python
patches = [
    {'instance_id': 'bug-1', 'patch_text': patch1},
    {'instance_id': 'bug-2', 'patch_text': patch2},
]

results = analyzer.analyze_dataset(
    patches,
    output_path='results.json'
)
```

### JSON 결과 저장
```python
import json

with open('my_results.json', 'w') as f:
    json.dump(result, f, indent=2)
```

---

## ❓ 문제 해결

### "No such file or directory"
→ `cd bug_difficulty_analyzer` 했는지 확인

### "ModuleNotFoundError"
→ `python3 simple_example.py` (python3 사용!)

### 느린 실행
→ `beam_width=1` 로 변경

---

## ✨ 완료!

```bash
# 최종 확인
python3 simple_example.py

# 출력:
# DFG-GED: 1.50
# Method: beam_search
# Beam width: 10
# ✓ Results saved to results.json
```

**이제 자신의 버그를 분석하세요!** 🎉
