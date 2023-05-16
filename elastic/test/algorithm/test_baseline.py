import unittest

from elastic.algorithm.baseline import MigrateAllBaseline, RecomputeAllBaseline
from elastic.test.test_utils import get_problem_setting


class TestOptimizerBaselines(unittest.TestCase):
    def test_migrate_all(self):
        # Setup problem
        opt = MigrateAllBaseline(migration_speed_bps=1)
        graph, active_vss = get_problem_setting()
        opt.dependency_graph = graph
        opt.active_vss = active_vss

        # Tests that all VSs are migrated.
        vss_to_migrate = opt.select_vss()
        self.assertEqual({graph.variable_snapshots["x"][0], graph.variable_snapshots["y"][0]}, vss_to_migrate)

    def test_recompute_all(self):
        # Setup problem
        opt = RecomputeAllBaseline(migration_speed_bps=1)
        graph, active_vss = get_problem_setting()
        opt.dependency_graph = graph
        opt.active_vss = active_vss

        # Tests that all VSs are recomputed.
        vss_to_migrate = opt.select_vss()
        self.assertEqual(set(), vss_to_migrate)


if __name__ == '__main__':
    unittest.main()
