from typing import List, Optional, Dict

import requests
from pydantic import BaseModel


class LlmMessage(BaseModel):
    type: int
    content: str


class QueryOutput(BaseModel):
    result: Optional[List[Dict]] = None
    interpreted_result: Optional[str] = None
    error: Optional[int] = None


class LLMClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def query(self, messages: List[LlmMessage], llm_type: str = "openai", network: str = "bitcoin") -> QueryOutput:
        url = f"{self.base_url}/v1/process_prompt"
        payload = {
            "llm_type": llm_type,
            "network": network,
            "messages": [message.dict() for message in messages]
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
