import unittest

import os, sys
sys.path.insert(0, os.path.abspath(".."))
from algorithm.selector import Selector
from algorithm.optimizer_greedy import OptimizerGreedy
from core.graph.graph import DependencyGraph
from core.graph.node import Node
from core.graph.edge import Edge
from core.graph.node_set import NodeSet

class TestOptimizer(unittest.TestCase):
    def test_init(self):
        ## Nodes
        nodes = []
        for i in range(18):
            nodes.append(Node(None, 1, None))

        ## Node sets
        node_sets = []
        for i in range(0, 18, 2):
            node_sets.append(NodeSet([nodes[i], nodes[i + 1]], None))
        node_sets.append(NodeSet([nodes[3], nodes[6]], None))
        node_sets.append(NodeSet([nodes[7], nodes[10]], None))
        node_sets.append(NodeSet([nodes[14], nodes[15]], None))

        ## Graph
        graph = DependencyGraph()
        graph.edges.append(Edge(None, 2, node_sets[0], node_sets[1]))
        graph.edges.append(Edge(None, 2, node_sets[2], node_sets[3]))
        graph.edges.append(Edge(None, 2, node_sets[4], node_sets[5]))
        graph.edges.append(Edge(None, 2, node_sets[9], node_sets[6]))
        graph.edges.append(Edge(None, 2, node_sets[10], node_sets[7]))
        graph.edges.append(Edge(None, 2, node_sets[11], node_sets[8]))

        opt = OptimizerGreedy(graph, nodes)
        result = opt.select_nodes()

        self.assertEqual(set(result), {node_sets[1], node_sets[3], node_sets[5],
             node_sets[6], node_sets[7], node_sets[8],
             node_sets[9], node_sets[10], node_sets[11]})
        
if __name__ == '__main__':
    unittest.main()
