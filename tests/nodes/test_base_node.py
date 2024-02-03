import unittest
from unittest.mock import patch

from neurons.nodes.factory import NodeFactory
from insights.protocol import NETWORK_BITCOIN, NETWORK_ETHEREUM, NETWORK_BITCOIN_CASH
from neurons.nodes.implementations import ethereum, bitcoin
class TestNode(unittest.TestCase):

    def setUp(self):
        pass

    def test_create_from_network_bitcoin(self):
        node = NodeFactory.create_node(NETWORK_BITCOIN)
        self.assertIsInstance(node, bitcoin.BitcoinNode)

    def test_create_from_network_ethereum(self):
        node = NodeFactory.create_node(NETWORK_ETHEREUM)
        self.assertIsInstance(node, ethereum.EthereumNode)

    def test_create_from_network_invalid(self):
        with self.assertRaises(ValueError):
            NodeFactory.create_node(NETWORK_BITCOIN_CASH)


    def test_validate_all_data_samples_invalid(self):
        for network in [NETWORK_BITCOIN, NETWORK_ETHEREUM]:
            with self.subTest(network=network):
                node = NodeFactory.create_node(network)
                data_samples = [1] * 8
                result = node.validate_all_data_samples(data_samples)
                self.assertFalse(result)

    @patch('neurons.nodes.implementations.bitcoin.BitcoinNode.validate_data_sample')
    def test_validate_data_sample_valid_samples(self, mock_validate_data_sample):
        mock_validate_data_sample.return_value = True  # Assuming this structure matches your actual data

        node = NodeFactory.create_node(NETWORK_BITCOIN)
        data_sample = [{'block_height': i, 'transaction_count': 3} for i in range(11)]
        result = node.validate_all_data_samples(data_sample)
        self.assertTrue(result)

    @patch('neurons.nodes.implementations.bitcoin.BitcoinNode.validate_data_sample')
    def test_validate_data_sample_invalid_samples(self, mock_validate_data_sample):
        mock_validate_data_sample.return_value = False  # Assuming this structure matches your actual data

        node = NodeFactory.create_node(NETWORK_BITCOIN)
        data_sample = [{'block_height': i, 'transaction_count': 3} for i in range(11)]
        result = node.validate_all_data_samples(data_sample)
        self.assertFalse(result)


    @patch('neurons.nodes.implementations.bitcoin.BitcoinNode.get_block_by_height')
    def test_validate_data_sample(self, mock_get_block_by_height):
        mock_get_block_by_height.return_value = {'tx': [1, 2, 3]}  # Assuming this structure matches your actual data

        node = NodeFactory.create_node(NETWORK_BITCOIN)
        data_sample = {'block_height': 1, 'transaction_count': 3}

        result = node.validate_data_sample(data_sample)

        self.assertTrue(result)
        mock_get_block_by_height.assert_called_with(data_sample['block_height'])


if __name__ == '__main__':
    unittest.main()
