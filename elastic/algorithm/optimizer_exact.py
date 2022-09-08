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
import scipy.optimize as optimize
import random
import math

class OptimizerExact(Selector):
    def __init__(self, dependency_graph: DependencyGraph,
                 active_nodes: List[Node]):
        super().__init__(dependency_graph, active_nodes)
        self.active_nodes = set(self.active_nodes)
        
        self.compute_graph = None
        self.active_node_sets = set()

        self.idx_to_node_set = {}

        self.recomputation_cost = {}
        self.migration_cost = {}
        self.migrate_none_cost = 0

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

    def normalize(self):
        self.migrate_none_cost = \
            self.compute_recomputation_cost(self.active_node_sets)

    def total_cost(self, migrated_node_sets):
        return self.compute_migration_cost(migrated_node_sets) + \
               self.compute_recomputation_cost(
                   self.active_node_sets.difference(migrated_node_sets)) - \
                   self.migrate_none_cost

    def lovasz_value(self, current_subset_list, x):
        x_list = list(x)
        x_subset = list(zip(x_list, current_subset_list))
        x_subset.sort(reverse = True)
        x_subset.append((0, None))

        val = (1 - x_subset[0][0]) * self.total_cost(set())
        for i in range(len(x_subset) - 1):
            val += (x_subset[i][0] - x_subset[i + 1][0]) * \
                   self.total_cost(set([x_subset[j][1] for j in range(i + 1)]))
        return val

    def get_min_possible_value(self, current_subset):
        if len(current_subset) == 0:
            return 0
        
        current_subset_list = list(current_subset)
        fun = lambda x: self.lovasz_value(current_subset_list, x)
        bnds = tuple((0, 1) for i in range(len(current_subset_list)))
        res = optimize.minimize(fun, tuple(
            random.random() for i in range(len(current_subset_list))),
                                      method = 'L-BFGS-B', bounds = bnds, tol = 1e-10)

        return fun(res.x)
        
    def select_nodes(self):
        self.construct_graph()
        self.construct_active_node_sets()
        self.construct_migration_costs()
        self.construct_recomputation_costs()
        self.normalize()

        # start with migrating all, greedily un-migrate node sets
        migrated_node_sets = set()
        for node_set in self.active_node_sets:
            migrated_node_sets.add(node_set)

        #print("test:", self.lovasz_value(migrated_node_sets, [1 for _ in range(
        #    len(migrated_node_sets))]))

        while True:
            if len(migrated_node_sets) == 0:
                break
            
            current_min = self.get_min_possible_value(migrated_node_sets)
            #print("current min:", current_min)
            current_score = self.total_cost(migrated_node_sets)
            #print("current score:", current_score)
            
            # If min score is attained by current set then we're done
            if math.isclose(current_score, current_min, rel_tol = 0.00001):
                break
            
            for node_set in migrated_node_sets:
                new_min = self.get_min_possible_value(migrated_node_sets -
                                                 {node_set})
                #print("new min:", new_min)
                # Shrink current set
                if math.isclose(new_min, current_min, rel_tol = 0.00001):
                    migrated_node_sets = migrated_node_sets - {node_set}
                    #print(migrated_node_sets)
                    break
            
        return [self.idx_to_node_set[i] for i in list(migrated_node_sets)]
