#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from typing import List
from core.graph.graph import DependencyGraph
from core.graph.node import Node


class Selector:
    """
        The `Selector` class provides interfaces to pick a subset of active nodes to migrate based on
            various heuristics and algorithms.
    """
    def __init__(self, dependency_graph: DependencyGraph, active_nodes: List[Node]):
        self.dependency_graph = dependency_graph
        self.active_nodes = active_nodes

    def select_nodes(self):
        """
            Classes that inherit from the `Selector` class (such as `Optimizer` and various baselines)
                should override `select_nodes`

            Returns:
                List[Node]: a subset of active nodes selected to migrate based on various heuristics and algorithms
        """
        raise NotImplementedError()
