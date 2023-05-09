import logging
from collections import defaultdict
from typing import List

from elastic.core.graph.variable_snapshot import VariableSnapshot
from elastic.core.graph.cell_execution import CellExecution


class DependencyGraph:
    """
        A dependency graph is a snapshot of the history of a notebook instance.
        Nodesets and operation events are the nodes and edges of the dependency graph.
    """
    def __init__(self):
        """
            Create a new dependency graph. Called when the magic extension of elastic notebook is loaded with %load_ext.
        """
        # Cell executions.
        self.cell_executions = []

        # Dict of variable snapshots.
        # Keys are variable names, while values are lists of the actual VSs.
        # i.e. {"x": [(x, 1), (x, 2)], "y": [(y, 1), (y, 2), (y, 3)]}
        self.variable_snapshots = defaultdict(list)

    def create_variable_snapshot(self, variable_name: str, deleted: bool) -> VariableSnapshot:
        """
            Creates a new variable snapshot for a given variable.
            Args:
                variable_name (str): variable_name
                deleted (bool): Whether this VS is created for the deletion of a variable, i.e. 'del x'.
        """

        # Assign a version number to the VS.
        if variable_name in self.variable_snapshots:
            version = len(self.variable_snapshots[variable_name])
        else:
            version = 0

        # Create a new VS instance and store it in the graph.
        vs = VariableSnapshot(variable_name, version, deleted)
        self.variable_snapshots[variable_name].append(vs)
        return vs

    def add_cell_execution(self, cell, cell_runtime: float, start_time: float, src_vss: List, dst_vss: List):
        """
            Create a cell execution from captured metrics.
            Args:
                cell (str): Raw cell cell.
                cell_runtime (float): Cell runtime.
                start_time (time): Time of start of cell execution. Note that this is different from when the cell was
                    queued.
                src_vss (List): List containing input VSs of the cell execution.
                dst_vss (List): List containing output VSs of the cell execution.
        """

        # Create a cell execution.
        ce = CellExecution(len(self.cell_executions), cell, cell_runtime, start_time, src_vss, dst_vss)

        # Add the newly created cell execution to the graph.
        self.cell_executions.append(ce)

        # Set the newly created cell execution as dependent on its input variable snapshots.
        for src_vs in src_vss:
            src_vs.input_ces.append(ce)

        # Set the newly created cell execution as the parent of its output variable snapshots.
        for dst_vs in dst_vss:
            dst_vs.output_ce = ce
