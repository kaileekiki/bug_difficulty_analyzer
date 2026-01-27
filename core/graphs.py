"""
Graph Structures for Code Analysis
- Base Graph class
- CFG (Control Flow Graph)
- DFG (Data Flow Graph)
- PDG (Program Dependence Graph)
- Call Graph
- CPG (Code Property Graph)
"""

from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class NodeType(Enum):
    """Types of nodes in code graphs"""
    # CFG nodes
    STATEMENT = "statement"
    ENTRY = "entry"
    EXIT = "exit"
    BRANCH = "branch"
    LOOP = "loop"
    
    # DFG nodes
    VARIABLE = "variable"
    DEFINITION = "definition"
    USE = "use"
    
    # Call graph nodes
    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    
    # CPG nodes
    AST_NODE = "ast_node"
    TYPE = "type"


class EdgeType(Enum):
    """Types of edges in code graphs"""
    # CFG edges
    CONTROL_FLOW = "control_flow"
    TRUE_BRANCH = "true_branch"
    FALSE_BRANCH = "false_branch"
    
    # DFG edges
    DATA_FLOW = "data_flow"
    DEF_USE = "def_use"
    
    # Call graph edges
    CALL = "call"
    INHERIT = "inherit"
    
    # PDG edges
    CONTROL_DEPENDENCE = "control_dependence"
    DATA_DEPENDENCE = "data_dependence"


@dataclass
class Node:
    """Generic graph node"""
    id: str
    type: NodeType
    label: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.id == other.id
    
    def __repr__(self):
        return f"Node({self.id}, {self.type.value}, {self.label})"


@dataclass
class Edge:
    """Generic graph edge"""
    source: str  # Node ID
    target: str  # Node ID
    type: EdgeType
    label: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash((self.source, self.target, self.type))
    
    def __eq__(self, other):
        if not isinstance(other, Edge):
            return False
        return (self.source == other.source and 
                self.target == other.target and 
                self.type == other.type)
    
    def __repr__(self):
        return f"Edge({self.source} -> {self.target}, {self.type.value})"


class Graph:
    """Base graph structure"""
    
    def __init__(self, name: str = ""):
        self.name = name
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self._adjacency: Dict[str, List[str]] = {}
    
    def add_node(self, node: Node):
        """Add a node to the graph"""
        self.nodes[node.id] = node
        if node.id not in self._adjacency:
            self._adjacency[node.id] = []
    
    def add_edge(self, edge: Edge):
        """Add an edge to the graph"""
        # Ensure nodes exist
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise ValueError(f"Edge nodes must exist: {edge.source}, {edge.target}")
        
        self.edges.append(edge)
        self._adjacency[edge.source].append(edge.target)
    
    def get_node(self, node_id: str) -> Node:
        """Get node by ID"""
        return self.nodes.get(node_id)
    
    def get_successors(self, node_id: str) -> List[str]:
        """Get successor node IDs"""
        return self._adjacency.get(node_id, [])
    
    def get_predecessors(self, node_id: str) -> List[str]:
        """Get predecessor node IDs"""
        predecessors = []
        for edge in self.edges:
            if edge.target == node_id:
                predecessors.append(edge.source)
        return predecessors
    
    def size(self) -> Tuple[int, int]:
        """Return (num_nodes, num_edges)"""
        return len(self.nodes), len(self.edges)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'nodes': [
                {
                    'id': n.id,
                    'type': n.type.value,
                    'label': n.label,
                    'attributes': n.attributes
                }
                for n in self.nodes.values()
            ],
            'edges': [
                {
                    'source': e.source,
                    'target': e.target,
                    'type': e.type.value,
                    'label': e.label,
                    'attributes': e.attributes
                }
                for e in self.edges
            ]
        }
    
    def __repr__(self):
        return f"Graph({self.name}, {len(self.nodes)} nodes, {len(self.edges)} edges)"


class CFG(Graph):
    """Control Flow Graph"""
    
    def __init__(self, name: str = "CFG"):
        super().__init__(name)
        self.entry_node: str = None
        self.exit_nodes: List[str] = []
    
    def set_entry(self, node_id: str):
        """Set entry node"""
        self.entry_node = node_id
    
    def add_exit(self, node_id: str):
        """Add exit node"""
        if node_id not in self.exit_nodes:
            self.exit_nodes.append(node_id)


class DFG(Graph):
    """Data Flow Graph"""
    
    def __init__(self, name: str = "DFG"):
        super().__init__(name)
        self.definitions: Dict[str, List[str]] = {}  # var_name -> [def_node_ids]
        self.uses: Dict[str, List[str]] = {}  # var_name -> [use_node_ids]
    
    def add_definition(self, var_name: str, node_id: str):
        """Record variable definition"""
        if var_name not in self.definitions:
            self.definitions[var_name] = []
        self.definitions[var_name].append(node_id)
    
    def add_use(self, var_name: str, node_id: str):
        """Record variable use"""
        if var_name not in self.uses:
            self.uses[var_name] = []
        self.uses[var_name].append(node_id)
    
    def get_def_use_chains(self) -> List[Tuple[str, str]]:
        """Get all definition-use chains"""
        chains = []
        for var_name in self.definitions:
            if var_name in self.uses:
                for def_node in self.definitions[var_name]:
                    for use_node in self.uses[var_name]:
                        chains.append((def_node, use_node))
        return chains


