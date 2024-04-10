import unittest

from neurons.nodes.bitcoin.node_utils import process_in_memory_txn_for_indexing
from neurons.nodes.factory import NodeFactory
from insights.protocol import NETWORK_BITCOIN

class TestUtils(unittest.TestCase):
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
