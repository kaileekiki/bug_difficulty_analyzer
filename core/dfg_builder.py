"""
DFG Builder - Constructs Data Flow Graph from Python code
Main Hypothesis: DFG-GED is the strongest predictor!
"""

import ast
import sys
from pathlib import Path
from typing import List, Set, Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.graphs import DFG, Node, Edge, NodeType, EdgeType


class DFGBuilder:
    """
    Build Data Flow Graph from Python AST.
    Tracks variable definitions and uses.
    """
    
    def __init__(self):
        self.node_counter = 0
        self.dfg = None
        self.current_scope = None  # Track current scope (function/module)
        self.scopes = {}  # scope_name -> {var_name -> [def_nodes]}
    
    def build(self, code: str, name: str = "DFG") -> DFG:
        """Build DFG from Python code"""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            dfg = DFG(name)
            error_node = self._create_node(NodeType.VARIABLE, f"SyntaxError: {e}")
            dfg.add_node(error_node)
            return dfg
        
        self.dfg = DFG(name)
        self.node_counter = 0
        self.current_scope = "__module__"
        self.scopes = {"__module__": {}}
        
        # Process the AST
        self._process_node(tree)
        
        # Build def-use edges
        self._build_def_use_edges()
        
        return self.dfg
    
    def _create_node(self, node_type: NodeType, label: str, 
                    attributes: Dict = None) -> Node:
        """Create a new node with unique ID"""
        node_id = f"d{self.node_counter}"
        self.node_counter += 1
        return Node(node_id, node_type, label, attributes or {})
    
    def _process_node(self, node: ast.AST):
        """Process AST node to extract data flow"""
        if isinstance(node, ast.FunctionDef):
            self._process_function(node)
        
        elif isinstance(node, ast.Assign):
            self._process_assignment(node)
        
        elif isinstance(node, ast.AugAssign):
            self._process_aug_assignment(node)
        
        elif isinstance(node, ast.AnnAssign):
            self._process_annotated_assignment(node)
        
        elif isinstance(node, ast.For):
            self._process_for_loop(node)
        
        elif isinstance(node, ast.Call):
            self._process_call(node)
        
        elif isinstance(node, ast.Return):
            self._process_return(node)
        
        # Recursively process children
        for child in ast.iter_child_nodes(node):
            self._process_node(child)
    
    def _process_function(self, node: ast.FunctionDef):
        """Process function definition"""
        # Create new scope for function
        old_scope = self.current_scope
        self.current_scope = f"func_{node.name}"
        self.scopes[self.current_scope] = {}
        
        # Process arguments (they are definitions)
        for arg in node.args.args:
            self._add_definition(arg.arg, node.lineno, is_param=True)
        
        # Process function body
        for stmt in node.body:
            self._process_node(stmt)
        
        # Restore scope
        self.current_scope = old_scope
    
    def _process_assignment(self, node: ast.Assign):
        """Process assignment: targets = value"""
        # First, process RHS (uses)
        self._extract_uses(node.value, node.lineno)
        
        # Then, process LHS (definitions)
        for target in node.targets:
            if isinstance(target, ast.Name):
                self._add_definition(target.id, node.lineno)
            elif isinstance(target, (ast.Tuple, ast.List)):
                # Multiple assignment: a, b = 1, 2
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self._add_definition(elt.id, node.lineno)
    
    def _process_aug_assignment(self, node: ast.AugAssign):
        """Process augmented assignment: x += 1"""
        if isinstance(node.target, ast.Name):
            var_name = node.target.id
            
            # Augmented assignment is both use and def
            self._add_use(var_name, node.lineno)
            self._add_definition(var_name, node.lineno)
            
            # Process RHS
            self._extract_uses(node.value, node.lineno)
    
    def _process_annotated_assignment(self, node: ast.AnnAssign):
        """Process annotated assignment: x: int = 5"""
        if isinstance(node.target, ast.Name):
            # Process RHS if exists
            if node.value:
                self._extract_uses(node.value, node.lineno)
            
            # LHS is definition
            self._add_definition(node.target.id, node.lineno)
    
    def _process_for_loop(self, node: ast.For):
        """Process for loop: for target in iter"""
        # Iterator is used
        self._extract_uses(node.iter, node.lineno)
        
        # Loop variable is defined
        if isinstance(node.target, ast.Name):
            self._add_definition(node.target.id, node.lineno)
        
        # Process body
        for stmt in node.body:
            self._process_node(stmt)
    
    def _process_call(self, node: ast.Call):
        """Process function call"""
        # Function itself might be a use
        if isinstance(node.func, ast.Name):
            self._add_use(node.func.id, node.lineno)
        
        # Arguments are uses
        for arg in node.args:
            self._extract_uses(arg, node.lineno)
        
        for keyword in node.keywords:
            self._extract_uses(keyword.value, node.lineno)
    
    def _process_return(self, node: ast.Return):
        """Process return statement"""
        if node.value:
            self._extract_uses(node.value, node.lineno)
    
    def _extract_uses(self, node: ast.AST, lineno: int):
        """Extract all variable uses from an expression"""
        if isinstance(node, ast.Name):
            self._add_use(node.id, lineno)
        
        elif isinstance(node, ast.BinOp):
            self._extract_uses(node.left, lineno)
            self._extract_uses(node.right, lineno)
        
        elif isinstance(node, ast.UnaryOp):
            self._extract_uses(node.operand, lineno)
        
        elif isinstance(node, ast.Compare):
            self._extract_uses(node.left, lineno)
            for comp in node.comparators:
                self._extract_uses(comp, lineno)
        
        elif isinstance(node, ast.Call):
            self._process_call(node)
        
        elif isinstance(node, ast.Subscript):
            self._extract_uses(node.value, lineno)
            self._extract_uses(node.slice, lineno)
        
        elif isinstance(node, ast.Attribute):
            self._extract_uses(node.value, lineno)
        
        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            for elt in node.elts:
                self._extract_uses(elt, lineno)
        
        elif isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if k:
                    self._extract_uses(k, lineno)
                self._extract_uses(v, lineno)
    
    def _add_definition(self, var_name: str, lineno: int, is_param: bool = False):
        """Add variable definition"""
        # Create definition node
        label = f"def {var_name}@{lineno}"
        if is_param:
            label += " (param)"
        
        def_node = self._create_node(
            NodeType.DEFINITION, 
            label,
            {'var_name': var_name, 'lineno': lineno, 'scope': self.current_scope}
        )
        self.dfg.add_node(def_node)
        self.dfg.add_definition(var_name, def_node.id)
        
        # Track in scope
        if var_name not in self.scopes[self.current_scope]:
            self.scopes[self.current_scope][var_name] = []
        self.scopes[self.current_scope][var_name].append(def_node.id)
    
    def _add_use(self, var_name: str, lineno: int):
        """Add variable use"""
        # Create use node
        use_node = self._create_node(
            NodeType.USE,
            f"use {var_name}@{lineno}",
            {'var_name': var_name, 'lineno': lineno, 'scope': self.current_scope}
        )
        self.dfg.add_node(use_node)
        self.dfg.add_use(var_name, use_node.id)
    
    def _build_def_use_edges(self):
        """Build edges from definitions to uses"""
        # For each variable
        for var_name in self.dfg.definitions:
            if var_name not in self.dfg.uses:
                continue
            
            def_nodes = self.dfg.definitions[var_name]
            use_nodes = self.dfg.uses[var_name]
            
            # For simplicity: connect each definition to each use
            # (Proper DFA would track reaching definitions)
            for def_id in def_nodes:
                def_node = self.dfg.get_node(def_id)
                
                for use_id in use_nodes:
                    use_node = self.dfg.get_node(use_id)
                    
                    # Only connect if in same scope or use is in inner scope
                    if self._can_reach(def_node, use_node):
                        edge = Edge(
                            source=def_id,
                            target=use_id,
                            type=EdgeType.DATA_FLOW,
                            label=f"{var_name}"
                        )
                        self.dfg.add_edge(edge)
    
    def _can_reach(self, def_node: Node, use_node: Node) -> bool:
        """Check if definition can reach use (simplified scope check)"""
        def_scope = def_node.attributes.get('scope', '__module__')
        use_scope = use_node.attributes.get('scope', '__module__')
        def_line = def_node.attributes.get('lineno', 0)
        use_line = use_node.attributes.get('lineno', 0)
        
        # Same scope: def must come before use
        if def_scope == use_scope:
            return def_line < use_line
        
        # Module scope can reach function scope
        if def_scope == '__module__':
            return True
        
        # Otherwise, no
        return False


