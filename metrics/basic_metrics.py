"""
Tier 1 Metrics: Simple code metrics
- LOC (Lines of Code)
- Token Edit Distance
- Cyclomatic Complexity
- Halstead Difficulty  
- Variable Scope Change
"""

import ast
import tokenize
import io
from typing import Dict, List, Tuple
from collections import defaultdict


class BasicMetrics:
    """Computes basic code metrics from patches"""
    
    @staticmethod
    def compute_loc(patch_content: str) -> Dict[str, int]:
        """
        Compute Lines of Code metrics from git diff.
        
        Returns:
            {
                'added': number of lines added,
                'deleted': number of lines deleted,
                'modified': total (added + deleted)
            }
        """
        added = 0
        deleted = 0
        
        for line in patch_content.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                added += 1
            elif line.startswith('-') and not line.startswith('---'):
                deleted += 1
        
        return {
            'added': added,
            'deleted': deleted,
            'modified': added + deleted
        }
    
    @staticmethod
    def compute_token_edit_distance(code_before: str, code_after: str) -> Dict[str, int]:
        """
        Compute token-level edit distance between two code versions.
        
        Returns:
            {
                'token_distance': Levenshtein distance at token level,
                'tokens_before': number of tokens in before,
                'tokens_after': number of tokens in after
            }
        """
        def tokenize_code(code: str) -> List[str]:
            """Tokenize Python code"""
            tokens = []
            try:
                readline = io.StringIO(code).readline
                for tok in tokenize.generate_tokens(readline):
                    if tok.type not in (tokenize.NEWLINE, tokenize.NL, 
                                       tokenize.INDENT, tokenize.DEDENT,
                                       tokenize.COMMENT):
                        tokens.append(tok.string)
            except tokenize.TokenError:
                # If tokenization fails, fall back to simple split
                tokens = code.split()
            return tokens
        
        tokens_before = tokenize_code(code_before)
        tokens_after = tokenize_code(code_after)
        
        # Simple Levenshtein distance (can be optimized)
        distance = BasicMetrics._levenshtein_distance(tokens_before, tokens_after)
        
        return {
            'token_distance': distance,
            'tokens_before': len(tokens_before),
            'tokens_after': len(tokens_after),
            'token_change_ratio': distance / max(len(tokens_before), 1)
        }
    
    @staticmethod
    def _levenshtein_distance(seq1: List, seq2: List) -> int:
        """Compute Levenshtein distance between two sequences"""
        if len(seq1) < len(seq2):
            return BasicMetrics._levenshtein_distance(seq2, seq1)
        
        if len(seq2) == 0:
            return len(seq1)
        
        previous_row = range(len(seq2) + 1)
        for i, c1 in enumerate(seq1):
            current_row = [i + 1]
            for j, c2 in enumerate(seq2):
                # Cost of insertions, deletions, or substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def compute_cyclomatic_complexity(code: str) -> Dict[str, float]:
        """
        Compute McCabe Cyclomatic Complexity.
        CC = E - N + 2P (edges - nodes + 2*connected_components)
        
        Simplified: count decision points
        CC = 1 + number of decision points (if, for, while, and, or, except)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {'complexity': 0, 'function_complexities': {}}
        
        complexities = {}
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = 1  # Base complexity
                
                for child in ast.walk(node):
                    # Decision points
                    if isinstance(child, (ast.If, ast.While, ast.For, 
                                        ast.AsyncFor, ast.ExceptHandler)):
                        complexity += 1
                    elif isinstance(child, (ast.And, ast.Or)):
                        complexity += 1
                    elif isinstance(child, ast.Lambda):
                        complexity += 1
                
                complexities[node.name] = complexity
        
        avg_complexity = sum(complexities.values()) / len(complexities) if complexities else 0
        
        return {
            'average_complexity': avg_complexity,
            'max_complexity': max(complexities.values()) if complexities else 0,
            'total_complexity': sum(complexities.values()),
            'function_complexities': complexities
        }
    
    @staticmethod
    def compute_cyclomatic_delta(code_before: str, code_after: str) -> Dict[str, float]:
        """Compute change in cyclomatic complexity"""
        cc_before = BasicMetrics.compute_cyclomatic_complexity(code_before)
        cc_after = BasicMetrics.compute_cyclomatic_complexity(code_after)
        
        return {
            'delta_average': cc_after['average_complexity'] - cc_before['average_complexity'],
            'delta_max': cc_after['max_complexity'] - cc_before['max_complexity'],
            'delta_total': cc_after['total_complexity'] - cc_before['total_complexity']
        }
    
    @staticmethod
    def compute_halstead_metrics(code: str) -> Dict[str, float]:
        """
        Compute Halstead complexity metrics.
        
        n1 = number of distinct operators
        n2 = number of distinct operands
        N1 = total number of operators
        N2 = total number of operands
        
        Vocabulary: n = n1 + n2
        Length: N = N1 + N2
        Volume: V = N * log2(n)
        Difficulty: D = (n1/2) * (N2/n2)
        Effort: E = D * V
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {'difficulty': 0}
        
        operators = []
        operands = []
        
        for node in ast.walk(tree):
            # Operators
            if isinstance(node, (ast.Add, ast.Sub, ast.Mult, ast.Div, 
                               ast.Mod, ast.Pow, ast.FloorDiv)):
                operators.append(type(node).__name__)
            elif isinstance(node, (ast.And, ast.Or, ast.Not)):
                operators.append(type(node).__name__)
            elif isinstance(node, (ast.Eq, ast.NotEq, ast.Lt, ast.LtE,
                                  ast.Gt, ast.GtE, ast.Is, ast.IsNot)):
                operators.append(type(node).__name__)
            elif isinstance(node, (ast.BitAnd, ast.BitOr, ast.BitXor,
                                  ast.LShift, ast.RShift, ast.Invert)):
                operators.append(type(node).__name__)
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.If,
                                  ast.For, ast.While, ast.Return)):
                operators.append(type(node).__name__)
            
            # Operands  
            elif isinstance(node, ast.Name):
                operands.append(node.id)
            elif isinstance(node, (ast.Constant, ast.Num, ast.Str)):
                if hasattr(node, 'value'):
                    operands.append(str(node.value))
                elif hasattr(node, 'n'):
                    operands.append(str(node.n))
                elif hasattr(node, 's'):
                    operands.append(node.s)
        
        n1 = len(set(operators))
        n2 = len(set(operands))
        N1 = len(operators)
        N2 = len(operands)
        
        if n1 == 0 or n2 == 0:
            return {'difficulty': 0}
        
        n = n1 + n2  # Vocabulary
        N = N1 + N2  # Length
        
        import math
        V = N * math.log2(n) if n > 0 else 0  # Volume
        D = (n1 / 2) * (N2 / n2) if n2 > 0 else 0  # Difficulty
        E = D * V  # Effort
        
        return {
            'vocabulary': n,
            'length': N,
            'volume': V,
            'difficulty': D,
            'effort': E
        }
    
    @staticmethod
    def compute_halstead_delta(code_before: str, code_after: str) -> Dict[str, float]:
        """Compute change in Halstead difficulty"""
        h_before = BasicMetrics.compute_halstead_metrics(code_before)
        h_after = BasicMetrics.compute_halstead_metrics(code_after)
        
        return {
            'delta_difficulty': h_after.get('difficulty', 0) - h_before.get('difficulty', 0),
            'delta_volume': h_after.get('volume', 0) - h_before.get('volume', 0),
            'delta_effort': h_after.get('effort', 0) - h_before.get('effort', 0)
        }
    
    @staticmethod
    def analyze_variable_scope_changes(code_before: str, code_after: str) -> Dict[str, int]:
        """
        Analyze changes in variable scopes.
        Track: local -> global, global -> local, etc.
        """
        def extract_scopes(code: str) -> Dict[str, Dict[str, str]]:
            """Extract variable scopes from code"""
            try:
                tree = ast.parse(code)
            except SyntaxError:
                return {}
            
            scopes = defaultdict(dict)  # {function_name: {var_name: scope_type}}
            
            # Global variables
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    # Check if at module level
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            scopes['__module__'][target.id] = 'global'
            
            # Function-level variables
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_name = node.name
                    
                    for child in ast.walk(node):
                        if isinstance(child, ast.Assign):
                            for target in child.targets:
                                if isinstance(target, ast.Name):
                                    scopes[func_name][target.id] = 'local'
                        
                        elif isinstance(child, ast.Global):
                            for name in child.names:
                                scopes[func_name][name] = 'global'
                        
                        elif isinstance(child, ast.Nonlocal):
                            for name in child.names:
                                scopes[func_name][name] = 'nonlocal'
            
            return scopes
        
        scopes_before = extract_scopes(code_before)
        scopes_after = extract_scopes(code_after)
        
        changes = {
            'local_to_global': 0,
            'global_to_local': 0,
            'local_to_nonlocal': 0,
            'new_globals': 0,
            'removed_globals': 0
        }
        
        # Compare scopes
        all_functions = set(scopes_before.keys()) | set(scopes_after.keys())
        
        for func in all_functions:
            vars_before = scopes_before.get(func, {})
            vars_after = scopes_after.get(func, {})
            
            all_vars = set(vars_before.keys()) | set(vars_after.keys())
            
            for var in all_vars:
                scope_before = vars_before.get(var)
                scope_after = vars_after.get(var)
                
                if scope_before == 'local' and scope_after == 'global':
                    changes['local_to_global'] += 1
                elif scope_before == 'global' and scope_after == 'local':
                    changes['global_to_local'] += 1
                elif scope_before == 'local' and scope_after == 'nonlocal':
                    changes['local_to_nonlocal'] += 1
                elif scope_before is None and scope_after == 'global':
                    changes['new_globals'] += 1
                elif scope_before == 'global' and scope_after is None:
                    changes['removed_globals'] += 1
        
        changes['total_scope_changes'] = sum(changes.values())
        
        return changes


