import os

from insights.llm.base_llm import BaseLLM
from insights.protocol import Query, QueryOutput

from langchain_openai import ChatOpenAI

from neurons.setup_logger import setup_logger

logger = setup_logger("OpenAI LLM")

class OpenAILLM(BaseLLM):
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY") or ""
        if not api_key:
            raise Exception("OpenAI_API_KEY is not set.")

        self.chat = ChatOpenAI(api_key=api_key, temperature=0)
        
    def build_query_from_text(self, query_text: str) -> Query:
        pass
        
    def generate_text_response_from_query_output(self, query_output: QueryOutput) -> str:
        pass
        
    def generate_llm_query_from_query(self, query: Query) -> str:
        pass
    