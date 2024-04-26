from insights.llm.base_llm import BaseLLM
from insights import protocol
from insights.protocol import Query, QueryOutput

from typing import List


class CustomLLM(BaseLLM):
    def __init__(self, model_name: str) -> None:
        pass
        
    def build_query_from_messages(self, llm_messages: List[protocol.LlmMessage]) -> Query:
        pass
        
    def interpret_result(self, llm_messages: List[protocol.LlmMessage], result: dict) -> str:
        pass
        
    def generate_llm_query_from_query(self, query: Query) -> str:
        pass
