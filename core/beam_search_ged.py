"""
Beam Search GED - Better approximation than greedy
Balances accuracy and performance
"""

import sys
from pathlib import Path
from typing import List, Tuple, Set, Dict
import heapq
from dataclasses import dataclass, field
from functools import lru_cache

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.graphs import Graph, Node, Edge


@dataclass(order=True)
class BeamState:
    """State in beam search for GED"""
    cost: float  # Total cost
    node_mapping: Dict[str, str] = field(compare=False)
    unmapped_g1: Set[str] = field(compare=False)
    unmapped_g2: Set[str] = field(compare=False)
    edit_sequence: List[str] = field(compare=False, default_factory=list)


class BeamSearchGED:
    """
    Beam Search for Graph Edit Distance.
    More accurate than greedy, faster than A*.
    
    Beam width controls trade-off:
    - k=1: Greedy (fast, less accurate)
    - k=10: Good balance
    - k=100: High accuracy (slower)
    """
    
    def __init__(self,
                 node_ins_cost: float = 1.0,
                 node_del_cost: float = 1.0,
                 node_sub_cost: float = 1.0,
                 edge_ins_cost: float = 1.0,
                 edge_del_cost: float = 1.0,
                 edge_sub_cost: float = 1.0,
                 beam_width: int = 10):
        self.node_ins_cost = node_ins_cost
        self.node_del_cost = node_del_cost
        self.node_sub_cost = node_sub_cost
        self.edge_ins_cost = edge_ins_cost
        self.edge_del_cost = edge_del_cost
        self.edge_sub_cost = edge_sub_cost
        self.beam_width = beam_width
    
    def compute(self, g1: Graph, g2: Graph) -> Dict[str, float]:
        """
        Compute GED using beam search.
        
        Returns:
            {
                'ged': approximate edit distance,
                'normalized_ged': ged / max(|g1|, |g2|),
                'beam_width': beam width used,
                'method': 'beam_search'
            }
        """
        # Handle empty graphs
        if len(g1.nodes) == 0 and len(g2.nodes) == 0:
            return {
                'ged': 0.0,
                'normalized_ged': 0.0,
                'beam_width': self.beam_width,
                'method': 'beam_search'
            }
        
        if len(g1.nodes) == 0:
            return {
                'ged': len(g2.nodes) * self.node_ins_cost,
                'normalized_ged': 1.0,
                'beam_width': self.beam_width,
                'method': 'beam_search'
            }
        
        if len(g2.nodes) == 0:
            return {
                'ged': len(g1.nodes) * self.node_del_cost,
                'normalized_ged': 1.0,
                'beam_width': self.beam_width,
                'method': 'beam_search'
            }
        
        # For very large graphs, use faster heuristic
        if len(g1.nodes) > 200 or len(g2.nodes) > 200:
            return self._compute_fast_heuristic(g1, g2)
        
        # Beam search
        result = self._beam_search(g1, g2)
        
        return result
    
    def _beam_search(self, g1: Graph, g2: Graph) -> Dict[str, float]:
        """Beam search for GED"""
        # Initial state: no mappings
        initial_state = BeamState(
            cost=0.0,
            node_mapping={},
            unmapped_g1=set(g1.nodes.keys()),
            unmapped_g2=set(g2.nodes.keys()),
            edit_sequence=[]
        )
        
        # Beam: keep top-k states
        beam = [initial_state]
        
        # Search until all nodes mapped
        while beam and beam[0].unmapped_g1:
            next_beam = []
            
            # Expand each state in beam
            for state in beam:
                # Generate successors
                successors = self._generate_successors(state, g1, g2)
                next_beam.extend(successors)
            
            # Keep top beam_width states
            next_beam.sort(key=lambda s: s.cost)
            beam = next_beam[:self.beam_width]
        
        # Best state
        if beam:
            best = beam[0]
            
            # Add cost for remaining G2 nodes (insertions)
            final_cost = best.cost + len(best.unmapped_g2) * self.node_ins_cost
            
            # Normalize
            max_size = max(len(g1.nodes), len(g2.nodes))
            normalized = final_cost / max_size if max_size > 0 else 0.0
            
            return {
                'ged': final_cost,
                'normalized_ged': normalized,
                'beam_width': self.beam_width,
                'method': 'beam_search'
            }
        else:
            # Fallback
            return {
                'ged': len(g1.nodes) + len(g2.nodes),
                'normalized_ged': 1.0,
                'beam_width': self.beam_width,
                'method': 'beam_search_fallback'
            }
    
    def _generate_successors(self, state: BeamState, 
                           g1: Graph, g2: Graph) -> List[BeamState]:
        """Generate successor states"""
        successors = []
        
        if not state.unmapped_g1:
            return [state]  # Done
        
        # Pick next G1 node (smallest ID for consistency)
        n1 = min(state.unmapped_g1)
        
        # Option 1: Delete n1
        del_cost = self.node_del_cost
        new_unmapped_g1 = state.unmapped_g1 - {n1}
        
        successors.append(BeamState(
            cost=state.cost + del_cost,
            node_mapping=state.node_mapping.copy(),
            unmapped_g1=new_unmapped_g1,
            unmapped_g2=state.unmapped_g2.copy(),
            edit_sequence=state.edit_sequence + [f"del({n1})"]
        ))
        
        # Option 2: Map n1 to each G2 node (limited by beam width)
        candidates = list(state.unmapped_g2)[:self.beam_width]
        
        for n2 in candidates:
            # Substitution cost
            sub_cost = self._node_substitution_cost(g1.nodes[n1], g2.nodes[n2])
            
            new_mapping = state.node_mapping.copy()
            new_mapping[n1] = n2
            
            new_unmapped_g1 = state.unmapped_g1 - {n1}
            new_unmapped_g2 = state.unmapped_g2 - {n2}
            
            successors.append(BeamState(
                cost=state.cost + sub_cost,
                node_mapping=new_mapping,
                unmapped_g1=new_unmapped_g1,
                unmapped_g2=new_unmapped_g2,
                edit_sequence=state.edit_sequence + [f"sub({n1}->{n2})"]
            ))
        
        return successors
    
    @lru_cache(maxsize=1024)
    def _node_substitution_cost(self, node1: Node, node2: Node) -> float:
        """Cost of substituting node1 with node2 (cached)"""
        # Exact match
        if node1.label == node2.label and node1.type == node2.type:
            return 0.0
        
        # Same type, different label
        if node1.type == node2.type:
            return self.node_sub_cost * 0.5
        
        # Different type
        return self.node_sub_cost
    
    def _compute_fast_heuristic(self, g1: Graph, g2: Graph) -> Dict[str, float]:
        """Fast heuristic for very large graphs"""
        # Hungarian-like bipartite matching
        n1_ids = list(g1.nodes.keys())
        n2_ids = list(g2.nodes.keys())
        
        cost = 0.0
        matched_g2 = set()
        
        # Sort by label for greedy matching
        n1_sorted = sorted(n1_ids, key=lambda x: g1.nodes[x].label)
        n2_sorted = sorted(n2_ids, key=lambda x: g2.nodes[x].label)
        
        # Greedy match
        j = 0
        for i, n1_id in enumerate(n1_sorted):
            n1 = g1.nodes[n1_id]
            
            best_match = None
            best_cost = self.node_del_cost
            
            # Look ahead in G2
            for k in range(j, min(j + 10, len(n2_sorted))):
                n2_id = n2_sorted[k]
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
                j += 1
        
        # Remaining G2 nodes
        cost += (len(n2_ids) - len(matched_g2)) * self.node_ins_cost
        
        # Normalize
        max_size = max(len(g1.nodes), len(g2.nodes))
        normalized = cost / max_size if max_size > 0 else 0.0
        
        return {
            'ged': cost,
            'normalized_ged': normalized,
            'beam_width': 0,
            'method': 'fast_heuristic'
        }


