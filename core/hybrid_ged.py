"""
Hybrid GED Calculator - Accuracy First
Small graphs: High beam width (k=50)
Large graphs: Progressive beam width with timeout
"""

import sys
from pathlib import Path
from typing import Dict, Any
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.graphs import Graph
from core.beam_search_ged import BeamSearchGED


class HybridGEDCalculator:
    """
    Hybrid GED with accuracy-first approach.
    
    Strategy:
    - Tiny (< 20 nodes): k=100 (near-exact)
    - Small (20-50 nodes): k=50 (very accurate)
    - Medium (50-100 nodes): k=20 (accurate)
    - Large (100-200 nodes): k=10 (fast)
    - Huge (> 200 nodes): fast heuristic
    """
    
    def __init__(self, max_time_per_graph: float = 120.0):
        """
        Args:
            max_time_per_graph: Maximum seconds per GED computation
        """
        self.max_time = max_time_per_graph
    
    def compute(self, g1: Graph, g2: Graph, 
                metric_name: str = "GED") -> Dict[str, Any]:
        """
        Compute GED with adaptive beam width.
        
        Returns:
            {
                'ged': float,
                'normalized_ged': float,
                'method': str,
                'beam_width': int,
                'computation_time': float,
                'graph_size': str
            }
        """
        start_time = time.time()
        
        # Determine graph size category
        max_size = max(len(g1.nodes), len(g2.nodes))
        
        # Empty graph handling
        if len(g1.nodes) == 0 and len(g2.nodes) == 0:
            return {
                'ged': 0.0,
                'normalized_ged': 0.0,
                'method': 'trivial',
                'beam_width': 0,
                'computation_time': 0.0,
                'graph_size': 'empty'
            }
        
        if len(g1.nodes) == 0:
            return {
                'ged': float(len(g2.nodes)),
                'normalized_ged': 1.0,
                'method': 'trivial',
                'beam_width': 0,
                'computation_time': time.time() - start_time,
                'graph_size': 'trivial'
            }
        
        if len(g2.nodes) == 0:
            return {
                'ged': float(len(g1.nodes)),
                'normalized_ged': 1.0,
                'method': 'trivial',
                'beam_width': 0,
                'computation_time': time.time() - start_time,
                'graph_size': 'trivial'
            }
        
        # Adaptive beam width selection
        if max_size < 20:
            beam_width = 100  # Near-exact for tiny graphs
            category = 'tiny'
        elif max_size < 50:
            beam_width = 50   # Very accurate for small graphs
            category = 'small'
        elif max_size < 100:
            beam_width = 20   # Accurate for medium graphs
            category = 'medium'
        elif max_size < 200:
            beam_width = 10   # Fast for large graphs
            category = 'large'
        else:
            # Huge graphs: use fast heuristic
            return self._fast_heuristic(g1, g2, start_time, 'huge')
        
        # Try with selected beam width
        try:
            ged_computer = BeamSearchGED(beam_width=beam_width)
            result = ged_computer.compute(g1, g2)
            
            computation_time = time.time() - start_time
            
            # Timeout check
            if computation_time > self.max_time:
                print(f"  ⚠️  {metric_name} timeout ({computation_time:.1f}s), using fallback")
                return self._fast_heuristic(g1, g2, start_time, category + '_timeout')
            
            return {
                'ged': result['ged'],
                'normalized_ged': result['normalized_ged'],
                'method': result['method'],
                'beam_width': beam_width,
                'computation_time': computation_time,
                'graph_size': category
            }
            
        except Exception as e:
            print(f"  ⚠️  {metric_name} error: {e}, using fallback")
            return self._fast_heuristic(g1, g2, start_time, category + '_error')
    
    def _fast_heuristic(self, g1: Graph, g2: Graph, 
                       start_time: float, category: str) -> Dict[str, Any]:
        """Fast heuristic for large graphs"""
        # Simple greedy matching
        ged_computer = BeamSearchGED(beam_width=1)  # Greedy
        result = ged_computer.compute(g1, g2)
        
        return {
            'ged': result['ged'],
            'normalized_ged': result['normalized_ged'],
            'method': 'fast_heuristic',
            'beam_width': 1,
            'computation_time': time.time() - start_time,
            'graph_size': category
        }
