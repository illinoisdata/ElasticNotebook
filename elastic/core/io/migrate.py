from collections import defaultdict

from pathlib import Path

from ipykernel.zmqshell import ZMQInteractiveShell

from elastic.core.common.checkpoint_file import CheckpointFile
from elastic.core.graph.graph import DependencyGraph

from elastic.core.io.filesystem_adapter import FilesystemAdapter

# Default checkpoint location if a file path isn't specified.
FILENAME = "./notebook.pickle"


def migrate(graph: DependencyGraph, shell: ZMQInteractiveShell, vss_to_migrate: set, vss_to_recompute: set,
            ces_to_recompute: set, udfs, filename: str):
    """
        Writes the graph representation of the notebook, migrated variables, and instructions for recomputation as the
        specified file.

        Args:
            graph (DependencyGraph): dependency graph representation of the notebook.
            shell (ZMQInteractiveShell): interactive Jupyter shell storing the state of the current session.
            vss_to_migrate (set): set of VSs to migrate.
            vss_to_recompute (set): set of VSs to recompute.
            ces_to_recompute (set): set of CEs to recompute post-migration.
            filename (str): the location to write the checkpoint to.
            udfs (set): set of user-declared functions.
    """
    # Retrieve variables
    variables = defaultdict(list)
    for vs in vss_to_migrate:
        variables[vs.output_ce].append((vs, shell.user_ns[vs.name]))

    # Retrieve variables to migrate from the current session.
    variables = defaultdict(list)
    for vs in vss_to_migrate:
        variables[vs.output_ce].append((vs, shell.user_ns[vs.name]))

    # Construct checkpoint JSON.
    adapter = FilesystemAdapter()
    metadata = CheckpointFile().with_dependency_graph(graph) \
        .with_variables(variables) \
        .with_vss_to_migrate(vss_to_migrate) \
        .with_vss_to_recompute(vss_to_recompute) \
        .with_ces_to_recompute(ces_to_recompute) \
        .with_udfs(udfs)

    # Write the JSON file to the specified location. Uses the default location if a file path isn't specified.
    if filename:
        print("Checkpoint saved to:", filename)
        adapter.write_all(Path(filename), metadata)
    else:
        adapter.write_all(Path(FILENAME), metadata)