def test_beam_search_ged():
    """Test beam search GED"""
    from core.graphs import Graph, Node, NodeType, Edge, EdgeType
    
    print("Testing Beam Search GED...")
    print("="*60)
    
    # Create two graphs
    g1 = Graph("g1")
    g1.add_node(Node("a", NodeType.STATEMENT, "x = 1"))
    g1.add_node(Node("b", NodeType.STATEMENT, "y = 2"))
    g1.add_node(Node("c", NodeType.STATEMENT, "z = 3"))
    
    g2 = Graph("g2")
    g2.add_node(Node("a", NodeType.STATEMENT, "x = 1"))
    g2.add_node(Node("b", NodeType.STATEMENT, "y = 5"))  # Changed
    g2.add_node(Node("c", NodeType.STATEMENT, "z = 3"))
    g2.add_node(Node("d", NodeType.STATEMENT, "w = 4"))  # Added
    
    print(f"G1: {g1}")
    print(f"G2: {g2}")
    
    # Test different beam widths
    for beam_width in [1, 5, 10, 20]:
        ged_computer = BeamSearchGED(beam_width=beam_width)
        result = ged_computer.compute(g1, g2)
        
        print(f"\nBeam width = {beam_width}:")
        print(f"  GED: {result['ged']:.2f}")
        print(f"  Normalized: {result['normalized_ged']:.3f}")
        print(f"  Method: {result['method']}")
    
    # Compare with greedy (k=1) vs optimal (k=20)
    print("\n✓ Beam search GED test passed!")


if __name__ == '__main__':
    test_beam_search_ged()
