from __future__ import print_function

import sys, traceback
import time
import types
from os.path import dirname
from pympler import asizeof

from IPython import get_ipython
from IPython.core.magic import (Magics, magics_class, cell_magic, line_magic)
from elastic.algorithm.selector import OptimizerType

from elastic.core.common.profile_migration_speed import profile_migration_speed
from elastic.core.common.profile_graph_size import profile_graph_size
from elastic.core.notebook.checkpoint import checkpoint
from elastic.core.notebook.update_graph import update_graph
from elastic.core.notebook.find_input_vars import find_input_vars
from elastic.core.notebook.find_output_vars import find_created_deleted_vars
from elastic.core.mutation.fingerprint import construct_fingerprint, compare_fingerprint
from elastic.core.mutation.object_hash import UnserializableObj
from elastic.core.notebook.restore_notebook import restore_notebook

from elastic.core.graph.graph import DependencyGraph
from elastic.core.io.recover import resume

from elastic.algorithm.optimizer_exact import OptimizerExact
from elastic.algorithm.baseline import RecomputeAllBaseline, MigrateAllBaseline


@magics_class
class ElasticNotebook(Magics):
    """
        Magics class for Elastic Notebook. Enable this in the notebook by running '%load_ext ElasticNotebook'.
        Enables efficient checkpointing of intermediate notebook state via balancing migration and recomputation
        costs.
    """

    def __init__(self, shell):
        super(ElasticNotebook, self).__init__(shell=shell)
        self.shell.configurables.append(self)

        # Initialize the dependency graph for capturing notebook state.
        self.dependency_graph = DependencyGraph()

        # Migration properties.
        self.migration_speed_bps = 100000
        self.alpha = 1
        self.selector = OptimizerExact(migration_speed_bps=self.migration_speed_bps)

        # Dictionary of object fingerprints. For detecting modified references.
        self.fingerprint_dict = {}

        # Set of user-declared functions.
        self.udfs = set()

        # Flag if migration speed has been manually set. In this case, skip profiling of migration speed at checkpoint
        # time.
        self.manual_migration_speed = False

        # Location to log runtimes to. For experiments only.
        self.write_log_location = None

        # Strings for determining log filename. For experiments only.
        self.optimizer_name = ""
        self.notebook_name = ""

        # Total elapsed time spent inferring cell inputs and outputs.
        # For measuring overhead.
        self.total_recordevent_time = 0

        # Dict for recording overhead of profiling operations.
        self.profile_dict = {"idgraph": 0, "representation": 0}

    @cell_magic
    def RecordEvent(self, line, cell):
        """
            Cell magic for recording cell execution. Put %%RecordEvent at the 1st line of cells to record.
            Args:
                line: unused.
                cell: cell content.
        """
        pre_execution = set(self.shell.user_ns.keys())

        # Create id trees for output variables
        for var in self.dependency_graph.variable_snapshots.keys():
            if var not in self.fingerprint_dict and var in self.shell.user_ns:
                self.fingerprint_dict[var] = construct_fingerprint(self.shell.user_ns[var], self.profile_dict)

        # Find input variables (variables potentially accessed) of the cell.
        input_variables, function_defs = find_input_vars(cell, set(self.dependency_graph.variable_snapshots.keys()),
                                                         self.shell, self.udfs)
        # Union of ID graphs of input variables. For detecting modifications to unserializable variables.
        input_variables_id_graph_union = set()
        for var in input_variables:
            if var in self.fingerprint_dict:
                input_variables_id_graph_union = input_variables_id_graph_union.union(self.fingerprint_dict[var][1])

        # Run the cell.
        start_time = time.time()
        try:
            cell_output = get_ipython().run_cell(cell)
            cell_output.raise_error()
            traceback_list = []
        except:
            _, _, tb = sys.exc_info()
            traceback_list = traceback.extract_tb(tb).format()
        cell_runtime = time.time() - start_time
        post_execution = set(self.shell.user_ns.keys())
        infer_start = time.time()

        # Find created and deleted variables by computing difference between namespace pre and post execution.
        created_variables, deleted_variables = find_created_deleted_vars(pre_execution, post_execution)

        # Remove stored ID graphs for deleted variables.
        for var in deleted_variables:
            del self.fingerprint_dict[var]
            if var in self.udfs:
                self.udfs.remove(var)

        # Find modified variables by comparing ID graphs and object hashes.
        modified_variables = set()
        for k, v in self.fingerprint_dict.items():
            changed, overwritten = compare_fingerprint(self.fingerprint_dict[k], self.shell.user_ns[k],
                                                       self.profile_dict, input_variables_id_graph_union)
            if changed:
                modified_variables.add(k)

            # In the case of non-overwrite modification, the variable is additionally considered as accessed.
            if changed and not overwritten:
                input_variables.add(k)

            # A user defined function has been overwritten.
            elif overwritten and k in self.udfs:
                self.udfs.remove(k)

            # Select unserializable variables are assumed to be modified if accessed.
            if not changed and not overwritten and isinstance(self.fingerprint_dict[k][2], UnserializableObj):
                if self.fingerprint_dict[k][1].intersection(input_variables_id_graph_union):
                    modified_variables.add(k)

        # Create ID graphs for output variables
        for var in created_variables:
            self.fingerprint_dict[var] = construct_fingerprint(self.shell.user_ns[var], self.profile_dict)

        # Record newly defined UDFs
        for udf in function_defs:
            if udf in self.shell.user_ns and isinstance(self.shell.user_ns[udf], types.FunctionType):
                self.udfs.add(udf)

        # Update the dependency graph.
        update_graph(cell, cell_runtime, start_time, input_variables, created_variables.union(modified_variables),
                     deleted_variables, self.dependency_graph)

        # Update total recordevent time tally.
        infer_end = time.time()
        self.total_recordevent_time += infer_end - infer_start

    @line_magic
    def SetMigrationSpeed(self, migration_speed=''):
        """
            %SetMigrationSpeed x: Sets the migration speed to x. Can be used when the user has a reasonable estimation
            of the migration speed.
            Args:
                migration_speed: migration speed in bytes per second.
        """

        try:
            if float(migration_speed) > 0:
                self.migration_speed_bps = float(migration_speed)
                self.manual_migration_speed = True
            else:
                print("Migration speed is not positive.")
        except ValueError:
            print("Migration speed is not a number.")
        self.selector.migration_speed_bps = self.migration_speed_bps

    @line_magic
    def SetOptimizer(self, optimizer=''):
        """
            %SetOptimizer optimizer: Sets the optimization method to use for computing checkpointing configuration to
            'optimizer'.
            Args:
                optimizer: Optimizer to use.
        """
        self.optimizer_name = optimizer

        if optimizer == OptimizerType.EXACT.value:
            self.selector = OptimizerExact(self.migration_speed_bps)
            self.alpha = 1
        elif optimizer == OptimizerType.EXACT_C.value:
            self.selector = OptimizerExact(self.migration_speed_bps)
            self.alpha = 20
        elif optimizer == OptimizerType.EXACT_R.value:
            self.selector = OptimizerExact(self.migration_speed_bps)
            self.alpha = 0.05
        elif optimizer == OptimizerType.MIGRATE_ALL.value:
            self.selector = MigrateAllBaseline(self.migration_speed_bps)
        elif optimizer == OptimizerType.RECOMPUTE_ALL.value:
            self.selector = RecomputeAllBaseline(self.migration_speed_bps)

    @line_magic
    def SetWriteLogLocation(self, filename=''):
        """
            Sets the location to log runtimes to. For experiments only.
        """
        self.write_log_location = filename

    @line_magic
    def SetNotebookName(self, name=''):
        """
            Sets the notebook name for the log file. For experiments only.
        """
        self.notebook_name = name

    @line_magic
    def Checkpoint(self, filename=''):
        """
            %Checkpoint file.pickle: Checkpoints the notebook to the specified location.
            Args:
                filename: File to write checkpoint to. If empty, writes to a default location (see io/migrate.py).
        """

        # Write overhead metrics to file (for experiments).
        if self.write_log_location:
            with open(self.write_log_location + '/output_' + self.notebook_name + '_' +
                      self.optimizer_name + '.txt', 'a') as f:
                f.write('comparison overhead - ' + repr(asizeof.asizeof(self.dependency_graph) +
                                                        asizeof.asizeof(self.fingerprint_dict)) + ' bytes' + '\n')
                f.write('notebook overhead - ' + repr(asizeof.asizeof(self.shell.user_ns)) + ' bytes' + '\n')
                f.write('Dependency graph storage overhead - ' + repr(profile_graph_size(self.dependency_graph)) +
                        " bytes" + '\n')
                f.write('Cell monitoring overhead - ' + repr(self.total_recordevent_time) + " seconds" + '\n')

        # Profile the migration speed to filename.
        if not self.manual_migration_speed:
            self.migration_speed_bps = profile_migration_speed(dirname(filename), alpha=self.alpha)
            self.selector.migration_speed_bps = self.migration_speed_bps

        # Checkpoint the notebook.
        checkpoint(self.dependency_graph, self.shell, self.fingerprint_dict, self.selector, self.udfs,
                   filename, self.profile_dict, self.write_log_location, self.notebook_name, self.optimizer_name)

    @line_magic
    def LoadCheckpoint(self, filename=''):
        """
            %LoadCheckpoint file.pickle: Load a checkpoint file and restore notebook state.
            Args:
                filename: File to read checkpoint from. If empty, reads from a default location (see io/migrate.py).
        """
        self.dependency_graph, variables, vss_to_migrate, vss_to_recompute, oes_to_recompute, self.udfs = \
            resume(filename, self.write_log_location, self.notebook_name, self.optimizer_name)

        # Recompute missing VSs and redeclare variables into the kernel.
        restore_notebook(self.dependency_graph, self.shell, variables, oes_to_recompute, self.write_log_location,
                         self.notebook_name, self.optimizer_name)


def load_ipython_extension(ipython):
    """
        Load the extension.
    """
    ipython.register_magics(ElasticNotebook)