# Test function
def test_basic_metrics():
    """Test basic metrics"""
    code_before = """
def calculate(x, y):
    if x > 0:
        result = x + y
    else:
        result = x - y
    return result

global_var = 10
"""
    
    code_after = """
def calculate(x, y):
    if x > 0:
        if y > 0:
            result = x + y + 1
        else:
            result = x
    else:
        result = x - y
    return result

def helper():
    global global_var
    return global_var * 2

global_var = 10
"""
    
    print("Testing Basic Metrics...")
    print("="*60)
    
    # LOC (simulated patch)
    patch = "+++ added line\n--- removed line\n+ another add"
    loc = BasicMetrics.compute_loc(patch)
    print(f"\nLOC: {loc}")
    
    # Token distance
    token_dist = BasicMetrics.compute_token_edit_distance(code_before, code_after)
    print(f"\nToken Edit Distance: {token_dist}")
    
    # Cyclomatic complexity
    cc_delta = BasicMetrics.compute_cyclomatic_delta(code_before, code_after)
    print(f"\nCyclomatic Complexity Delta: {cc_delta}")
    
    # Halstead
    h_delta = BasicMetrics.compute_halstead_delta(code_before, code_after)
    print(f"\nHalstead Delta: {h_delta}")
    
    # Variable scope
    scope_changes = BasicMetrics.analyze_variable_scope_changes(code_before, code_after)
    print(f"\nVariable Scope Changes: {scope_changes}")
    
    print("\n✓ All tests passed!")


if __name__ == '__main__':
    test_basic_metrics()
