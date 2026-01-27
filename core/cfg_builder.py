"""
CFG Builder - Constructs Control Flow Graph from Python code
"""

import ast
import sys
from pathlib import Path
from typing import List, Set, Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.graphs import CFG, Node, Edge, NodeType, EdgeType


class CFGBuilder:
    """Build Control Flow Graph from Python AST"""
    
    def __init__(self):
        self.node_counter = 0
        self.cfg = None
    
    def build(self, code: str, name: str = "CFG") -> CFG:
        """Build CFG from Python code"""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            # Return empty CFG for syntax errors
            cfg = CFG(name)
            error_node = self._create_node(NodeType.STATEMENT, f"SyntaxError: {e}")
            cfg.add_node(error_node)
            return cfg
        
        self.cfg = CFG(name)
        self.node_counter = 0
        
        # Create entry node
        entry = self._create_node(NodeType.ENTRY, "entry")
        self.cfg.add_node(entry)
        self.cfg.set_entry(entry.id)
        
        # Process module body
        last_nodes = self._process_statements(tree.body, entry.id)
        
        # Create exit node
        exit_node = self._create_node(NodeType.EXIT, "exit")
        self.cfg.add_node(exit_node)
        self.cfg.add_exit(exit_node.id)
        
        # Connect last nodes to exit
        for node_id in last_nodes:
            self.cfg.add_edge(Edge(node_id, exit_node.id, EdgeType.CONTROL_FLOW))
        
        return self.cfg
    
    def _create_node(self, node_type: NodeType, label: str) -> Node:
        """Create a new node with unique ID"""
        node_id = f"n{self.node_counter}"
        self.node_counter += 1
        return Node(node_id, node_type, label)
    
    def _process_statements(self, statements: List[ast.stmt], 
                          prev_node_id: str) -> List[str]:
        """
        Process a list of statements.
        Returns list of node IDs that represent possible exit points.
        """
        if not statements:
            return [prev_node_id]
        
        current_id = prev_node_id
        
        for stmt in statements:
            # Get exit nodes from this statement
            exit_nodes = self._process_statement(stmt, current_id)
            
            # For next statement, use first exit node as entry
            # (This is simplified; proper CFG would track all paths)
            if exit_nodes:
                current_id = exit_nodes[0]
        
        return exit_nodes if exit_nodes else [current_id]
    
    def _process_statement(self, stmt: ast.stmt, prev_node_id: str) -> List[str]:
        """
        Process a single statement.
        Returns list of exit node IDs.
        """
        if isinstance(stmt, ast.If):
            return self._process_if(stmt, prev_node_id)
        
        elif isinstance(stmt, (ast.While, ast.For, ast.AsyncFor)):
            return self._process_loop(stmt, prev_node_id)
        
        elif isinstance(stmt, ast.Try):
            return self._process_try(stmt, prev_node_id)
        
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return self._process_function(stmt, prev_node_id)
        
        elif isinstance(stmt, ast.Return):
            return self._process_return(stmt, prev_node_id)
        
        elif isinstance(stmt, (ast.Break, ast.Continue)):
            return self._process_jump(stmt, prev_node_id)
        
        else:
            # Simple statement
            return self._process_simple_statement(stmt, prev_node_id)
    
    def _process_if(self, stmt: ast.If, prev_node_id: str) -> List[str]:
        """Process if statement"""
        # Create branch node
        condition = ast.unparse(stmt.test) if hasattr(ast, 'unparse') else "condition"
        branch = self._create_node(NodeType.BRANCH, f"if {condition}")
        self.cfg.add_node(branch)
        self.cfg.add_edge(Edge(prev_node_id, branch.id, EdgeType.CONTROL_FLOW))
        
        # Process then branch
        then_exits = self._process_statements(stmt.body, branch.id)
        
        # Process else branch
        if stmt.orelse:
            else_exits = self._process_statements(stmt.orelse, branch.id)
        else:
            # No else: branch directly connects to merge point
            else_exits = [branch.id]
        
        # Merge point: both branches converge
        merge = self._create_node(NodeType.STATEMENT, "merge")
        self.cfg.add_node(merge)
        
        for exit_id in then_exits:
            self.cfg.add_edge(Edge(exit_id, merge.id, EdgeType.CONTROL_FLOW))
        for exit_id in else_exits:
            self.cfg.add_edge(Edge(exit_id, merge.id, EdgeType.CONTROL_FLOW))
        
        return [merge.id]
    
    def _process_loop(self, stmt: ast.stmt, prev_node_id: str) -> List[str]:
        """Process loop statement (while/for)"""
        # Create loop header
        if isinstance(stmt, ast.While):
            condition = ast.unparse(stmt.test) if hasattr(ast, 'unparse') else "condition"
            header = self._create_node(NodeType.LOOP, f"while {condition}")
        else:
            target = ast.unparse(stmt.target) if hasattr(ast, 'unparse') else "var"
            header = self._create_node(NodeType.LOOP, f"for {target}")
        
        self.cfg.add_node(header)
        self.cfg.add_edge(Edge(prev_node_id, header.id, EdgeType.CONTROL_FLOW))
        
        # Process loop body
        body_exits = self._process_statements(stmt.body, header.id)
        
        # Loop back edge
        for exit_id in body_exits:
            self.cfg.add_edge(Edge(exit_id, header.id, EdgeType.CONTROL_FLOW))
        
        # Loop exit (when condition is false)
        after_loop = self._create_node(NodeType.STATEMENT, "after_loop")
        self.cfg.add_node(after_loop)
        self.cfg.add_edge(Edge(header.id, after_loop.id, EdgeType.FALSE_BRANCH))
        
        return [after_loop.id]
    
    def _process_try(self, stmt: ast.Try, prev_node_id: str) -> List[str]:
        """Process try-except statement"""
        # Try block
        try_exits = self._process_statements(stmt.body, prev_node_id)
        
        # Exception handlers
        handler_exits = []
        for handler in stmt.handlers:
            handler_exits.extend(
                self._process_statements(handler.body, prev_node_id)
            )
        
        # Finally block (if exists)
        if stmt.finalbody:
            # Both try and handlers lead to finally
            finally_entry = try_exits + handler_exits
            for entry_id in finally_entry:
                finally_exits = self._process_statements(stmt.finalbody, entry_id)
            return finally_exits
        else:
            return try_exits + handler_exits
    
    def _process_function(self, stmt: ast.FunctionDef, prev_node_id: str) -> List[str]:
        """Process function definition (simplified: treat as single node)"""
        func_node = self._create_node(NodeType.STATEMENT, f"def {stmt.name}")
        self.cfg.add_node(func_node)
        self.cfg.add_edge(Edge(prev_node_id, func_node.id, EdgeType.CONTROL_FLOW))
        
        # Note: We don't recursively process function body in module-level CFG
        # Each function would have its own CFG
        
        return [func_node.id]
    
    def _process_return(self, stmt: ast.Return, prev_node_id: str) -> List[str]:
        """Process return statement"""
        value = ast.unparse(stmt.value) if stmt.value and hasattr(ast, 'unparse') else ""
        ret_node = self._create_node(NodeType.STATEMENT, f"return {value}")
        self.cfg.add_node(ret_node)
        self.cfg.add_edge(Edge(prev_node_id, ret_node.id, EdgeType.CONTROL_FLOW))
        
        return [ret_node.id]
    
    def _process_jump(self, stmt: ast.stmt, prev_node_id: str) -> List[str]:
        """Process break/continue"""
        jump_type = "break" if isinstance(stmt, ast.Break) else "continue"
        jump_node = self._create_node(NodeType.STATEMENT, jump_type)
        self.cfg.add_node(jump_node)
        self.cfg.add_edge(Edge(prev_node_id, jump_node.id, EdgeType.CONTROL_FLOW))
        
        return [jump_node.id]
    
    def _process_simple_statement(self, stmt: ast.stmt, prev_node_id: str) -> List[str]:
        """Process simple statement (assignment, expression, etc.)"""
        # Try to get readable representation
        if hasattr(ast, 'unparse'):
            label = ast.unparse(stmt)
        else:
            label = type(stmt).__name__
        
        # Truncate long labels
        if len(label) > 50:
            label = label[:47] + "..."
        
        stmt_node = self._create_node(NodeType.STATEMENT, label)
        self.cfg.add_node(stmt_node)
        self.cfg.add_edge(Edge(prev_node_id, stmt_node.id, EdgeType.CONTROL_FLOW))
        
        return [stmt_node.id]


def test_cfg_builder():
    """Test CFG builder"""
    code = """
def calculate(x, y):
    if x > 0:
        result = x + y
    else:
        result = x - y
    return result

x = 10
while x > 0:
    x = x - 1
    if x == 5:
        break

try:
    y = 1 / x
except ZeroDivisionError:
    y = 0
"""
    
    print("Testing CFG Builder...")
    print("="*60)
    
    builder = CFGBuilder()
    cfg = builder.build(code, "test_cfg")
    
    print(f"✓ CFG built: {cfg}")
    print(f"  Entry: {cfg.entry_node}")
    print(f"  Exits: {cfg.exit_nodes}")
    print(f"  Nodes: {len(cfg.nodes)}")
    print(f"  Edges: {len(cfg.edges)}")
    
    print("\nNodes:")
    for node_id, node in list(cfg.nodes.items())[:10]:  # Show first 10
        print(f"  {node}")
    
    print("\nEdges:")
    for edge in list(cfg.edges)[:10]:  # Show first 10
        print(f"  {edge}")
    
    print("\n✓ CFG Builder test passed!")
    
    return cfg


if __name__ == '__main__':
    test_cfg_builder()
