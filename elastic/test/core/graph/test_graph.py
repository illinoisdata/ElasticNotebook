import unittest
from elastic.core.graph.graph import DependencyGraph


class TestGraph(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = DependencyGraph()

    def test_create_variable_snapshot(self):
        """
            Test graph correctly handles versioning of VSs with the same and different names.
        """
        vs1 = self.graph.create_variable_snapshot("x", False)
        vs2 = self.graph.create_variable_snapshot("x", False)
        vs3 = self.graph.create_variable_snapshot("y", False)

        # VSs are versioned correcly
        self.assertEqual(0, vs1.version)
        self.assertEqual(1, vs2.version)  # vs2 is second VS for variable x
        self.assertEqual(0, vs3.version)

        # VSs are stored in the graph correctly
        self.assertEqual({"x", "y"}, set(self.graph.variable_snapshots.keys()))
        self.assertEqual(2, len(self.graph.variable_snapshots["x"]))
        self.assertEqual(1, len(self.graph.variable_snapshots["y"]))

    def test_add_operation_event(self):
        vs1 = self.graph.create_variable_snapshot("x", False)
        vs2 = self.graph.create_variable_snapshot("y", False)

        self.graph.add_cell_execution("", 1, 1, {vs1}, {vs2})

        # CE is stored in the graph correctly
        self.assertEqual(1, len(self.graph.cell_executions))

        # Newly create CE correctly set as adjacent CE of variable snapshots
        self.assertTrue(vs1.input_ces[0] == self.graph.cell_executions[0])
        self.assertTrue(vs2.output_ce == self.graph.cell_executions[0])


if __name__ == '__main__':
    unittest.main()
