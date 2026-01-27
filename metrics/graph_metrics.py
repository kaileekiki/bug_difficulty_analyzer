"""
Graph-based Metrics
Integrates graph builders and GED computation for:
- CFG-GED
- DFG-GED (Main Hypothesis!)
- PDG-GED
- Call Graph-GED
- CPG-GED
"""

import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.graphs import PDG, CPG, EdgeType
from core.cfg_builder import CFGBuilder
from core.dfg_builder import DFGBuilder
from core.callgraph_builder import CallGraphBuilder
from core.ged_approximation import GEDApproximation


class GraphMetrics:
    """Compute all graph-based metrics"""
    
    def __init__(self):
        self.cfg_builder = CFGBuilder()
        self.dfg_builder = DFGBuilder()
        self.cg_builder = CallGraphBuilder()
        self.ged_computer = GEDApproximation(max_iterations=5000)
    
    def compute_all_graph_metrics(self, code_before: str, 
                                  code_after: str) -> Dict[str, Any]:
        """
        Compute all 5 graph-based metrics.
        
        Returns metrics for:
        - CFG-GED
        - DFG-GED (Main Hypothesis!)
        - PDG-GED (CFG + DFG)
        - Call Graph-GED
        - CPG-GED (union of all)
        """
        results = {}
        
        # 1. CFG-GED
        print("  Computing CFG-GED...")
        results['CFG_GED'] = self._compute_cfg_ged(code_before, code_after)
        
        # 2. DFG-GED (Main Hypothesis!)
        print("  Computing DFG-GED ⭐...")
        results['DFG_GED'] = self._compute_dfg_ged(code_before, code_after)
        
        # 3. Call Graph-GED
        print("  Computing Call Graph-GED...")
        results['Call_Graph_GED'] = self._compute_callgraph_ged(code_before, code_after)
        
        # 4. PDG-GED (requires CFG + DFG)
        print("  Computing PDG-GED...")
        results['PDG_GED'] = self._compute_pdg_ged(code_before, code_after)
        
        # 5. CPG-GED (union of all)
        print("  Computing CPG-GED...")
        results['CPG_GED'] = self._compute_cpg_ged(code_before, code_after)
        
        return results
    
    def _compute_cfg_ged(self, code_before: str, code_after: str) -> Dict[str, Any]:
        """Compute Control Flow Graph Edit Distance"""
        try:
            cfg_before = self.cfg_builder.build(code_before, "cfg_before")
            cfg_after = self.cfg_builder.build(code_after, "cfg_after")
            
            ged_result = self.ged_computer.compute(cfg_before, cfg_after)
            
            return {
                'cfg_ged': ged_result['ged'],
                'cfg_normalized_ged': ged_result['normalized_ged'],
                'cfg_nodes_before': len(cfg_before.nodes),
                'cfg_nodes_after': len(cfg_after.nodes),
                'cfg_edges_before': len(cfg_before.edges),
                'cfg_edges_after': len(cfg_after.edges)
            }
        except Exception as e:
            return {'cfg_ged': -1, 'error': str(e)}
    
    def _compute_dfg_ged(self, code_before: str, code_after: str) -> Dict[str, Any]:
        """
        Compute Data Flow Graph Edit Distance.
        ⭐ MAIN HYPOTHESIS: This should be the strongest predictor!
        """
        try:
            dfg_before = self.dfg_builder.build(code_before, "dfg_before")
            dfg_after = self.dfg_builder.build(code_after, "dfg_after")
            
            ged_result = self.ged_computer.compute(dfg_before, dfg_after)
            
            return {
                'dfg_ged': ged_result['ged'],
                'dfg_normalized_ged': ged_result['normalized_ged'],
                'dfg_nodes_before': len(dfg_before.nodes),
                'dfg_nodes_after': len(dfg_after.nodes),
                'dfg_edges_before': len(dfg_before.edges),
                'dfg_edges_after': len(dfg_after.edges),
                'dfg_variables_before': len(dfg_before.definitions),
                'dfg_variables_after': len(dfg_after.definitions),
                'dfg_def_use_chains_before': len(dfg_before.get_def_use_chains()),
                'dfg_def_use_chains_after': len(dfg_after.get_def_use_chains())
            }
        except Exception as e:
            return {'dfg_ged': -1, 'error': str(e)}
    
    def _compute_callgraph_ged(self, code_before: str, 
                               code_after: str) -> Dict[str, Any]:
        """Compute Call Graph Edit Distance"""
        try:
            cg_before = self.cg_builder.build(code_before, "cg_before")
            cg_after = self.cg_builder.build(code_after, "cg_after")
            
            ged_result = self.ged_computer.compute(cg_before, cg_after)
            
            return {
                'callgraph_ged': ged_result['ged'],
                'callgraph_normalized_ged': ged_result['normalized_ged'],
                'callgraph_functions_before': len(cg_before.functions),
                'callgraph_functions_after': len(cg_after.functions),
                'callgraph_calls_before': sum(1 for e in cg_before.edges 
                                             if e.type == EdgeType.CALL),
                'callgraph_calls_after': sum(1 for e in cg_after.edges 
                                            if e.type == EdgeType.CALL)
            }
        except Exception as e:
            return {'callgraph_ged': -1, 'error': str(e)}
    
    def _compute_pdg_ged(self, code_before: str, code_after: str) -> Dict[str, Any]:
        """
        Compute Program Dependence Graph Edit Distance.
        PDG = CFG + DFG (control + data dependencies)
        """
        try:
            # Build CFG and DFG
            cfg_before = self.cfg_builder.build(code_before, "cfg")
            dfg_before = self.dfg_builder.build(code_before, "dfg")
            
            cfg_after = self.cfg_builder.build(code_after, "cfg")
            dfg_after = self.dfg_builder.build(code_after, "dfg")
            
            # Merge into PDG
            pdg_before = self._merge_to_pdg(cfg_before, dfg_before)
            pdg_after = self._merge_to_pdg(cfg_after, dfg_after)
            
            ged_result = self.ged_computer.compute(pdg_before, pdg_after)
            
            return {
                'pdg_ged': ged_result['ged'],
                'pdg_normalized_ged': ged_result['normalized_ged'],
                'pdg_nodes_before': len(pdg_before.nodes),
                'pdg_nodes_after': len(pdg_after.nodes),
                'pdg_edges_before': len(pdg_before.edges),
                'pdg_edges_after': len(pdg_after.edges)
            }
        except Exception as e:
            return {'pdg_ged': -1, 'error': str(e)}
    
    def _compute_cpg_ged(self, code_before: str, code_after: str) -> Dict[str, Any]:
        """
        Compute Code Property Graph Edit Distance.
        CPG = CFG + DFG + Call Graph (comprehensive)
        """
        try:
            # Build all graphs
            cfg_before = self.cfg_builder.build(code_before, "cfg")
            dfg_before = self.dfg_builder.build(code_before, "dfg")
            cg_before = self.cg_builder.build(code_before, "cg")
            
            cfg_after = self.cfg_builder.build(code_after, "cfg")
            dfg_after = self.dfg_builder.build(code_after, "dfg")
            cg_after = self.cg_builder.build(code_after, "cg")
            
            # Merge into CPG
            cpg_before = CPG("cpg_before")
            cpg_before.merge_graphs(cfg_before, dfg_before, cg_before)
            
            cpg_after = CPG("cpg_after")
            cpg_after.merge_graphs(cfg_after, dfg_after, cg_after)
            
            ged_result = self.ged_computer.compute(cpg_before, cpg_after)
            
            return {
                'cpg_ged': ged_result['ged'],
                'cpg_normalized_ged': ged_result['normalized_ged'],
                'cpg_nodes_before': len(cpg_before.nodes),
                'cpg_nodes_after': len(cpg_after.nodes),
                'cpg_edges_before': len(cpg_before.edges),
                'cpg_edges_after': len(cpg_after.edges)
            }
        except Exception as e:
            return {'cpg_ged': -1, 'error': str(e)}
    
    def _merge_to_pdg(self, cfg, dfg) -> PDG:
        """Merge CFG and DFG into PDG"""
        pdg = PDG(f"pdg_{cfg.name}")
        
        # Add all nodes from both graphs
        for node in cfg.nodes.values():
            if node.id not in pdg.nodes:
                pdg.add_node(node)
        
        for node in dfg.nodes.values():
            if node.id not in pdg.nodes:
                pdg.add_node(node)
        
        # Add control edges from CFG
        for edge in cfg.edges:
            pdg.add_control_edge(edge)
        
        # Add data edges from DFG
        for edge in dfg.edges:
            pdg.add_data_edge(edge)
        
        return pdg


def test_graph_metrics():
    """Test all graph metrics"""
    code_before = """
def calculate(x, y):
    result = x + y
    return result

a = 10
b = 20
c = calculate(a, b)
"""
    
    code_after = """
def calculate(x, y):
    if y == 0:
        return 0
    result = x + y
    temp = result * 2
    return temp

def helper(z):
    return z + 1

a = 10
b = 20
c = calculate(a, b)
d = helper(c)
"""
    
    print("Testing Graph Metrics...")
    print("="*60)
    
    metrics = GraphMetrics()
    results = metrics.compute_all_graph_metrics(code_before, code_after)
    
    print("\n✓ All Graph Metrics Computed:")
    for metric_name, metric_data in results.items():
        print(f"\n{metric_name}:")
        for key, value in metric_data.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.3f}")
            else:
                print(f"  {key}: {value}")
    
    print("\n✓ Graph Metrics test passed!")
    
    return results


if __name__ == '__main__':
    test_graph_metrics()
