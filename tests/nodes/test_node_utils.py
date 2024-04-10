import unittest
from unittest.mock import Mock

from neurons.nodes.factory import NodeFactory
from neurons.nodes.bitcoin.node_utils import process_in_memory_txn_for_indexing
from insights.protocol import NETWORK_BITCOIN, NETWORK_ETHEREUM

class TestNodeUtils(unittest.TestCase):
    def test_process_in_memory_txn_for_indexing(self):
        txn_id = "aabbcc442e2c92661fdaf463e3bc5e0ca37dc6b48c0a459c34ac944ac840433f"
        node = NodeFactory.create_node(NETWORK_BITCOIN)
        
        txn_data = node.get_txn_data_by_id(txn_id)
        tx = node.create_in_memory_txn(txn_data)
        result = process_in_memory_txn_for_indexing(tx, node)

        # Check the result
        expected_result = ({'bc1pzhsphssqzngp00ddm5n2jt8dmkcxygrd4zn9ffhqejpt6kf6cr2qwq3tcx': 38963}, {'bc1pgc5kvr6u646tjgsjx3j9l8x67kkjpzevr0sxv8d7plaptsrftlssl6vjfw': 29261, 'bc1pzhsphssqzngp00ddm5n2jt8dmkcxygrd4zn9ffhqejpt6kf6cr2qwq3tcx': 0}, ['bc1pzhsphssqzngp00ddm5n2jt8dmkcxygrd4zn9ffhqejpt6kf6cr2qwq3tcx'], ['bc1pgc5kvr6u646tjgsjx3j9l8x67kkjpzevr0sxv8d7plaptsrftlssl6vjfw'], 38963, 29261)
        self.assertEqual(result, expected_result)

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()

    unittest.main()
