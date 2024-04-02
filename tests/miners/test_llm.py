import unittest
import os

from insights import protocol
from insights.llm import OpenAILLM
from neurons.miners.bitcoin.funds_flow.query_builder import QueryBuilder
from neurons.miners.bitcoin.funds_flow.graph_search import GraphSearch

class TestLLM(unittest.TestCase):
    def setUp(self) -> None:
        self.llm = OpenAILLM()
        self.graph_search = GraphSearch()
    
    def tearDown(self) -> None:
        self.graph_search.close()
    
    def test_build_query(self):
        # test case 1
        query_text = "Return 15 transactions outgoing from my address bc1q4s8yps9my6hun2tpd5ke5xmvgdnxcm2qspnp9r"
        query = self.llm.build_query_from_messages([
            protocol.LlmMessage(
                type=protocol.LLM_MESSAGE_TYPE_USER,
                content=query_text
            )
        ])
        expected_query = {
            "type": "search",
            "target": "Transaction",
            "where": {
                "from_address": "bc1q4s8yps9my6hun2tpd5ke5xmvgdnxcm2qspnp9r"
            },
            "limit": 15,
            "skip": 0
        }
        self.assertEqual(query.type, expected_query["type"])
        self.assertEqual(query.target, expected_query["target"])
        self.assertDictEqual(query.where, expected_query["where"])
        self.assertEqual(query.limit, expected_query["limit"])
        self.assertEqual(query.skip, expected_query["skip"])

        # test case 2
        query_text = "I have sent more than 1.5 BTC to somewhere but I couldn't remember. Show me relevant transactions. My address is bc1q4s8yps9my6hun2tpd5ke5xmvgdnxcm2qspnp9r"
        query = self.llm.build_query_from_messages([
            protocol.LlmMessage(
                type=protocol.LLM_MESSAGE_TYPE_USER,
                content=query_text
            )
        ])
        expected_query = {
            "type": "search",
            "target": "Transaction",
            "where": {
                "from_address": "bc1q4s8yps9my6hun2tpd5ke5xmvgdnxcm2qspnp9r",
                "amount_range": {
                    "from": 1.5
                }
            },
            "limit": None,
            "skip": 0
        }
        self.assertEqual(query.type, expected_query["type"])
        self.assertEqual(query.target, expected_query["target"])
        self.assertDictEqual(query.where, expected_query["where"])
        self.assertEqual(query.limit, expected_query["limit"])
        self.assertEqual(query.skip, expected_query["skip"])
        
    def test_llm_query_handler(self):
        query_text = "Return 15 transactions outgoing from my address bc1q4s8yps9my6hun2tpd5ke5xmvgdnxcm2qspnp9r"
        llm_messages = [
            protocol.LlmMessage(
                type=protocol.LLM_MESSAGE_TYPE_USER,
                content=query_text
            )
        ]
        query = self.llm.build_query_from_messages(llm_messages)
        result = self.graph_search.execute_query(query=query)
        interpreted_result = self.llm.interpret_result(llm_messages=llm_messages, result=result)
        print("--- Interpreted result ---")
        print(interpreted_result)

    def test_edge_cases(self):
        with self.assertRaises(Exception) as context:
            query_text = "What is React.js?"
            llm_messages = [
                protocol.LlmMessage(
                    type=protocol.LLM_MESSAGE_TYPE_USER,
                    content=query_text
                )
            ]
            query = self.llm.build_query_from_messages(llm_messages)
            result = self.graph_search.execute_query(query=query)
            interpreted_result = self.llm.interpret_result(llm_messages=llm_messages, result=result)
        self.assertEqual(str(context.exception), str(protocol.LLM_ERROR_TYPE_NOT_SUPPORTED))
        
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    unittest.main()
