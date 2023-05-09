import json
from typing import Dict
from elastic.core.graph.graph import DependencyGraph

KEY_DEPENDENCY_GRAPH = "dependencyGraph"
KEY_VARIABLES = "variables"
KEY_VSS_TO_MIGRATE = "vss_to_migrate"
KEY_VSS_TO_RECOMPUTE = "vss_to_recompute"
KEY_CES_TO_RECOMPUTE = "ces_to_recompute"
KEY_UDFS = "udfs"


class CheckpointFile:
    """
        JSON representation of the notebook checkpoint.
    """
    def __init__(self):
        # Dependency graph representation of the notebook.
        self.dependency_graph = None

        # Migrated variables.
        self.variables = None

        # Active VSs corresponding to migrated variables.
        self.vss_to_migrate = None

        # Variables to recompute post-migration.
        self.vss_to_recompute = None

        # CEs to recompute to restore non-migrated variables (vss_to_recompute).
        self.ces_to_recompute = None

        # User-declared functions in the session.
        self.udfs = None

    def with_dependency_graph(self, graph: DependencyGraph):
        self.dependency_graph = graph
        return self

    def get_dependency_graph(self):
        return self.dependency_graph

    def with_variables(self, variables: Dict):
        self.variables = variables
        return self

    def get_variables(self):
        return self.variables

    def with_vss_to_migrate(self, vss_to_migrate: set):
        self.vss_to_migrate = vss_to_migrate
        return self

    def get_vss_to_migrate(self):
        return self.vss_to_migrate

    def with_vss_to_recompute(self, vss_to_recompute: set):
        self.vss_to_recompute = vss_to_recompute
        return self

    def get_vss_to_recompute(self):
        return self.vss_to_recompute

    def with_ces_to_recompute(self, ces_to_recompute: set):
        self.ces_to_recompute = ces_to_recompute
        return self

    def get_ces_to_recompute(self):
        return self.ces_to_recompute

    def with_udfs(self, udfs: set):
        self.udfs = udfs
        return self

    def get_udfs(self):
        return self.udfs

    def to_json_str(self) -> str:
        return json.dumps({
            KEY_DEPENDENCY_GRAPH: self.dependency_graph,
            KEY_VARIABLES: self.variables,
            KEY_VSS_TO_MIGRATE: self.vss_to_migrate,
            KEY_VSS_TO_RECOMPUTE: self.vss_to_recompute,
            KEY_CES_TO_RECOMPUTE: self.ces_to_recompute,
            KEY_UDFS: self.udfs
        })

    @staticmethod
    def from_json(kv: Dict):
        return CheckpointFile().with_dependency_graph(kv[KEY_DEPENDENCY_GRAPH])\
                                  .with_variables(kv[KEY_VARIABLES])\
                                  .with_vss_to_migrate(kv[KEY_VSS_TO_MIGRATE])\
                                  .with_vss_to_recompute(kv[KEY_VSS_TO_RECOMPUTE])\
                                  .with_ces_to_recompute(kv[KEY_CES_TO_RECOMPUTE])\
                                  .with_udfs(kv[KEY_UDFS])
