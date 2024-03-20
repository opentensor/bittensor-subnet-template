import unittest
import os

from insights import protocol
from insights.llm import OpenAILLM
from neurons.miners.bitcoin.funds_flow.query_builder import QueryBuilder

class TestLLM(unittest.TestCase):
    def setUp(self) -> None:
        self.llm = OpenAILLM()
    
    def test_build_query(self):
        query_text = "Return 20 transactions."
        query = self.llm.build_query_from_text(query_text=query_text)
        print(f"query: {query}")


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    unittest.main()
