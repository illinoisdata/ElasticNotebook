from elastic.core.graph.graph import DependencyGraph
from elastic.core.graph.variable_snapshot import VariableSnapshot
from elastic.core.graph.cell_execution import CellExecution


def get_test_vs(name: str, ver=0, deleted=False):
    """
        Fast variable snapshot creation with pre-filled fields.
    """
    return VariableSnapshot(name, ver, deleted)


def get_test_ce(cell_num: int, cell="", cell_runtime=1, start_time=1, src_vss=[], dst_vss=[]):
    """
        Fast cell execution creation with pre-filled fields.
    """
    return CellExecution(cell_num, cell, cell_runtime, start_time, src_vss, dst_vss)


def get_problem_setting():
    """
        Returns the graph containing the test problem setting for the optimizers.
        (cost:2) "x"  "y" (cost: 2)
             c3   |    |  c2
                 "z" "z"
                   "z"
                    | c1 (cost: 3)
                   []
    """
    graph = DependencyGraph()

    # Variable snapshots
    vs1 = graph.create_variable_snapshot("x", False)
    vs2 = graph.create_variable_snapshot("y", False)
    vs3 = graph.create_variable_snapshot("z", True)
    vs1.size = 2
    vs2.size = 2
    active_vss = {vs1, vs2}

    # Cell executions
    graph.add_cell_execution("", 3, 0, set(), {vs3})
    graph.add_cell_execution("", 0.1, 0, {vs3}, {vs1})
    graph.add_cell_execution("", 0.1, 0, {vs3}, {vs2})

    return graph, active_vss
