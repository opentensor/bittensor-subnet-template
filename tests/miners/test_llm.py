import unittest
import os

from insights import protocol
from insights.llm import OpenAILLM
from neurons.miners.bitcoin.funds_flow.query_builder import QueryBuilder

class TestLLM(unittest.TestCase):
    def setUp(self) -> None:
        self.llm = OpenAILLM()
    
    def test_build_query(self):
        # test case 1
        query_text = "Return 15 transactions outgoing from my address bc1q4s8yps9my6hun2tpd5ke5xmvgdnxcm2qspnp9r"
        query = self.llm.build_query_from_text(query_text=query_text)
        expected_query = {
            "type": "search",
            "target": "Transaction",
            "where": {
                "from_address": "bc1q4s8yps9my6hun2tpd5ke5xmvgdnxcm2qspnp9r"
            },
            "limit": 15,
            "skip": 0
        }
        self.assertDictEqual(query, expected_query)

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    unittest.main()
