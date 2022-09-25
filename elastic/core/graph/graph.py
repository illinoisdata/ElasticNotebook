#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import logging
from core.notebook.operation_event import OperationEvent
from core.notebook.record_event import RecordEvent
from core.graph.edge import Edge
from core.graph.node_set import NodeSet
from core.graph.recompute import find_edges_to_recompute
from algorithm.selector import Selector

logger = logging.getLogger(__name__)


# A dependency graph is a snapshot of the history of a notebook instance.
class DependencyGraph:
    def __init__(self) -> None:
        # Edges of the dependency graph representing the cell executions (operation events).
        self.edges = []

        # Active nodes are nodes corresponding to the latest instances/versions of each variable (variable snapshots).
        self.active_nodes = []

        # Subset of active nodes requiring recomputation post-migration (due to being trimmed pre-migration).
        self.nodes_to_recompute = []

    def add_edge(self, src: NodeSet, dst: NodeSet, oe: OperationEvent):
        edge = Edge(oe, src, dst)
        self.edges.append(edge)
        src.edge = edge
        dst.edge = edge

    # Reduce the size of the graph for migration by deleting the contents of some nodes (and recomputing them post-
    # migration).

    def trim_graph(self, selector):
        selector.dependency_graph = self
        selector.active_nodes = self.active_nodes
        nodes_to_migrate = selector.select_nodes()

        print("---------------------------")
        print("Nodes to migrate:")
        for node in nodes_to_migrate:
            print(node.vs.get_name(), node.vs.get_version(), node.vs.get_size())

        self.nodes_to_recompute = set(self.active_nodes) - set(nodes_to_migrate)

        # Delete the contents of the nodes to recompute
        for node in self.nodes_to_recompute:
            node.vs.clear_item()

    # Recompute non-migrated nodes post-migration by re-executing some cells.
    def recompute_graph(self):
        edges_to_recompute = find_edges_to_recompute(self)
        edges_to_recompute.sort(key=lambda x: x.oe.start)
        for edge in edges_to_recompute:
            print("Recomputing edge " + edge.oe.cell_func_name + "...")

            # declare input nodes into the kernel
            for node in edge.src.nodes:
                exec(node.vs.get_name() + "=node.vs.get_item()")

            # Run cell code
            output_variable_snapshot_set = edge.oe.cell_func_obj().variable_snapshots

            # Assign outputs to output nodes
            for node in edge.dst.nodes:
                node.vs.set_item(output_variable_snapshot_set[node.vs.get_name()])

        # Clear old versions of variables
        for edge in edges_to_recompute:
            for node in edge.dst.nodes:
                if node not in self.active_nodes:
                    node.vs.clear_item()

    # Declares active nodes and functions into the kernel.
    def reconstruct_notebook(self):
        for node in self.active_nodes:
            exec("{} = node.vs".format(node.vs.get_name()))

        for edge in self.edges:
            exec("{} = edge.oe.cell_func_code".format(edge.oe.cell_func_name))
