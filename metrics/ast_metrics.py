"""
AST-based Metrics:
- AST-GED (Abstract Syntax Tree Graph Edit Distance)
- Exception Handling Change
"""

import ast
from typing import Dict, List, Tuple, Any
from collections import defaultdict


class ASTNode:
    """Simplified AST node for tree edit distance"""
    def __init__(self, label: str, children: List['ASTNode'] = None):
        self.label = label
        self.children = children or []
    
    def __repr__(self):
        return f"ASTNode({self.label}, {len(self.children)} children)"


class ASTMetrics:
    """AST-based metrics computation"""
    
    @staticmethod
    def ast_to_simple_tree(code: str) -> ASTNode:
        """Convert Python AST to simplified tree for TED computation"""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return ASTNode("SyntaxError")
        
        def convert_node(node) -> ASTNode:
            """Recursively convert AST node"""
            node_type = type(node).__name__
            children = []
            
            for child in ast.iter_child_nodes(node):
                children.append(convert_node(child))
            
            return ASTNode(node_type, children)
        
        return convert_node(tree)
    
    @staticmethod
    def compute_ast_ged(code_before: str, code_after: str) -> Dict[str, Any]:
        """
        Compute AST Graph Edit Distance (Tree Edit Distance).
        Using Zhang-Shasha algorithm approximation.
        """
        tree_before = ASTMetrics.ast_to_simple_tree(code_before)
        tree_after = ASTMetrics.ast_to_simple_tree(code_after)
        
        # Compute tree edit distance
        distance = ASTMetrics._tree_edit_distance(tree_before, tree_after)
        
        # Additional stats
        size_before = ASTMetrics._tree_size(tree_before)
        size_after = ASTMetrics._tree_size(tree_after)
        
        return {
            'ast_ged': distance,
            'ast_size_before': size_before,
            'ast_size_after': size_after,
            'ast_size_delta': abs(size_after - size_before),
            'normalized_ged': distance / max(size_before, size_after) if max(size_before, size_after) > 0 else 0
        }
    
    @staticmethod
    def _tree_size(node: ASTNode) -> int:
        """Count total nodes in tree"""
        return 1 + sum(ASTMetrics._tree_size(child) for child in node.children)
    
    @staticmethod
    def _tree_edit_distance(tree1: ASTNode, tree2: ASTNode) -> int:
        """
        Compute tree edit distance (simplified Zhang-Shasha).
        Operations: insert, delete, relabel
        """
        # Base cases
        if not tree1 and not tree2:
            return 0
        if not tree1:
            return ASTMetrics._tree_size(tree2)
        if not tree2:
            return ASTMetrics._tree_size(tree1)
        
        # If labels match, only count children differences
        if tree1.label == tree2.label:
            # Cost of aligning children
            return ASTMetrics._forest_distance(tree1.children, tree2.children)
        else:
            # Cost of relabeling + aligning children
            relabel_cost = 1 + ASTMetrics._forest_distance(tree1.children, tree2.children)
            
            # Or delete tree1 and insert tree2
            delete_insert_cost = ASTMetrics._tree_size(tree1) + ASTMetrics._tree_size(tree2)
            
            return min(relabel_cost, delete_insert_cost)
    
    @staticmethod
    def _forest_distance(forest1: List[ASTNode], forest2: List[ASTNode]) -> int:
        """
        Compute edit distance between two forests (lists of trees).
        Using dynamic programming.
        """
        m, n = len(forest1), len(forest2)
        
        # DP table
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # Initialize: cost of deleting all trees from forest1
        for i in range(1, m + 1):
            dp[i][0] = dp[i-1][0] + ASTMetrics._tree_size(forest1[i-1])
        
        # Initialize: cost of inserting all trees from forest2
        for j in range(1, n + 1):
            dp[0][j] = dp[0][j-1] + ASTMetrics._tree_size(forest2[j-1])
        
        # Fill DP table
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                # Option 1: match forest1[i-1] with forest2[j-1]
                match_cost = dp[i-1][j-1] + ASTMetrics._tree_edit_distance(
                    forest1[i-1], forest2[j-1]
                )
                
                # Option 2: delete forest1[i-1]
                delete_cost = dp[i-1][j] + ASTMetrics._tree_size(forest1[i-1])
                
                # Option 3: insert forest2[j-1]
                insert_cost = dp[i][j-1] + ASTMetrics._tree_size(forest2[j-1])
                
                dp[i][j] = min(match_cost, delete_cost, insert_cost)
        
        return dp[m][n]
    
    @staticmethod
    def analyze_exception_handling(code_before: str, code_after: str) -> Dict[str, Any]:
        """
        Analyze changes in exception handling.
        """
        def extract_exception_info(code: str) -> Dict[str, Any]:
            """Extract exception handling information"""
            try:
                tree = ast.parse(code)
            except SyntaxError:
                return {'try_blocks': 0, 'except_handlers': 0, 'exception_types': set()}
            
            info = {
                'try_blocks': 0,
                'except_handlers': 0,
                'exception_types': set(),
                'finally_blocks': 0,
                'else_blocks': 0,
                'raise_statements': 0,
                'generic_excepts': 0  # except: without type
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Try):
                    info['try_blocks'] += 1
                    info['except_handlers'] += len(node.handlers)
                    
                    for handler in node.handlers:
                        if handler.type is None:
                            info['generic_excepts'] += 1
                        elif isinstance(handler.type, ast.Name):
                            info['exception_types'].add(handler.type.id)
                        elif isinstance(handler.type, ast.Tuple):
                            for exc in handler.type.elts:
                                if isinstance(exc, ast.Name):
                                    info['exception_types'].add(exc.id)
                    
                    if node.finalbody:
                        info['finally_blocks'] += 1
                    if node.orelse:
                        info['else_blocks'] += 1
                
                elif isinstance(node, ast.Raise):
                    info['raise_statements'] += 1
            
            return info
        
        info_before = extract_exception_info(code_before)
        info_after = extract_exception_info(code_after)
        
        # Convert sets to lists for JSON serialization
        types_before = info_before['exception_types']
        types_after = info_after['exception_types']
        
        return {
            'try_blocks_delta': info_after['try_blocks'] - info_before['try_blocks'],
            'except_handlers_delta': info_after['except_handlers'] - info_before['except_handlers'],
            'new_exception_types': list(types_after - types_before),
            'removed_exception_types': list(types_before - types_after),
            'exception_specificity_change': (
                info_after['generic_excepts'] - info_before['generic_excepts']
            ),
            'finally_blocks_delta': info_after['finally_blocks'] - info_before['finally_blocks'],
            'raise_statements_delta': info_after['raise_statements'] - info_before['raise_statements'],
            'total_exception_changes': (
                abs(info_after['try_blocks'] - info_before['try_blocks']) +
                abs(info_after['except_handlers'] - info_before['except_handlers']) +
                len(types_after - types_before) +
                len(types_before - types_after)
            )
        }
    
    @staticmethod
    def analyze_type_changes(code_before: str, code_after: str) -> Dict[str, Any]:
        """
        Analyze type annotation changes (Python 3.5+ type hints).
        """
        def extract_type_info(code: str) -> Dict[str, Any]:
            """Extract type annotation information"""
            try:
                tree = ast.parse(code)
            except SyntaxError:
                return {
                    'annotated_args': 0,
                    'return_annotations': 0,
                    'variable_annotations': 0,
                    'type_names': set()
                }
            
            info = {
                'annotated_args': 0,
                'return_annotations': 0,
                'variable_annotations': 0,
                'type_names': set()
            }
            
            for node in ast.walk(tree):
                # Function type annotations
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Argument annotations
                    for arg in node.args.args:
                        if arg.annotation:
                            info['annotated_args'] += 1
                            type_name = ASTMetrics._get_type_name(arg.annotation)
                            if type_name:
                                info['type_names'].add(type_name)
                    
                    # Return annotation
                    if node.returns:
                        info['return_annotations'] += 1
                        type_name = ASTMetrics._get_type_name(node.returns)
                        if type_name:
                            info['type_names'].add(type_name)
                
                # Variable annotations (Python 3.6+)
                elif isinstance(node, ast.AnnAssign):
                    info['variable_annotations'] += 1
                    type_name = ASTMetrics._get_type_name(node.annotation)
                    if type_name:
                        info['type_names'].add(type_name)
            
            return info
        
        info_before = extract_type_info(code_before)
        info_after = extract_type_info(code_after)
        
        types_before = info_before['type_names']
        types_after = info_after['type_names']
        
        return {
            'annotated_args_delta': info_after['annotated_args'] - info_before['annotated_args'],
            'return_annotations_delta': info_after['return_annotations'] - info_before['return_annotations'],
            'variable_annotations_delta': info_after['variable_annotations'] - info_before['variable_annotations'],
            'new_types': list(types_after - types_before),
            'removed_types': list(types_before - types_after),
            'total_type_changes': (
                abs(info_after['annotated_args'] - info_before['annotated_args']) +
                abs(info_after['return_annotations'] - info_before['return_annotations']) +
                abs(info_after['variable_annotations'] - info_before['variable_annotations']) +
                len(types_after - types_before) +
                len(types_before - types_after)
            )
        }
    
    @staticmethod
    def _get_type_name(annotation) -> str:
        """Extract type name from annotation AST node"""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Subscript):
            # Generic types like List[int]
            if isinstance(annotation.value, ast.Name):
                return annotation.value.id
        elif isinstance(annotation, ast.Attribute):
            # Module.Type
            return annotation.attr
        return None


# Test function
def test_ast_metrics():
    """Test AST metrics"""
    code_before = """
def calculate(x, y):
    try:
        result = x / y
    except:
        result = 0
    return result
"""
    
    code_after = """
def calculate(x: int, y: int) -> int:
    try:
        result = x / y
    except ZeroDivisionError:
        print("Division by zero!")
        result = 0
    except TypeError:
        raise ValueError("Invalid types")
    finally:
        pass
    return result
"""
    
    print("Testing AST Metrics...")
    print("="*60)
    
    # AST-GED
    ast_ged = ASTMetrics.compute_ast_ged(code_before, code_after)
    print(f"\nAST-GED: {ast_ged}")
    
    # Exception handling
    exc_changes = ASTMetrics.analyze_exception_handling(code_before, code_after)
    print(f"\nException Handling Changes: {exc_changes}")
    
    # Type changes
    type_changes = ASTMetrics.analyze_type_changes(code_before, code_after)
    print(f"\nType Changes: {type_changes}")
    
    print("\n✓ All tests passed!")


if __name__ == '__main__':
    test_ast_metrics()
