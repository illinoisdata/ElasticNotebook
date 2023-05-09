from elastic.algorithm.selector import Selector
from elastic.core.graph.variable_snapshot import VariableSnapshot
from elastic.core.graph.cell_execution import CellExecution

from collections import defaultdict
import networkx as nx
from networkx.algorithms.flow import shortest_augmenting_path
import numpy as np


class OptimizerExact(Selector):
    """
        The exact optimizer constructs a flow graph and runs the min-cut algorithm to exactly find the best
        checkpointing configuration.
    """

    def __init__(self, migration_speed_bps=1):
        super().__init__(migration_speed_bps)

        # Augmented computation graph
        self.active_oes = None
        self.compute_graph = None

        # CEs required to recompute a variables last modified by a given CE.
        self.recomputation_ces = defaultdict(set)

        self.idx = 0

    def get_new_idx(self) -> int:
        """
            Get a new index number to add to compute graph.
        """
        idx = self.idx
        self.idx += 1
        return idx

    def dfs(self, current: str, visited: set, recompute_ces: str):
        """
            Perform DFS on the Application History Graph for finding the CEs required to recompute a variable.
            Args:
                current (str): Name of current nodeset.
                visited (set): Visited nodesets.
                recompute_ces (set): Set of CEs needing re-execution to recompute the current nodeset.
        """
        if isinstance(current, CellExecution):
            # Result is memoized
            if current in self.recomputation_ces:
                recompute_ces.update(self.recomputation_ces[current])
            else:
                recompute_ces.add(current)
                for vs in current.src_vss:
                    if vs not in self.active_vss and vs not in visited:
                        self.dfs(vs, visited, recompute_ces)

        elif isinstance(current, VariableSnapshot):
            visited.add(current)
            if current.output_ce not in recompute_ces:
                self.dfs(current.output_ce, visited, recompute_ces)

    def find_prerequisites(self):
        """
            Find the necessary (prerequisite) cell executions to rerun a cell execution.
        """
        self.active_vss = set(self.active_vss)

        for oe in self.dependency_graph.cell_executions:
            if oe.dst_vss.intersection(self.active_vss):
                self.dfs(oe, set(), self.recomputation_ces[oe])

    def select_vss(self, write_log_location=None, notebook_name=None, optimizer_name=None) -> set:
        self.find_prerequisites()

        # Construct flow graph for computing mincut
        mincut_graph = nx.DiGraph()

        # Add source and sink to flow graph.
        mincut_graph.add_node("source")
        mincut_graph.add_node("sink")

        # Add all active VSs as nodes, connect them with the source with edge capacity equal to migration cost.
        for active_vs in self.active_vss:
            mincut_graph.add_node(active_vs)
            mincut_graph.add_edge("source", active_vs, capacity=active_vs.size / self.migration_speed_bps)

        # Add all CEs as nodes, connect them with the sink with edge capacity equal to recomputation cost.
        for ce in self.dependency_graph.cell_executions:
            mincut_graph.add_node(ce)
            mincut_graph.add_edge(ce, "sink", capacity=ce.cell_runtime)

        # Connect each CE with its output variables and its prerequisite OEs.
        for active_vs in self.active_vss:
            for ce in self.recomputation_ces[active_vs.output_ce]:
                mincut_graph.add_edge(active_vs, ce, capacity=np.inf)

        # Add constraints: overlapping variables must either be migrated or recomputed together.
        for vs_pair in self.overlapping_vss:
            mincut_graph.add_edge(vs_pair[0], vs_pair[1], capacity=np.inf)
            mincut_graph.add_edge(vs_pair[1], vs_pair[0], capacity=np.inf)

        # Prune CEs which produce no active variables to speedup computation.
        for ce in self.dependency_graph.cell_executions:
            if mincut_graph.in_degree(ce) == 0:
                mincut_graph.remove_node(ce)

        # Solve min-cut with Ford-Fulkerson.
        cut_value, partition = nx.minimum_cut(mincut_graph, "source", "sink", flow_func=shortest_augmenting_path)

        # Determine the replication plan from the partition.
        vss_to_migrate = set(partition[1]).intersection(self.active_vss)
        ces_to_recompute = set(partition[0]).intersection(self.dependency_graph.cell_executions)

        return vss_to_migrate, ces_to_recompute
