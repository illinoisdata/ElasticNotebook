#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from elastic.algorithm.selector import Selector
from elastic.core.graph.node_set import NodeSet
from elastic.core.graph.node_set import NodeSetType
import networkx as nx
import numpy as np


class OptimizerExact(Selector):
    """
        The exact optimizer constructs a flow graph and runs the min-cut algorithm to exactly find the best
        checkpointing configuration.
    """
    def __init__(self, migration_speed_bps=1):
        super().__init__(migration_speed_bps)

        # Augmented computation graph
        self.compute_graph = None

        # A node set is active if all of its nodes are active.
        self.active_node_sets = set()

        # Unique index number assigned to node sets to speedup lookup
        self.idx_to_node_set = {}

        # OEs required to recompute a give nodeset.
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
        visited.add(current)
        for parent in self.compute_graph.predecessors(current):
            if self.compute_graph.get_edge_data(parent, current)["weight"] != 0:
                recompute_oes.add((parent, current))
            if parent not in self.active_node_sets and parent not in visited:
                self.dfs(parent, visited, recompute_oes)

    def construct_graph(self):
        """
            Construct the augmented dependency graph.
        """
        self.compute_graph = nx.DiGraph()
        self.active_vss = set(self.active_vss)
        self.idx_to_node_set = {}
        self.idx = 0

        srcs = []
        dsts = []

        for oe in self.dependency_graph.operation_events:
            # Add source and destination node sets to graph
            src_idx = self.get_new_idx()
            dst_idx = self.get_new_idx()

            self.compute_graph.add_node(src_idx)
            self.compute_graph.add_node(dst_idx)

            self.idx_to_node_set[src_idx] = oe.src
            self.idx_to_node_set[dst_idx] = oe.dst

            srcs.append(src_idx)
            dsts.append(dst_idx)

            self.compute_graph.add_edge(src_idx, dst_idx, weight=oe.cell_runtime)

        # Augment compute graph by connecting overlapping destination and source sets
        for dst in dsts:
            has_successor = False
            for src in srcs:
                # Create intermediate nodeset for inter-cell dependencies
                if set(self.idx_to_node_set[dst].vs_list).intersection(
                        set(self.idx_to_node_set[src].vs_list)):
                    has_successor = True
                    vs_intersection = set(self.idx_to_node_set[dst].vs_list).intersection(
                        self.idx_to_node_set[src].vs_list)
                    vs_intersection_idx = self.get_new_idx()
                    self.idx_to_node_set[vs_intersection_idx] = NodeSet(list(vs_intersection), NodeSetType.DUMMY)

                    self.compute_graph.add_node(vs_intersection_idx)
                    self.compute_graph.add_edge(dst, vs_intersection_idx, weight=0)
                    self.compute_graph.add_edge(vs_intersection_idx, src, weight=0)

            # Create nodeset with subset of active nodes if no successors
            if not has_successor:
                active_vs_subset = set(self.idx_to_node_set[dst].vs_list).intersection(self.active_vss)
                active_vs_subset_idx = self.get_new_idx()
                self.idx_to_node_set[active_vs_subset_idx] = NodeSet(list(active_vs_subset), NodeSetType.DUMMY)

                self.compute_graph.add_node(active_vs_subset_idx)
                self.compute_graph.add_edge(dst, active_vs_subset_idx, weight=0)

        # Find active node sets consisting entirely of active nodes
        for idx in self.compute_graph.nodes():
            if set(self.idx_to_node_set[idx].vs_list).issubset(self.active_vss) \
                    and len(set(self.idx_to_node_set[idx].vs_list)) > 0:
                self.active_node_sets.add(idx)

        # Find edges required to recompute each node set given all active node sets are migrated
        for idx in self.compute_graph.nodes():
            recompute_oes = set()
            self.dfs(idx, set(), recompute_oes)
            self.recomputation_oes[idx] = recompute_oes
        
    def select_vss(self) -> set:
        self.construct_graph()

        # Construct flow graph for computing mincut
        mincut_graph = nx.DiGraph()

        # Find all active VSs and OEs.
        all_active_vss = set().union(*[self.idx_to_node_set[i].vs_list for i in self.active_node_sets])
        all_oes = set().union(*[self.recomputation_oes[i] for i in self.active_node_sets])

        # Add source and sink to flow graph.
        mincut_graph.add_node("source")
        mincut_graph.add_node("sink")

        # Add all active VSs as nodes, connect them with the source with edge capacity equal to common cost.
        for active_vs in all_active_vss:
            mincut_graph.add_node(active_vs)
            mincut_graph.add_edge("source", active_vs, capacity=active_vs.size / self.migration_speed_bps)

        # Add all OEs as nodes, connect them with the sink with edge capacity equal to recomputation cost.
        for oe in all_oes:
            mincut_graph.add_node(oe)
            mincut_graph.add_edge(oe, "sink", capacity=self.compute_graph.get_edge_data(*oe)["weight"])

        # Add all nodesets as nodes, connect them with VSs in the nodesets and OEs required to recompute the nodesets
        # with infinite edge capacity.
        for idx in self.active_node_sets:
            mincut_graph.add_node(idx)
            for active_node in self.idx_to_node_set[idx].vs_list:
                mincut_graph.add_edge(active_node, idx, capacity=np.inf)
            for operation in self.recomputation_oes[idx]:
                mincut_graph.add_edge(idx, operation, capacity=np.inf)

        # Run min-cut.
        cut_value, partition = nx.minimum_cut(mincut_graph, "source", "sink")
        migrated_node_sets = set(partition[1]).intersection(self.active_node_sets)

        # VSs to migrate as the union of the VSs in the nodesets to migrate.
        vss_to_migrate = set()
        for i in list(migrated_node_sets):
            for vs in self.idx_to_node_set[i].vs_list:
                vss_to_migrate.add(vs)
        return vss_to_migrate
