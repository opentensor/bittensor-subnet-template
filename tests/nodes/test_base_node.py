import unittest
from neurons.nodes.bitcoin.node import BitcoinNode
from neurons.nodes.evm.ethereum.node import EthereumNode
from neurons.nodes.factory import NodeFactory
from insights.protocol import NETWORK_BITCOIN, NETWORK_ETHEREUM

class TestNode(unittest.TestCase):

    def setUp(self):
        pass

    def test_create_from_network_bitcoin(self):
        node = NodeFactory.create_node(NETWORK_BITCOIN)
        self.assertIsInstance(node, BitcoinNode)

    def test_create_from_network_ethereum(self):
        node = NodeFactory.create_node(NETWORK_ETHEREUM)
        self.assertIsInstance(node, EthereumNode)

    def test_create_from_network_invalid(self):
        with self.assertRaises(ValueError):
            NodeFactory.create_node("INVALID_NETWORK")


if __name__ == '__main__':
    unittest.main()
