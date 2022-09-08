#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from typing import List
from algorithm.selector import Selector
from core.graph.graph import DependencyGraph
from core.graph.node import Node
from core.graph.edge import Edge
from core.graph.node_set import NodeSet
import networkx as nx
import numpy as np

class OptimizerGreedy(Selector):
    def __init__(self, dependency_graph: DependencyGraph,
                 active_nodes: List[Node]):
        super().__init__(dependency_graph, active_nodes)
        self.active_nodes = set(self.active_nodes)
        
        self.compute_graph = None
        self.active_node_sets = set()

        self.idx_to_node_set = {}

        self.recomputation_cost = {}
        self.migration_cost = {}

        self.migration_speed = 1

    # Construct compute graph from node sets
    def construct_graph(self):
        self.compute_graph = nx.DiGraph()
        srcs = []
        dsts = []
        idx = 0
        for edge in self.dependency_graph.edges:
            self.compute_graph.add_node(idx)
            self.compute_graph.add_node(idx + 1)
            self.compute_graph.add_edge(idx, idx + 1, weight = edge.duration)

            self.idx_to_node_set[idx] = edge.src
            self.idx_to_node_set[idx + 1] = edge.dst

            srcs.append(idx)
            dsts.append(idx + 1)

            idx += 2

        # Augment compute graph with edges between overlapping destination and source sets
        for dst in dsts:
            for src in srcs:
                if set(self.idx_to_node_set[dst].nodes).intersection(
                    set(self.idx_to_node_set[src].nodes)):
                    self.compute_graph.add_edge(dst, src, weight = 0)

    # Find active node sets consisting entirely of active nodes
    def construct_active_node_sets(self):
        for idx in self.compute_graph.nodes():
            if set(self.idx_to_node_set[idx].nodes).issubset(self.active_nodes):
                self.active_node_sets.add(idx)

    # Construct migration costs of node sets
    def construct_migration_costs(self):
        for idx in self.compute_graph.nodes():
            self.migration_cost[idx] = set(self.idx_to_node_set[idx].nodes)

    def dfs(self, current, visited, recompute_edges):
        visited.add(current)
        for parent in self.compute_graph.predecessors(current):
            recompute_edges.add((parent, current))
            if parent not in self.active_nodes and parent not in visited:
                self.dfs(parent, visited, recompute_edges)
                
    # Construct recomputation costs of node sets
    def construct_recomputation_costs(self):
        for idx in self.compute_graph.nodes():
            recompute_edges = set()
            self.dfs(idx, set(), recompute_edges)
            self.recomputation_cost[idx] = recompute_edges

    def compute_migration_cost(self, node_sets):
        migrate_nodes = set().union(*[self.migration_cost[i] for i in node_sets])
        return sum([i.size for i in migrate_nodes]) * self.migration_speed

    def compute_recomputation_cost(self, node_sets):
        recompute_edges = set().union(*[self.recomputation_cost[i]
                                        for i in node_sets])
        return sum([self.compute_graph.get_edge_data(*i)["weight"]
                    for i in recompute_edges])

    def total_cost(self, migrated_node_sets):
        return self.compute_migration_cost(migrated_node_sets) + \
               self.compute_recomputation_cost(
                   self.active_node_sets.difference(migrated_node_sets))
        
    def select_nodes(self):
        self.construct_graph()
        self.construct_active_node_sets()
        self.construct_migration_costs()
        self.construct_recomputation_costs()

        # start with migrating all, greedily un-migrate node sets
        migrated_node_sets = set()
        for node_set in self.active_node_sets:
            migrated_node_sets.add(node_set)

        while True:
            best_decrease = -np.inf
            best_set = None
            current_score = self.total_cost(migrated_node_sets)
            for node_set in migrated_node_sets:
                decrease = current_score - self.total_cost(
                    migrated_node_sets.difference({node_set}))
                if decrease > best_decrease:
                    best_decrease = decrease
                    best_set = node_set

            if best_decrease < 0:
                break
            migrated_node_sets = migrated_node_sets.difference({best_set})
            
        return [self.idx_to_node_set[i] for i in list(migrated_node_sets)]
