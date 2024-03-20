from insights.protocol import Query, QueryOutput

from abc import ABC, abstractmethod


class BaseLLM(ABC):
    @abstractmethod
    def __init__(self) -> None:
        """
        Initialize LLM
        """
    
    @abstractmethod
    def build_query_from_text(self, query_text: str) -> Query:
        """
        Build query synapse from natural language query
        Used by miner
        """

    @abstractmethod
    def generate_text_response_from_query_output(self, query_output: QueryOutput) -> str:
        """
        Generate natural language response from query_output
        Used by miner
        """
    
    @abstractmethod
    def generate_llm_query_from_query(self, query: Query) -> str:
        """
        Generate natural language query from Query object
        Used by validator
        """
