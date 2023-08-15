import time

from IPython import get_ipython
from IPython.utils.capture import capture_output
from ipykernel.zmqshell import ZMQInteractiveShell

from elastic.core.graph.graph import DependencyGraph


def restore_notebook(graph: DependencyGraph, shell: ZMQInteractiveShell,
                     variables: dict, ces_to_recompute: set, write_log_location=None, notebook_name=None,
                     optimizer_name=None):
    """
        Restores the notebook. Declares variables back into the kernel and recomputes the CEs to restore non-migrated
        variables.
        Args:
            graph (DependencyGraph): dependency graph representation of the notebook.
            shell (ZMQInteractiveShell): interactive Jupyter shell storing the state of the current session.
            variables (Dict): Mapping from OEs to lists of variables defined in those OEs.
            oes_to_recompute (set): OEs to recompute to restore non-migrated variables.
            write_log_location (str): location to write component runtimes to. For experimentation only.
            notebook_name (str): notebook name. For experimentation only.
            optimizer_name (str): optimizer name. For experimentation only.
    """

    # Recompute OEs following the order they were executed in.
    recompute_start = time.time()
    for ce in graph.cell_executions:
        if ce in ces_to_recompute:
            # Rerun cell code; suppress stdout when rerunning.
            print("Rerunning cell", ce.cell_num + 1)
            cell_capture = capture_output(stdout=True, stderr=True, display=True)
            try:
                with cell_capture:
                    get_ipython().run_cell(ce.cell)
            except Exception as e:
                raise e
        
        # Define output variables in the CE.
        for pair in variables[ce.cell_num]:
            print("Declaring variable", pair[0].name)
            shell.user_ns[pair[0].name] = pair[1]
    
    recompute_end = time.time()

    if write_log_location:
        with open(write_log_location + '/output_' + notebook_name + '_' + optimizer_name + '.txt', 'a') as f:
            f.write('Recompute stage took - ' + repr(recompute_end - recompute_start) + " seconds" + '\n')

