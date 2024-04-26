from insights import protocol
from insights.protocol import Query, QueryOutput

from abc import ABC, abstractmethod
from typing import List

class BaseLLM(ABC):
    @abstractmethod
    def __init__(self) -> None:
        """
        Initialize LLM
        """
    
    @abstractmethod
    def build_query_from_messages(self, llm_messages: List[protocol.LlmMessage]) -> Query:
        """
        Build query synapse from natural language query
        Used by miner
        """

    @abstractmethod
    def interpret_result(self, llm_messages: List[protocol.LlmMessage], result: list) -> str:
        """
        Interpret result into natural language based on user's query and structured result dict
        """

    @abstractmethod
    def generate_general_response(self, llm_messages: List[protocol.LlmMessage]) -> str:
        """
        Generate general response based on chat history
        """
    
    @abstractmethod
    def generate_llm_query_from_query(self, query: Query) -> str:
        """
        Generate natural language query from Query object
        Used by validator
        """
