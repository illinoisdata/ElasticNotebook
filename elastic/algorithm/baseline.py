#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import random
from typing import List
from algorithm.selector import Selector
from core.graph.graph import DependencyGraph
from core.graph.node import Node


class MigrateAllBaseline(Selector):
    def __init__(self, dependency_graph: DependencyGraph, active_nodes: List[Node]):
        super().__init__(dependency_graph, active_nodes)

    def select_nodes(self):
        """
        Returns:
            List[Node]: the list of all active nodes are returned so that they are all migrated
        """
        return self.active_nodes


class RecomputeAllBaseline(Selector):
    def __init__(self, dependency_graph: DependencyGraph, active_nodes: List[Node]):
        super().__init__(dependency_graph, active_nodes)

    def select_nodes(self):
        """
        Returns:
            List[Node]: the empty list is returned so that no active nodes are migrated and all recomputed
        """
        return []


class RandomBaseline(Selector):
    def __init__(self, dependency_graph: DependencyGraph, active_nodes: List[Node]):
        super().__init__(dependency_graph, active_nodes)

    def select_nodes(self):
        """
        Returns:
            List[Node]: a random subset of active nodes is returned
        """
        # NOTE: when this selector is used, the caller should fix a particular seed, for example in the 
        #   automation script for benchmarking
        return random.sample(self.active_nodes)
