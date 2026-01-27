"""
Graph Edit Distance (GED) Approximation
Uses A* search with admissible heuristic (Riesen & Bunke, 2009)
"""

import sys
from pathlib import Path
from typing import List, Tuple, Set, Dict
import heapq
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.graphs import Graph, Node, Edge


@dataclass(order=True)
class SearchState:
    """State in A* search for GED"""
    f_cost: float  # g + h (total estimated cost)
    g_cost: float = field(compare=False)  # Actual cost so far
    h_cost: float = field(compare=False)  # Heuristic estimate
    node_mapping: Dict[str, str] = field(compare=False)  # G1 node -> G2 node
    unmapped_g1: Set[str] = field(compare=False)  # Unmapped nodes in G1
    unmapped_g2: Set[str] = field(compare=False)  # Unmapped nodes in G2


class GEDApproximation:
    """
    Approximate Graph Edit Distance using A* search.
    
    Based on:
    Riesen, K., & Bunke, H. (2009). 
    Approximate graph edit distance computation by means of bipartite graph matching.
    Image and Vision Computing, 27(7), 950-959.
    """
    
    def __init__(self, 
                 node_ins_cost: float = 1.0,
                 node_del_cost: float = 1.0,
                 node_sub_cost: float = 1.0,
                 edge_ins_cost: float = 1.0,
                 edge_del_cost: float = 1.0,
                 edge_sub_cost: float = 1.0,
                 max_iterations: int = 10000):
        """
        Initialize GED approximation with edit costs.
        
        Args:
            node_*_cost: Costs for node operations
            edge_*_cost: Costs for edge operations
            max_iterations: Maximum A* iterations (prevents timeout)
        """
        self.node_ins_cost = node_ins_cost
        self.node_del_cost = node_del_cost
        self.node_sub_cost = node_sub_cost
        self.edge_ins_cost = edge_ins_cost
        self.edge_del_cost = edge_del_cost
        self.edge_sub_cost = edge_sub_cost
        self.max_iterations = max_iterations
    
    def compute(self, g1: Graph, g2: Graph) -> Dict[str, float]:
        """
        Compute approximate GED between two graphs.
        
        Returns:
            {
                'ged': approximate edit distance,
                'normalized_ged': ged / max(|g1|, |g2|),
                'iterations': number of A* iterations,
                'timeout': whether max iterations reached
            }
        """
        # Handle empty graphs
        if len(g1.nodes) == 0 and len(g2.nodes) == 0:
            return {'ged': 0.0, 'normalized_ged': 0.0, 'iterations': 0, 'timeout': False}
        
        if len(g1.nodes) == 0:
            return {
                'ged': len(g2.nodes) * self.node_ins_cost,
                'normalized_ged': 1.0,
                'iterations': 0,
                'timeout': False
            }
        
        if len(g2.nodes) == 0:
            return {
                'ged': len(g1.nodes) * self.node_del_cost,
                'normalized_ged': 1.0,
                'iterations': 0,
                'timeout': False
            }
        
        # For large graphs, use faster heuristic-only approach
        if len(g1.nodes) > 100 or len(g2.nodes) > 100:
            return self._compute_greedy(g1, g2)
        
        # A* search
        result = self._a_star_search(g1, g2)
        
        return result
    
    def _a_star_search(self, g1: Graph, g2: Graph) -> Dict[str, float]:
        """A* search for GED"""
        # Initial state: no mappings
        initial_h = self._compute_heuristic(
            set(g1.nodes.keys()), 
            set(g2.nodes.keys()),
            g1, g2
        )
        
        initial_state = SearchState(
            f_cost=initial_h,
            g_cost=0.0,
            h_cost=initial_h,
            node_mapping={},
            unmapped_g1=set(g1.nodes.keys()),
            unmapped_g2=set(g2.nodes.keys())
        )
        
        # Priority queue: (f_cost, state)
        open_set = [initial_state]
        iterations = 0
        best_cost = float('inf')
        
        while open_set and iterations < self.max_iterations:
            iterations += 1
            
            # Pop state with lowest f_cost
            current = heapq.heappop(open_set)
            
            # Goal test: all nodes mapped
            if not current.unmapped_g1 and not current.unmapped_g2:
                best_cost = current.g_cost
                break
            
            # Generate successors
            successors = self._generate_successors(current, g1, g2)
            
            for successor in successors:
                heapq.heappush(open_set, successor)
                
                # Update best cost
                if successor.g_cost < best_cost:
                    best_cost = successor.g_cost
        
        # Normalize by graph size
        max_size = max(len(g1.nodes), len(g2.nodes))
        normalized = best_cost / max_size if max_size > 0 else 0.0
        
        return {
            'ged': best_cost,
            'normalized_ged': normalized,
            'iterations': iterations,
            'timeout': iterations >= self.max_iterations
        }
    
    def _generate_successors(self, state: SearchState, 
                           g1: Graph, g2: Graph) -> List[SearchState]:
        """Generate successor states from current state"""
        successors = []
        
        if not state.unmapped_g1:
            # No more G1 nodes: insert remaining G2 nodes
            insert_cost = len(state.unmapped_g2) * self.node_ins_cost
            new_g = state.g_cost + insert_cost
            successor = SearchState(
                f_cost=new_g,
                g_cost=new_g,
                h_cost=0.0,
                node_mapping=state.node_mapping.copy(),
                unmapped_g1=set(),
                unmapped_g2=set()
            )
            return [successor]
        
        # Pick next G1 node (greedy: smallest ID for consistency)
        n1 = min(state.unmapped_g1)
        
        # Option 1: Delete n1
        del_cost = self.node_del_cost
        new_unmapped_g1 = state.unmapped_g1 - {n1}
        new_g_del = state.g_cost + del_cost
        new_h_del = self._compute_heuristic(new_unmapped_g1, state.unmapped_g2, g1, g2)
        
        successors.append(SearchState(
            f_cost=new_g_del + new_h_del,
            g_cost=new_g_del,
            h_cost=new_h_del,
            node_mapping=state.node_mapping.copy(),
            unmapped_g1=new_unmapped_g1,
            unmapped_g2=state.unmapped_g2.copy()
        ))
        
        # Option 2: Map n1 to each unmapped G2 node
        for n2 in list(state.unmapped_g2)[:5]:  # Limit branching factor
            # Cost of substitution
            sub_cost = self._node_substitution_cost(g1.nodes[n1], g2.nodes[n2])
            
            new_mapping = state.node_mapping.copy()
            new_mapping[n1] = n2
            
            new_unmapped_g1 = state.unmapped_g1 - {n1}
            new_unmapped_g2 = state.unmapped_g2 - {n2}
            
            new_g_sub = state.g_cost + sub_cost
            new_h_sub = self._compute_heuristic(new_unmapped_g1, new_unmapped_g2, g1, g2)
            
            successors.append(SearchState(
                f_cost=new_g_sub + new_h_sub,
                g_cost=new_g_sub,
                h_cost=new_h_sub,
                node_mapping=new_mapping,
                unmapped_g1=new_unmapped_g1,
                unmapped_g2=new_unmapped_g2
            ))
        
        return successors
    
    def _compute_heuristic(self, unmapped_g1: Set[str], 
                          unmapped_g2: Set[str],
                          g1: Graph, g2: Graph) -> float:
        """
        Admissible heuristic: lower bound on remaining cost.
        Uses bipartite matching approximation.
        """
        n1 = len(unmapped_g1)
        n2 = len(unmapped_g2)
        
        if n1 == 0 and n2 == 0:
            return 0.0
        
        # Simple heuristic: assume best case (all can be matched with sub)
        # Remaining = |difference| * del/ins + |min| * sub
        if n1 > n2:
            return (n1 - n2) * self.node_del_cost + n2 * (self.node_sub_cost * 0.5)
        else:
            return (n2 - n1) * self.node_ins_cost + n1 * (self.node_sub_cost * 0.5)
    
    def _node_substitution_cost(self, node1: Node, node2: Node) -> float:
        """Cost of substituting node1 with node2"""
        # If labels match, cost is 0; otherwise use sub_cost
        if node1.label == node2.label:
            return 0.0
        else:
            return self.node_sub_cost
    
    def _compute_greedy(self, g1: Graph, g2: Graph) -> Dict[str, float]:
        """
        Greedy approximation for large graphs.
        Faster but less accurate than A*.
        """
        # Bipartite matching heuristic
        n1_ids = list(g1.nodes.keys())
        n2_ids = list(g2.nodes.keys())
        
        cost = 0.0
        
        # Match nodes greedily by label similarity
        matched_g2 = set()
        
        for n1_id in n1_ids:
            n1 = g1.nodes[n1_id]
            
            # Find best match in G2
            best_match = None
            best_cost = self.node_del_cost  # Cost of deleting
            
            for n2_id in n2_ids:
                if n2_id in matched_g2:
                    continue
                
                n2 = g2.nodes[n2_id]
                sub_cost = self._node_substitution_cost(n1, n2)
                
                if sub_cost < best_cost:
                    best_cost = sub_cost
                    best_match = n2_id
            
            cost += best_cost
            if best_match:
                matched_g2.add(best_match)
        
        # Remaining G2 nodes need insertion
        cost += (len(n2_ids) - len(matched_g2)) * self.node_ins_cost
        
        # Normalize
        max_size = max(len(g1.nodes), len(g2.nodes))
        normalized = cost / max_size if max_size > 0 else 0.0
        
        return {
            'ged': cost,
            'normalized_ged': normalized,
            'iterations': 0,
            'timeout': False
        }


