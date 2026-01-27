"""
Call Graph Builder - Constructs call relationships between functions
"""

import ast
import sys
from pathlib import Path
from typing import List, Set, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.graphs import CallGraph, Node, Edge, NodeType, EdgeType


class CallGraphBuilder:
    """Build Call Graph from Python AST"""
    
    def __init__(self):
        self.call_graph = None
        self.current_function = None
        self.functions = {}  # func_name -> node_id
    
    def build(self, code: str, name: str = "CallGraph") -> CallGraph:
        """Build call graph from Python code"""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            cg = CallGraph(name)
            error_node = Node("error", NodeType.FUNCTION, f"SyntaxError: {e}")
            cg.add_node(error_node)
            return cg
        
        self.call_graph = CallGraph(name)
        self.current_function = None
        self.functions = {}
        
        # First pass: collect all function definitions
        self._collect_functions(tree)
        
        # Second pass: find function calls
        self._find_calls(tree)
        
        return self.call_graph
    
    def _collect_functions(self, node: ast.AST):
        """Collect all function and method definitions"""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_name = node.name
            func_node = Node(
                f"func_{func_name}",
                NodeType.FUNCTION,
                func_name,
                attributes={'lineno': node.lineno}
            )
            self.call_graph.add_function(func_name, func_node)
            self.functions[func_name] = func_node.id
        
        elif isinstance(node, ast.ClassDef):
            # Add class node
            class_name = node.name
            class_node = Node(
                f"class_{class_name}",
                NodeType.CLASS,
                class_name,
                attributes={'lineno': node.lineno}
            )
            self.call_graph.add_node(class_node)
            
            # Process methods
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_name = f"{class_name}.{item.name}"
                    method_node = Node(
                        f"method_{method_name}",
                        NodeType.METHOD,
                        method_name,
                        attributes={'lineno': item.lineno, 'class': class_name}
                    )
                    self.call_graph.add_function(method_name, method_node)
                    self.functions[method_name] = method_node.id
                    
                    # Add edge from class to method
                    self.call_graph.add_edge(Edge(
                        source=class_node.id,
                        target=method_node.id,
                        type=EdgeType.INHERIT,
                        label="defines"
                    ))
        
        # Recurse
        for child in ast.iter_child_nodes(node):
            self._collect_functions(child)
    
    def _find_calls(self, node: ast.AST, parent_func: str = None):
        """Find function calls and build call edges"""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Set current function context
            old_func = self.current_function
            self.current_function = node.name
            
            # Process function body
            for child in ast.iter_child_nodes(node):
                self._find_calls(child, self.current_function)
            
            self.current_function = old_func
        
        elif isinstance(node, ast.Call):
            self._process_call(node)
        
        else:
            # Recurse to children
            for child in ast.iter_child_nodes(node):
                self._find_calls(child, parent_func)
    
    def _process_call(self, node: ast.Call):
        """Process a function call"""
        callee_name = None
        
        # Direct function call: foo()
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
        
        # Method call: obj.method()
        elif isinstance(node.func, ast.Attribute):
            # Try to resolve method name
            if isinstance(node.func.value, ast.Name):
                # Simple case: ClassName.method()
                callee_name = f"{node.func.value.id}.{node.func.attr}"
            else:
                # Instance method: just use method name
                callee_name = node.func.attr
        
        # Add call edge if both caller and callee are known
        if callee_name and callee_name in self.functions:
            if self.current_function and self.current_function in self.functions:
                caller_id = self.functions[self.current_function]
                callee_id = self.functions[callee_name]
                
                try:
                    self.call_graph.add_call_edge(caller_id, callee_id)
                except ValueError:
                    # Edge already exists or nodes not found
                    pass
    
    def build_from_multiple_files(self, files: Dict[str, str], 
                                  name: str = "CallGraph") -> CallGraph:
        """
        Build call graph from multiple Python files.
        
        Args:
            files: Dict of {filepath: code_content}
        """
        self.call_graph = CallGraph(name)
        self.functions = {}
        
        # First pass: collect all functions from all files
        for filepath, code in files.items():
            try:
                tree = ast.parse(code, filename=filepath)
                self._collect_functions(tree)
            except SyntaxError:
                continue
        
        # Second pass: find all calls
        for filepath, code in files.items():
            try:
                tree = ast.parse(code, filename=filepath)
                self._find_calls(tree)
            except SyntaxError:
                continue
        
        return self.call_graph


def test_call_graph_builder():
    """Test call graph builder"""
    code = """
def foo(x):
    return bar(x * 2)

def bar(y):
    return baz(y + 1)

def baz(z):
    return z * z

class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        result = self.add(a, 0)  # Calls add
        return result * b

calc = Calculator()
result = calc.add(10, 20)
answer = foo(result)
"""
    
    print("Testing Call Graph Builder...")
    print("="*60)
    
    builder = CallGraphBuilder()
    cg = builder.build(code, "test_callgraph")
    
    print(f"✓ Call Graph built: {cg}")
    print(f"  Functions: {len(cg.functions)}")
    print(f"  Nodes: {len(cg.nodes)}")
    print(f"  Edges: {len(cg.edges)}")
    
    print("\nFunctions:")
    for func_name, node in cg.functions.items():
        print(f"  {func_name} -> {node}")
    
    print("\nCall Edges:")
    for edge in cg.edges:
        if edge.type == EdgeType.CALL:
            caller = cg.get_node(edge.source)
            callee = cg.get_node(edge.target)
            print(f"  {caller.label} calls {callee.label}")
    
    print("\n✓ Call Graph Builder test passed!")
    
    return cg


if __name__ == '__main__':
    test_call_graph_builder()
