#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import dis

from elastic.core.graph.graph import DependencyGraph
from elastic.core.graph.node_set import NodeSet, NodeSetType


def update_graph(cell: str, cell_runtime: float, start_time: float, input_variables: set,
                 created_and_modified_variables: set, deleted_variables: set, graph: DependencyGraph):
    """
        Updates the graph according to the newly executed cell and its input and output variables.
        Args:
             cell (str): Raw cell cell.
             cell_runtime (float): Cell runtime.
             start_time (time): Time of start of cell execution. Note that this is different from when the cell was
                 queued.
             input_variables (set): Set of input variables of the cell.
             created_and_modified_variables (set): set of created and modified variables.
             deleted_variables (set): set of deleted variables
             graph (DependencyGraph): Dependency graph representation of the notebook.
    """

    # Retrieve input variable snapshots
    input_vss = set(graph.variable_snapshots[variable][-1] for variable in input_variables)

    # Create output variable snapshots
    output_vss_create = set(graph.create_variable_snapshot(k, 0, False) for k in created_and_modified_variables)
    output_vss_delete = set(graph.create_variable_snapshot(k, 0, True) for k in deleted_variables)

    # Add the newly created OE to the graph.
    graph.add_cell_execution(cell, cell_runtime, start_time, input_vss, output_vss_create.union(output_vss_delete))
