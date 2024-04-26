import unittest
 
from neurons.validators.utils.utils import count_hotkeys_per_ip, generate_challenge_to_check
 
from neurons.nodes.bitcoin.node_utils import process_in_memory_txn_for_indexing
from neurons.nodes.factory import NodeFactory
from insights.protocol import NETWORK_BITCOIN

class TestUtils(unittest.TestCase):
 
    # def test_get_miner_distributions(self):
    #     # Mock data
    #     miners_metadata = {
    #         'hotkey1': Mock(n=1),
    #         'hotkey2': Mock(n=2),
    #         'hotkey3': Mock(n=1),
    #     }
    #     network_importance_keys = [1, 2]

    #     # Mock get_network_by_id function
    #     def mock_get_network_by_id(network_id):
    #         return network_id

    #     with unittest.mock.patch('insights.protocol.get_network_by_id', mock_get_network_by_id):
    #         result = get_miner_distributions(miners_metadata, network_importance_keys)

    #     # Check the result
    #     expected_result = {1: 2, 2: 1}
    #     self.assertEqual(result, expected_result)

    def test_count_hotkeys_per_ip(self):
        # Mock data
        class MockAxon:
            def __init__(self, ip):
                self.ip = ip

        axons = [
            MockAxon(ip='192.168.1.1'),
            MockAxon(ip='192.168.1.2'),
            MockAxon(ip='192.168.1.1'),
            MockAxon(ip='192.168.1.3'),
        ]

        result = count_hotkeys_per_ip(axons)

        # Check the result
        expected_result = {'192.168.1.1': 2, '192.168.1.2': 1, '192.168.1.3': 1}
        self.assertEqual(result, expected_result)
 
 
    def test_generate_challenge_to_check(self):
        node = NodeFactory.create_node(NETWORK_BITCOIN)
        challenge, txn_id_to_check = node.create_challenge(500000, 600000)

        txn_data = node.get_txn_data_by_id(txn_id_to_check)
        tx = node.create_in_memory_txn(txn_data)
        in_amount_by_address, out_amount_by_address, input_addresses, output_addresses, in_total_amount, out_total_amount = process_in_memory_txn_for_indexing(tx, node)
        self.assertEqual(challenge.in_total_amount, in_total_amount)
        self.assertEqual(challenge.out_total_amount, out_total_amount)
        self.assertEqual(challenge.tx_id_last_4_chars, txn_id_to_check[-4:])

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    unittest.main()
