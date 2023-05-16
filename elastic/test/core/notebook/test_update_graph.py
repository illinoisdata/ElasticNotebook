import unittest
from elastic.core.graph.graph import DependencyGraph
from elastic.core.notebook.update_graph import update_graph


class TestUpdateGraph(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = DependencyGraph()

    def test_update_graph(self):
        """
            Test graph correctly handles updating from cell code.
        """
        graph = DependencyGraph()
        graph.create_variable_snapshot("x", False)

        update_graph("y = 1\nz = 1", 1, 1, {"x"}, {"y", "z"}, set(), graph)

        # Check elements have been added to the graph.
        self.assertEqual(1, len(graph.variable_snapshots["y"]))
        self.assertEqual(1, len(graph.variable_snapshots["z"]))
        self.assertEqual(1, len(graph.cell_executions))

        # Check fields are filled in correctly.
        self.assertEqual(0, graph.cell_executions[0].cell_num)
        self.assertEqual("y = 1\nz = 1", graph.cell_executions[0].cell)
        self.assertEqual(1, graph.cell_executions[0].cell_runtime)
        self.assertEqual(1, graph.cell_executions[0].start_time)


if __name__ == '__main__':
    unittest.main()