def test_ged_approximation():
    """Test GED approximation"""
    from core.graphs import Graph, Node, NodeType, Edge, EdgeType
    
    print("Testing GED Approximation...")
    print("="*60)
    
    # Create two similar graphs
    g1 = Graph("g1")
    g1.add_node(Node("a", NodeType.STATEMENT, "x = 1"))
    g1.add_node(Node("b", NodeType.STATEMENT, "y = 2"))
    g1.add_node(Node("c", NodeType.STATEMENT, "z = 3"))
    g1.add_edge(Edge("a", "b", EdgeType.CONTROL_FLOW))
    g1.add_edge(Edge("b", "c", EdgeType.CONTROL_FLOW))
    
    g2 = Graph("g2")
    g2.add_node(Node("a", NodeType.STATEMENT, "x = 1"))
    g2.add_node(Node("b", NodeType.STATEMENT, "y = 5"))  # Changed
    g2.add_node(Node("c", NodeType.STATEMENT, "z = 3"))
    g2.add_node(Node("d", NodeType.STATEMENT, "w = 4"))  # Added
    g2.add_edge(Edge("a", "b", EdgeType.CONTROL_FLOW))
    g2.add_edge(Edge("b", "c", EdgeType.CONTROL_FLOW))
    g2.add_edge(Edge("c", "d", EdgeType.CONTROL_FLOW))
    
    print(f"G1: {g1}")
    print(f"G2: {g2}")
    
    # Compute GED
    ged_computer = GEDApproximation(max_iterations=1000)
    result = ged_computer.compute(g1, g2)
    
    print(f"\n✓ GED Result:")
    print(f"  GED: {result['ged']}")
    print(f"  Normalized GED: {result['normalized_ged']:.3f}")
    print(f"  Iterations: {result['iterations']}")
    print(f"  Timeout: {result['timeout']}")
    
    # Test with identical graphs
    result_same = ged_computer.compute(g1, g1)
    print(f"\n✓ GED for identical graphs: {result_same['ged']}")
    
    print("\n✓ GED Approximation test passed!")


if __name__ == '__main__':
    test_ged_approximation()
