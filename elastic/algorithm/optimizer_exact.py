#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from elastic.algorithm.selector import Selector
from elastic.core.graph.variable_snapshot import VariableSnapshot
from elastic.core.graph.cell_execution import CellExecution
import networkx as nx
from networkx.algorithms.flow import shortest_augmenting_path
import numpy as np

from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_flow


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

        # OEs required to recompute a given OE.
        self.recomputation_oes = {}

        self.idx = 0

    def get_new_idx(self) -> int:
        """
            Get a new index number to add to compute graph.
        """
        idx = self.idx
        self.idx += 1
        return idx

    def dfs(self, current: str, visited: set, recompute_oes: str):
        """
            DFS helper for finding the OEs required to recompute a node set.
            Args:
                current (str): Name of current nodeset.
                visited (set): Visited nodesets.
                recompute_oes (set): Set of OEs needing re-execution to recompute the cirremt nodeset.
        """
        if isinstance(current, CellExecution):
            if current in self.active_oes:
                recompute_oes.update(self.recomputation_oes[current])
            else:
                recompute_oes.add(current)
                for vs in current.src_vss:
                    if vs not in self.active_vss and vs not in visited:
                        self.dfs(vs, visited, recompute_oes)
        elif isinstance(current, VariableSnapshot):
            if current.output_ce not in recompute_oes:
                self.dfs(current.output_ce, visited, recompute_oes)

    def find_prerequisites(self):
        """
            Find the necessary (prerequisite) cell executions to rerun a cell execution.
        """
        self.active_vss = set(self.active_vss)

        self.active_oes = set()
        for oe in self.dependency_graph.operation_events:
            if oe.dst_vss.intersection(self.active_vss):
                self.recomputation_oes[oe] = set()
                self.dfs(oe, set(), self.recomputation_oes[oe])
                self.active_oes.add(oe)

    def select_vss(self) -> set:
        self.find_prerequisites()

        # Construct flow graph for computing mincut
        mincut_graph = nx.DiGraph()
        # mincut_graph = graph_tool.Graph()
        # mincut_graph.edge_properties['cap'] = mincut_graph.new_edge_property('double')

        # Find all active VSs and OEs.
        all_oes = set().union(*[self.recomputation_oes[i] for i in self.active_oes])

        # Add source and sink to flow graph.
        mincut_graph.add_node("source")
        mincut_graph.add_node("sink")
        # source = mincut_graph.add_vertex()
        # sink = mincut_graph.add_vertex()

        # Add all active VSs as nodes, connect them with the source with edge capacity equal to common cost.
        for active_vs in self.active_vss:
            mincut_graph.add_node(active_vs)
            mincut_graph.add_edge("source", active_vs, capacity=active_vs.size / self.migration_speed_bps)

        # Add OEs outputting active VSs as nodes.
        for oe in self.active_oes:
            mincut_graph.add_node(oe)
            mincut_graph.add_edge("source", oe, capacity=sum(
                [active_node.size for active_node in oe.dst_vss]) / self.migration_speed_bps)

        # Add all OEs as nodes, connect them with the sink with edge capacity equal to recomputation cost.
        for oe in all_oes:
            mincut_graph.add_node(oe)
            mincut_graph.add_edge(oe, "sink", capacity=oe.cell_runtime)

        # Connect each OE with its output variables and its prerequisite OEs.
        for oe in self.active_oes:
            for active_vs in oe.dst_vss:
                mincut_graph.add_edge(active_vs, oe, capacity=np.inf)
            for prereq in self.recomputation_oes[oe]:
                mincut_graph.add_edge(oe, prereq, capacity=np.inf)

        # Add constraints: overlapping variables must either be migrated or recomputed together.
        for vs_pair in self.overlapping_vss:
            mincut_graph.add_edge(vs_pair[0], vs_pair[1], capacity=np.inf)
            mincut_graph.add_edge(vs_pair[1], vs_pair[0], capacity=np.inf)

        # Run min-cut.
        cut_value, partition = nx.minimum_cut(mincut_graph, "source", "sink", flow_func=shortest_augmenting_path)
        vss_to_migrate = set(partition[1]).intersection(self.active_vss)
        oes_to_recompute = set(partition[0]).intersection(all_oes)

        return vss_to_migrate, oes_to_recompute
