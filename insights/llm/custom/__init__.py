from insights.llm.base_llm import BaseLLM
from insights.protocol import Query, QueryOutput


class CustomLLM(BaseLLM):
    def __init__(self, model_name: str) -> None:
        pass
        
    def build_query_from_text(self, query_text: str) -> Query:
        pass
        
    def interpret_result(self, query_text: str, result: dict) -> str:
        pass
        
    def generate_llm_query_from_query(self, query: Query) -> str:
        pass
