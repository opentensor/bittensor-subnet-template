import unittest
from unittest.mock import patch, MagicMock
import sys
import os

from neurons.miners.miner import Miner
from neurons.miners.miner import wait_for_blocks_sync
from neurons.miners.bitcoin.funds_flow.graph_search import GraphSearch

class TestGraphSearch(unittest.TestCase):
    def test_solve_challenge(self):
        graph_search = GraphSearch(
            graph_db_url=os.environ.get('GRAPH_DB_URL'),
            graph_db_user=os.environ.get('GRAPH_DB_USER'),
            graph_db_password=os.environ.get('GRAPH_DB_PASSWORD'),
        )
        output = graph_search.solve_challenge(in_total_amount=203216, out_total_amount=200000, tx_id_last_4_chars="d946")
        self.assertEqual(output, "93fa1edce68762615740fd35581fc337d508ca33e682057bed7b395b5d66d946")

        
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    unittest.main()