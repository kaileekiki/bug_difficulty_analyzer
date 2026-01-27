"""
Enhanced DFG Builder - SSA-inspired Data Flow Analysis
More accurate def-use chains with phi-node concepts
"""

import ast
import sys
from pathlib import Path
from typing import List, Set, Dict, Optional, Tuple
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.graphs import DFG, Node, Edge, NodeType, EdgeType


class EnhancedDFGBuilder:
    """
    Enhanced DFG Builder with SSA-inspired analysis.
    
    Improvements over basic DFG:
    1. Version numbering for variables (SSA-like)
    2. Phi nodes at merge points
    3. More accurate reaching definitions
    4. Control flow aware data flow
    """
    
    def __init__(self):
        self.node_counter = 0
        self.dfg = None
        self.current_scope = None
        self.scopes = {}
        self.version_counters = defaultdict(int)  # var_name -> version
        self.reaching_defs = {}  # block_id -> {var_name -> [def_nodes]}
    
    def build(self, code: str, name: str = "DFG") -> DFG:
        """Build enhanced DFG from Python code"""
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
        self.version_counters = defaultdict(int)
        self.reaching_defs = {}
        
        # Process the AST with enhanced analysis
        self._process_node(tree)
        
        # Build enhanced def-use edges
        self._build_enhanced_def_use_edges()
        
        return self.dfg
    
    def _create_node(self, node_type: NodeType, label: str, 
                    attributes: Dict = None) -> Node:
        """Create a new node with unique ID"""
        node_id = f"d{self.node_counter}"
        self.node_counter += 1
        return Node(node_id, node_type, label, attributes or {})
    
    def _get_versioned_name(self, var_name: str) -> str:
        """Get SSA-style versioned name (e.g., x_1, x_2)"""
        version = self.version_counters[var_name]
        return f"{var_name}_{version}"
    
    def _increment_version(self, var_name: str):
        """Increment version counter for variable"""
        self.version_counters[var_name] += 1
    
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
        
        elif isinstance(node, ast.While):
            self._process_while_loop(node)
        
        elif isinstance(node, ast.If):
            self._process_if_statement(node)
        
        elif isinstance(node, ast.Call):
            self._process_call(node)
        
        elif isinstance(node, ast.Return):
            self._process_return(node)
        
        # Recursively process children (for non-handled types)
        else:
            for child in ast.iter_child_nodes(node):
                self._process_node(child)
    
    def _process_function(self, node: ast.FunctionDef):
        """Process function definition"""
        old_scope = self.current_scope
        self.current_scope = f"func_{node.name}"
        self.scopes[self.current_scope] = {}
        
        # Reset version counters for new scope
        old_versions = self.version_counters.copy()
        self.version_counters = defaultdict(int)
        
        # Process arguments (they are definitions)
        for arg in node.args.args:
            self._add_definition(arg.arg, node.lineno, is_param=True)
        
        # Process function body
        for stmt in node.body:
            self._process_node(stmt)
        
        # Restore scope and versions
        self.current_scope = old_scope
        self.version_counters = old_versions
    
    def _process_assignment(self, node: ast.Assign):
        """Process assignment with version tracking"""
        # First, process RHS (uses current versions)
        use_nodes = self._extract_uses(node.value, node.lineno)
        
        # Then, process LHS (creates new versions)
        for target in node.targets:
            if isinstance(target, ast.Name):
                self._add_definition(target.id, node.lineno)
            elif isinstance(target, (ast.Tuple, ast.List)):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self._add_definition(elt.id, node.lineno)
    
    def _process_aug_assignment(self, node: ast.AugAssign):
        """Process augmented assignment (use then def)"""
        if isinstance(node.target, ast.Name):
            var_name = node.target.id
            
            # Use current version
            self._add_use(var_name, node.lineno)
            
            # Process RHS
            self._extract_uses(node.value, node.lineno)
            
            # Create new version
            self._add_definition(var_name, node.lineno)
    
    def _process_annotated_assignment(self, node: ast.AnnAssign):
        """Process annotated assignment"""
        if isinstance(node.target, ast.Name):
            if node.value:
                self._extract_uses(node.value, node.lineno)
            self._add_definition(node.target.id, node.lineno)
    
    def _process_for_loop(self, node: ast.For):
        """Process for loop with phi-like handling"""
        # Iterator is used
        self._extract_uses(node.iter, node.lineno)
        
        # Loop variable: create phi node (merge point)
        if isinstance(node.target, ast.Name):
            var_name = node.target.id
            # Save pre-loop version
            pre_loop_version = self.version_counters[var_name]
            
            # Create phi node for loop variable
            self._add_phi_node(var_name, node.lineno, "for_loop")
            
            # Process body (may redefine loop var)
            for stmt in node.body:
                self._process_node(stmt)
            
            # Post-loop: another phi node
            self._add_phi_node(var_name, node.lineno, "for_exit")
    
    def _process_while_loop(self, node: ast.While):
        """Process while loop with phi handling"""
        # Condition uses variables
        self._extract_uses(node.test, node.lineno)
        
        # Process body
        for stmt in node.body:
            self._process_node(stmt)
    
    def _process_if_statement(self, node: ast.If):
        """Process if statement with merge points"""
        # Condition
        self._extract_uses(node.test, node.lineno)
        
        # Track versions before branches
        pre_branch_versions = self.version_counters.copy()
        
        # Then branch
        for stmt in node.body:
            self._process_node(stmt)
        then_versions = self.version_counters.copy()
        
        # Restore and process else branch
        self.version_counters = pre_branch_versions.copy()
        if node.orelse:
            for stmt in node.orelse:
                self._process_node(stmt)
        else_versions = self.version_counters.copy()
        
        # Merge point: create phi nodes for modified variables
        modified_vars = set(then_versions.keys()) | set(else_versions.keys())
        for var in modified_vars:
            if then_versions[var] != else_versions[var]:
                # Variable was modified in at least one branch
                self._add_phi_node(var, node.lineno, "if_merge")
                # Use max version
                self.version_counters[var] = max(then_versions[var], else_versions[var])
    
    def _process_call(self, node: ast.Call):
        """Process function call"""
        if isinstance(node.func, ast.Name):
            self._add_use(node.func.id, node.lineno)
        
        for arg in node.args:
            self._extract_uses(arg, node.lineno)
        
        for keyword in node.keywords:
            self._extract_uses(keyword.value, node.lineno)
    
    def _process_return(self, node: ast.Return):
        """Process return statement"""
        if node.value:
            self._extract_uses(node.value, node.lineno)
    
    def _extract_uses(self, node: ast.AST, lineno: int) -> List[str]:
        """Extract all variable uses from an expression"""
        use_nodes = []
        
        if isinstance(node, ast.Name):
            use_id = self._add_use(node.id, lineno)
            use_nodes.append(use_id)
        
        elif isinstance(node, ast.BinOp):
            use_nodes.extend(self._extract_uses(node.left, lineno))
            use_nodes.extend(self._extract_uses(node.right, lineno))
        
        elif isinstance(node, ast.UnaryOp):
            use_nodes.extend(self._extract_uses(node.operand, lineno))
        
        elif isinstance(node, ast.Compare):
            use_nodes.extend(self._extract_uses(node.left, lineno))
            for comp in node.comparators:
                use_nodes.extend(self._extract_uses(comp, lineno))
        
        elif isinstance(node, ast.Call):
            self._process_call(node)
        
        elif isinstance(node, ast.Subscript):
            use_nodes.extend(self._extract_uses(node.value, lineno))
            use_nodes.extend(self._extract_uses(node.slice, lineno))
        
        elif isinstance(node, ast.Attribute):
            use_nodes.extend(self._extract_uses(node.value, lineno))
        
        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            for elt in node.elts:
                use_nodes.extend(self._extract_uses(elt, lineno))
        
        elif isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if k:
                    use_nodes.extend(self._extract_uses(k, lineno))
                use_nodes.extend(self._extract_uses(v, lineno))
        
        return use_nodes
    
    def _add_definition(self, var_name: str, lineno: int, is_param: bool = False):
        """Add variable definition with version tracking"""
        # Increment version for new definition
        self._increment_version(var_name)
        versioned = self._get_versioned_name(var_name)
        
        label = f"def {versioned}@{lineno}"
        if is_param:
            label += " (param)"
        
        def_node = self._create_node(
            NodeType.DEFINITION,
            label,
            {
                'var_name': var_name,
                'version': self.version_counters[var_name],
                'lineno': lineno,
                'scope': self.current_scope
            }
        )
        self.dfg.add_node(def_node)
        self.dfg.add_definition(var_name, def_node.id)
        
        # Track in scope
        if var_name not in self.scopes[self.current_scope]:
            self.scopes[self.current_scope][var_name] = []
        self.scopes[self.current_scope][var_name].append(def_node.id)
    
    def _add_use(self, var_name: str, lineno: int) -> str:
        """Add variable use (references current version)"""
        versioned = self._get_versioned_name(var_name)
        
        use_node = self._create_node(
            NodeType.USE,
            f"use {versioned}@{lineno}",
            {
                'var_name': var_name,
                'version': self.version_counters[var_name],
                'lineno': lineno,
                'scope': self.current_scope
            }
        )
        self.dfg.add_node(use_node)
        self.dfg.add_use(var_name, use_node.id)
        
        return use_node.id
    
    def _add_phi_node(self, var_name: str, lineno: int, context: str):
        """Add phi node for merge points"""
        self._increment_version(var_name)
        versioned = self._get_versioned_name(var_name)
        
        phi_node = self._create_node(
            NodeType.DEFINITION,
            f"φ {versioned}@{lineno} ({context})",
            {
                'var_name': var_name,
                'version': self.version_counters[var_name],
                'lineno': lineno,
                'scope': self.current_scope,
                'is_phi': True
            }
        )
        self.dfg.add_node(phi_node)
        self.dfg.add_definition(var_name, phi_node.id)
    
    def _build_enhanced_def_use_edges(self):
        """Build edges using version information"""
        for var_name in self.dfg.definitions:
            if var_name not in self.dfg.uses:
                continue
            
            def_nodes = self.dfg.definitions[var_name]
            use_nodes = self.dfg.uses[var_name]
            
            # Match by version
            for use_id in use_nodes:
                use_node = self.dfg.get_node(use_id)
                use_version = use_node.attributes.get('version', 0)
                use_line = use_node.attributes.get('lineno', 0)
                
                # Find reaching definition: latest def with version <= use_version
                reaching_def = None
                for def_id in def_nodes:
                    def_node = self.dfg.get_node(def_id)
                    def_version = def_node.attributes.get('version', 0)
                    def_line = def_node.attributes.get('lineno', 0)
                    
                    # Must be in same scope and before use
                    if (def_node.attributes.get('scope') == use_node.attributes.get('scope')
                        and def_version == use_version
                        and def_line < use_line):
                        reaching_def = def_id
                        break
                
                if reaching_def:
                    edge = Edge(
                        source=reaching_def,
                        target=use_id,
                        type=EdgeType.DATA_FLOW,
                        label=f"{var_name}"
                    )
                    self.dfg.add_edge(edge)


def test_enhanced_dfg():
    """Test enhanced DFG builder"""
    code = """
x = 1
if condition:
    x = 2
    y = x + 1
else:
    x = 3
    y = x + 2
z = x + y  # x and y should use merged versions
"""
    
    print("Testing Enhanced DFG Builder...")
    print("="*60)
    
    builder = EnhancedDFGBuilder()
    dfg = builder.build(code)
    
    print(f"✓ Enhanced DFG: {dfg}")
    print(f"  Nodes: {len(dfg.nodes)}")
    print(f"  Edges: {len(dfg.edges)}")
    
    print("\nNodes with versions:")
    for node_id, node in list(dfg.nodes.items())[:15]:
        version = node.attributes.get('version', '?')
        is_phi = node.attributes.get('is_phi', False)
        marker = "φ" if is_phi else ""
        print(f"  {marker} {node.label} (v{version})")
    
    print("\n✓ Enhanced DFG test passed!")


if __name__ == '__main__':
    test_enhanced_dfg()