class PDG(Graph):
    """Program Dependence Graph (CFG + DFG)"""
    
    def __init__(self, name: str = "PDG"):
        super().__init__(name)
        self.control_edges: List[Edge] = []
        self.data_edges: List[Edge] = []
    
    def add_control_edge(self, edge: Edge):
        """Add control dependence edge"""
        edge.type = EdgeType.CONTROL_DEPENDENCE
        self.control_edges.append(edge)
        self.add_edge(edge)
    
    def add_data_edge(self, edge: Edge):
        """Add data dependence edge"""
        edge.type = EdgeType.DATA_DEPENDENCE
        self.data_edges.append(edge)
        self.add_edge(edge)


class CallGraph(Graph):
    """Call Graph"""
    
    def __init__(self, name: str = "CallGraph"):
        super().__init__(name)
        self.functions: Dict[str, Node] = {}
    
    def add_function(self, func_name: str, node: Node):
        """Register a function node"""
        self.functions[func_name] = node
        self.add_node(node)
    
    def add_call_edge(self, caller: str, callee: str):
        """Add function call edge"""
        edge = Edge(
            source=caller,
            target=callee,
            type=EdgeType.CALL,
            label="calls"
        )
        self.add_edge(edge)


class CPG(Graph):
    """Code Property Graph (combines all)"""
    
    def __init__(self, name: str = "CPG"):
        super().__init__(name)
        self.cfg: CFG = None
        self.dfg: DFG = None
        self.call_graph: CallGraph = None
        self.pdg: PDG = None
    
    def merge_graphs(self, cfg: CFG = None, dfg: DFG = None, 
                    call_graph: CallGraph = None):
        """Merge multiple graphs into CPG"""
        if cfg:
            self.cfg = cfg
            for node in cfg.nodes.values():
                self.add_node(node)
            for edge in cfg.edges:
                self.add_edge(edge)
        
        if dfg:
            self.dfg = dfg
            for node in dfg.nodes.values():
                if node.id not in self.nodes:
                    self.add_node(node)
            for edge in dfg.edges:
                if edge not in self.edges:
                    self.add_edge(edge)
        
        if call_graph:
            self.call_graph = call_graph
            for node in call_graph.nodes.values():
                if node.id not in self.nodes:
                    self.add_node(node)
            for edge in call_graph.edges:
                if edge not in self.edges:
                    self.add_edge(edge)


def test_graphs():
    """Test graph structures"""
    print("Testing Graph Structures...")
    print("="*60)
    
    # Test CFG
    cfg = CFG("test_cfg")
    
    # Add nodes
    entry = Node("n0", NodeType.ENTRY, "entry")
    stmt1 = Node("n1", NodeType.STATEMENT, "x = 1")
    branch = Node("n2", NodeType.BRANCH, "if x > 0")
    stmt2 = Node("n3", NodeType.STATEMENT, "y = 2")
    exit_node = Node("n4", NodeType.EXIT, "exit")
    
    cfg.add_node(entry)
    cfg.add_node(stmt1)
    cfg.add_node(branch)
    cfg.add_node(stmt2)
    cfg.add_node(exit_node)
    
    cfg.set_entry("n0")
    cfg.add_exit("n4")
    
    # Add edges
    cfg.add_edge(Edge("n0", "n1", EdgeType.CONTROL_FLOW))
    cfg.add_edge(Edge("n1", "n2", EdgeType.CONTROL_FLOW))
    cfg.add_edge(Edge("n2", "n3", EdgeType.TRUE_BRANCH))
    cfg.add_edge(Edge("n2", "n4", EdgeType.FALSE_BRANCH))
    cfg.add_edge(Edge("n3", "n4", EdgeType.CONTROL_FLOW))
    
    print(f"✓ CFG: {cfg}")
    print(f"  Entry: {cfg.entry_node}")
    print(f"  Exits: {cfg.exit_nodes}")
    
    # Test DFG
    dfg = DFG("test_dfg")
    
    def_x = Node("d1", NodeType.DEFINITION, "def x")
    use_x = Node("u1", NodeType.USE, "use x")
    
    dfg.add_node(def_x)
    dfg.add_node(use_x)
    dfg.add_definition("x", "d1")
    dfg.add_use("x", "u1")
    dfg.add_edge(Edge("d1", "u1", EdgeType.DATA_FLOW))
    
    print(f"✓ DFG: {dfg}")
    print(f"  Def-Use chains: {dfg.get_def_use_chains()}")
    
    # Test Call Graph
    call_graph = CallGraph("test_callgraph")
    
    func1 = Node("f1", NodeType.FUNCTION, "foo")
    func2 = Node("f2", NodeType.FUNCTION, "bar")
    
    call_graph.add_function("foo", func1)
    call_graph.add_function("bar", func2)
    call_graph.add_call_edge("f1", "f2")
    
    print(f"✓ Call Graph: {call_graph}")
    
    # Test CPG
    cpg = CPG("test_cpg")
    cpg.merge_graphs(cfg, dfg, call_graph)
    
    print(f"✓ CPG: {cpg}")
    print(f"  Total nodes: {len(cpg.nodes)}")
    print(f"  Total edges: {len(cpg.edges)}")
    
    print("\n✓ All graph structure tests passed!")


if __name__ == '__main__':
    test_graphs()
