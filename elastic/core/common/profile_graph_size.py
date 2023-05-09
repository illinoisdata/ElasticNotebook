from elastic.core.graph.graph import DependencyGraph
from elastic.core.common.profile_variable_size import profile_variable_size
import sys


def profile_graph_size(graph: DependencyGraph):
    """
       Profiles the in-memory size of a dependency graph of Elastic Notebook.
       For experiments only.
       Args:
           graph (DependencyGraph): dependency graph to profile.
    """

    # Tally fields in graph
    total_size = sys.getsizeof(graph)
    total_size += sys.getsizeof(graph.cell_executions)
    total_size += profile_variable_size(graph.variable_snapshots)

    # Tally fields in operation events
    for oe in graph.cell_executions:
        total_size += sys.getsizeof(oe.cell_num)
        total_size += sys.getsizeof(oe.cell)
        total_size += sys.getsizeof(oe.cell_runtime)
        total_size += sys.getsizeof(oe.start_time)
        total_size += sys.getsizeof(oe.src_vss)
        total_size += sys.getsizeof(oe.dst_vss)

    # Tally fields in nodes
    for vs_list in graph.variable_snapshots.values():
        for vs in vs_list:
            total_size += sys.getsizeof(vs.name)
            total_size += sys.getsizeof(vs.version)
            total_size += sys.getsizeof(vs.deleted)
            total_size += sys.getsizeof(vs.output_ce)
            total_size += sys.getsizeof(vs.input_ces)
            total_size += sys.getsizeof(vs.size)

    return total_size
