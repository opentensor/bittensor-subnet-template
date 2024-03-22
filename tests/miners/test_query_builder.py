import unittest
import os

from insights import protocol
from neurons.miners.bitcoin.funds_flow.query_builder import QueryBuilder

class TestGraphSearch(unittest.TestCase):
    def test_build_search_query(self):
        # test case 1
        query = protocol.Query(type=protocol.QUERY_TYPE_SEARCH, target='Transaction', limit=20)
        cypher_query = QueryBuilder.build_query(query)
        self.assertEqual(cypher_query, "MATCH (t:Transaction)\nRETURN t\nLIMIT 20;")
        
        # test case 2
        query = protocol.Query(type=protocol.QUERY_TYPE_SEARCH, target='Transaction', limit=20, where={
            "tx_id": "0123456789"
        })
        cypher_query = QueryBuilder.build_query(query)
        self.assertEqual(cypher_query, 'MATCH (t:Transaction{tx_id: "0123456789"})\nRETURN t\nLIMIT 20;')
        
        # test case 3
        query = protocol.Query(type=protocol.QUERY_TYPE_SEARCH, target='Transaction', limit=20, where={
            "from_address": "123",
            "to_address": "456",
        })
        cypher_query = QueryBuilder.build_query(query)
        self.assertEqual(cypher_query, 'MATCH (a1:Address{address: "123"})-[s1:SENT]->(t:Transaction)-[s2:SENT]->(a2:Address{address: "456"})\nRETURN t\nLIMIT 20;')
        
        # test case 4
        query = protocol.Query(type=protocol.QUERY_TYPE_SEARCH, target='Transaction', limit=20, where={
           "amount_range": {
               "from": 2000,
               "to": 3000,
           },
           "timestamp_range": {
               "from": 4000,
           },
        })
        cypher_query = QueryBuilder.build_query(query)
        self.assertEqual(cypher_query, 'MATCH (t:Transaction)\nWHERE t.out_total_amount >= 2000 AND t.out_total_amount <= 3000 AND t.timestamp >= 4000\nRETURN t\nLIMIT 20;')
        
if __name__ == '__main__':
    unittest.main()
