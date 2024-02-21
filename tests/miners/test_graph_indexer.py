import unittest
import os

from neurons.miners.bitcoin.funds_flow.graph_indexer import GraphIndexer

class TestGraphIndexer(unittest.TestCase):
    def test_solve_challenge(self):
        graph_indexer = GraphIndexer(
            graph_db_url=os.environ.get('GRAPH_DB_URL'),
            graph_db_user=os.environ.get('GRAPH_DB_USER'),
            graph_db_password=os.environ.get('GRAPH_DB_PASSWORD'),
        )
        output = graph_indexer.check_if_block_is_indexed(-1)
        self.assertEqual(output, False)

        
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    unittest.main()