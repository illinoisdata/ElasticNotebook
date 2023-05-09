import numpy as np

from elastic.algorithm.selector import Selector


class MigrateAllBaseline(Selector):
    """
        Migrates all active VSs.
    """
    def __init__(self, migration_speed_bps=1):
        super().__init__(migration_speed_bps)

    def select_vss(self) -> set:
        vss_to_migrate = set()
        for vs in self.active_vss:
            if vs.size < np.inf:
                vss_to_migrate.add(vs)
        return vss_to_migrate


class RecomputeAllBaseline(Selector):
    """
        Recomputes all active VSs.
    """
    def __init__(self, migration_speed_bps=1):
        super().__init__(migration_speed_bps)

    def select_vss(self) -> set:
        return set()