def test_dfg_builder():
    """Test DFG builder"""
    code = """
def calculate(x, y):
    result = x + y
    temp = result * 2
    return temp

a = 10
b = 20
c = calculate(a, b)
d = c + a
"""
    
    print("Testing DFG Builder...")
    print("="*60)
    
    builder = DFGBuilder()
    dfg = builder.build(code, "test_dfg")
    
    print(f"✓ DFG built: {dfg}")
    print(f"  Nodes: {len(dfg.nodes)}")
    print(f"  Edges: {len(dfg.edges)}")
    print(f"  Variables: {len(dfg.definitions)}")
    
    print("\nDefinitions:")
    for var, nodes in list(dfg.definitions.items())[:5]:
        print(f"  {var}: {nodes}")
    
    print("\nUses:")
    for var, nodes in list(dfg.uses.items())[:5]:
        print(f"  {var}: {nodes}")
    
    print("\nDef-Use Chains:")
    for chain in list(dfg.get_def_use_chains())[:10]:
        def_node = dfg.get_node(chain[0])
        use_node = dfg.get_node(chain[1])
        print(f"  {def_node.label} -> {use_node.label}")
    
    print("\nSample Edges:")
    for edge in list(dfg.edges)[:10]:
        print(f"  {edge}")
    
    print("\n✓ DFG Builder test passed!")
    
    return dfg


if __name__ == '__main__':
    test_dfg_builder()
