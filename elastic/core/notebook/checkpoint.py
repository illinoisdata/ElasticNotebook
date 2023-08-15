import time
from typing import Dict

import numpy as np
from elastic.algorithm.selector import Selector
from elastic.core.graph.graph import DependencyGraph
from elastic.core.io.migrate import migrate
from elastic.core.io.pickle import is_picklable
from elastic.core.common.profile_variable_size import profile_variable_size
from ipykernel.zmqshell import ZMQInteractiveShell

from elastic.core.mutation.object_hash import UnserializableObj


def checkpoint(graph: DependencyGraph, shell: ZMQInteractiveShell, fingerprint_dict: Dict,
               selector: Selector, udfs: set, filename: str, profile_dict, write_log_location=None, notebook_name=None,
               optimizer_name=None):
    """
        Checkpoints the notebook. The optimizer selects the VSs to migrate and recompute and the OEs to recompute, then
        writes the checkpoint as the specified filename.
        Args:
            graph (DependencyGraph): dependency graph representation of the notebook.
            shell (ZMQInteractiveShell): interactive Jupyter shell storing the state of the current session.
            selector (Selector): optimizer for computing the checkpointing configuration.
            udfs (set): set of user-declared functions.
            filename (str): location to write the file to.
            write_log_location (str): location to write component runtimes to. For experimentation only.
            notebook_name (str): notebook name. For experimentation only.
            optimizer_name (str): optimizer name. For experimentation only.
    """
    profile_start = time.time()

    # Retrieve active VSs from the graph. Active VSs are correspond to the latest instances/versions of each variable.
    active_vss = set()
    for vs_list in graph.variable_snapshots.values():
        if not vs_list[-1].deleted:
            active_vss.add(vs_list[-1])

    # Profile the size of each variable defined in the current session.
    for active_vs in active_vss:
        attr_str = getattr(shell.user_ns[active_vs.name], '__module__', None)
        # Object is unserializable
        if isinstance(fingerprint_dict[active_vs.name][2], UnserializableObj):
            active_vs.size = np.inf

        # Blacklisted object
        elif attr_str and ("dataprep.eda" in attr_str or "bokeh" in attr_str):
            active_vs.size = np.inf

        # Profile size of object.
        else:
            active_vs.size = profile_variable_size(shell.user_ns[active_vs.name])

    # Check for pairwise variable intersections. Variables sharing underlying data must be migrated or recomputed
    # together.
    overlapping_vss = []
    for active_vs1 in active_vss:
        for active_vs2 in active_vss:
            if active_vs1 != active_vs2 and fingerprint_dict[active_vs1.name][1].intersection(
                    fingerprint_dict[active_vs2.name][1]):
                overlapping_vss.append((active_vs1, active_vs2))

    profile_end = time.time()
    if write_log_location:
        with open(write_log_location + '/output_' + notebook_name + '_' + optimizer_name + '.txt', 'a') as f:
            f.write('overlappings - ' + repr(len(overlapping_vss)) + '\n')
            f.write('Profile stage took - ' + repr(profile_start - profile_end) + " seconds" + '\n')
            f.write('Idgraph stage took - ' + repr(profile_dict["idgraph"]) + " seconds" + '\n')
            f.write('Representation stage took - ' + repr(profile_dict["representation"]) + " seconds" + '\n')

    optimize_start = time.time()
    # Initialize the optimizer.
    add_start = time.time()
    selector.dependency_graph = graph
    selector.active_vss = active_vss
    selector.overlapping_vss = overlapping_vss
    add_end = time.time()

    # Use the optimizer to compute the checkpointing configuration.
    opt_start = time.time()
    vss_to_migrate, ces_to_recompute = selector.select_vss(write_log_location, notebook_name, optimizer_name)
    opt_end = time.time()
    print("---------------------------")
    print("variables to migrate:")
    for vs in vss_to_migrate:
        print(vs.name, vs.size)

    difference_start = time.time()
    vss_to_recompute = active_vss - vss_to_migrate
    difference_end = time.time()

    print("---------------------------")
    print("variables to recompute:")
    for vs in vss_to_recompute:
        print(vs.name, vs.size)
    print([vs.name for vs in vss_to_recompute])

    print("---------------------------")
    print("cells to recompute:")
    for ce in ces_to_recompute:
        print(ce.cell_num, ce.cell_runtime)
    print(sorted([ce.cell_num + 1 for ce in ces_to_recompute]))

    optimize_end = time.time()
    if write_log_location:
        with open(write_log_location + '/output_' + notebook_name + '_' + optimizer_name + '.txt', 'a') as f:
            f.write('Optimize stage took - ' + repr(optimize_end - optimize_start) + " seconds" + '\n')
            f.write('  Add stage took - ' + repr(add_end - add_start) + " seconds" + '\n')
            f.write('  Opt stage took - ' + repr(opt_end - opt_start) + " seconds" + '\n')
            f.write('  Diff stage took - ' + repr(difference_end - difference_start) + " seconds" + '\n')

    # Store the notebook checkpoint to the specified location.
    migrate_start = time.time()
    migrate_success = True
    migrate(graph, shell, vss_to_migrate, vss_to_recompute, ces_to_recompute, udfs, selector.recomputation_ces, selector.overlapping_vss, filename)
    migrate_end = time.time()

    if write_log_location:
        with open(write_log_location + '/output_' + notebook_name + '_' + optimizer_name + '.txt', 'a') as f:
            f.write('Migrate stage took - ' + repr(migrate_end - migrate_start) + " seconds" + '\n')
    return migrate_success
