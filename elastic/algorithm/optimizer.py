#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from typing import List
from algorithm.selector import Selector
from core.graph.graph import DependencyGraph
from core.graph.node import Node


class Optimizer(Selector):
    def __init__(self, dependency_graph: DependencyGraph, active_nodes: List[Node]):
        super().__init__(dependency_graph, active_nodes)

    def select_nodes(self):
        # FIXME: augment the graph and use the submodularity of the objective to find best set of nodes to migrate
        return []