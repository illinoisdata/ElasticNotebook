#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois
import os
import unittest
from ipykernel.zmqshell import ZMQInteractiveShell

from elastic.core.graph.graph import DependencyGraph
from elastic.core.notebook.restore_notebook import restore_notebook
from IPython.terminal.interactiveshell import TerminalInteractiveShell


class TestRestoreNotebook(unittest.TestCase):
    def setUp(self) -> None:
        self.shell = ZMQInteractiveShell()

        # Construct simple test case
        self.graph = DependencyGraph()
        self.vs1 = self.graph.create_variable_snapshot("x", False)
        self.vs2 = self.graph.create_variable_snapshot("y", False)
        self.graph.add_cell_execution("x = 1\ny = 2", 1, 1, set(), {self.vs1, self.vs2})

    def test_restore_notebook_redeclare(self):
        """
            Test redeclaring variables works as expected.
        """
        # Redeclare x and y into the kernel.
        ce = self.graph.cell_executions[0]
        restore_notebook(self.graph, self.shell, {ce: [(self.vs1, 1), (self.vs2, 2)]}, set())

        # Assert that x and y are correctly redeclared.
        self.assertEqual(1, self.shell.user_ns["x"])
        self.assertEqual(2, self.shell.user_ns["y"])

    def test_restore_notebook_recompute(self):
        """
            Test recomputing OEs works as expected.
        """
        shell = TerminalInteractiveShell.instance()

        # Recompute the OE to recompute x and y.
        ce = self.graph.cell_executions[0]
        restore_notebook(self.graph, shell, {ce: []}, {ce})

        # Assert that x and y are correctly redeclared.
        self.assertEqual(1, shell.user_ns["x"])
        self.assertEqual(2, shell.user_ns["y"])


if __name__ == '__main__':
    unittest.main()
