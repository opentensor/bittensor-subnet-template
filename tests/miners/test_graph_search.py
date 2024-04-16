import unittest
from unittest.mock import patch, MagicMock
import sys
import os

from neurons.nodes.factory import NodeFactory
from insights.protocol import NETWORK_BITCOIN, Challenge, MODEL_TYPE_FUNDS_FLOW, MODEL_TYPE_BALANCE_TRACKING
from neurons.miners.miner import Miner
from neurons.miners.miner import wait_for_blocks_sync
from neurons.miners.bitcoin.funds_flow.graph_search import GraphSearch

class TestGraphSearch(unittest.TestCase):
    def test_solve_challenge(self):
        node = NodeFactory.create_node(NETWORK_BITCOIN)
        graph_search = GraphSearch(
            graph_db_url=os.environ.get('GRAPH_DB_URL'),
            graph_db_user=os.environ.get('GRAPH_DB_USER'),
            graph_db_password=os.environ.get('GRAPH_DB_PASSWORD'),
        )

        challenge = Challenge(model_type=MODEL_TYPE_FUNDS_FLOW, in_total_amount=203216, out_total_amount=200000, tx_id_last_4_chars="d946")
        expected_output = "93fa1edce68762615740fd35581fc337d508ca33e682057bed7b395b5d66d946"
        test_output1 = "93fa1edce68762615740fd35581fc337d508ca33e682057bed7b395b5d66d945"
        test_output2 = "83fa1edce68762615740fd35581fc337d508ca33e682057bed7b395b5d66d946"

        output = graph_search.solve_challenge(in_total_amount=challenge.in_total_amount, out_total_amount=challenge.out_total_amount, tx_id_last_4_chars=challenge.tx_id_last_4_chars)
        self.assertEqual(output, expected_output)
        
        is_valid = node.validate_challenge_response_output(challenge, expected_output)
        self.assertEqual(is_valid, True)

        is_valid = node.validate_challenge_response_output(challenge, test_output1)
        self.assertEqual(is_valid, False)

        is_valid = node.validate_challenge_response_output(challenge, test_output2)
        self.assertEqual(is_valid, False)

        graph_search.close()
        
    def test_get_min_max_block_height_cache(self):
        graph_search = GraphSearch(
            graph_db_url=os.environ.get('GRAPH_DB_URL'),
            graph_db_user=os.environ.get('GRAPH_DB_USER'),
            graph_db_password=os.environ.get('GRAPH_DB_PASSWORD'),
        )
        print(graph_search.get_min_max_block_height_cache())
        graph_search.close()

    def test_get_min_max_block_height(self):
        print("Running query for getting min max block height...")
        graph_search = GraphSearch(
            graph_db_url=os.environ.get('GRAPH_DB_URL'),
            graph_db_user=os.environ.get('GRAPH_DB_USER'),
            graph_db_password=os.environ.get('GRAPH_DB_PASSWORD'),
        )
        min_block_height, max_block_height = graph_search.get_min_max_block_height()
        print((min_block_height, max_block_height))
        self.assertNotEqual(min_block_height, 0)
        self.assertNotEqual(max_block_height, 0)
        graph_search.close()

        
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    unittest.main()