from typing import List, Optional, Dict

import requests
from pydantic import BaseModel

from neurons import logger


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

    def query(self, messages: List[LlmMessage], llm_type: str = "openai", network: str = "bitcoin") -> QueryOutput | None:
        try:
            url = f"{self.base_url}/v1/process_prompt"
            payload = {
                "llm_type": llm_type,
                "network": network,
                "messages": [message.dict() for message in messages]
            }
            #TODO: add basic auth based on auth key
            
            logger.debug(f"Request URL: {url}")
            logger.debug(f"Request Payload: {payload}")
            response = requests.post(url, json=payload, timeout=180)
            response.raise_for_status()
            return response.json()
        except requests.ConnectionError as e:
            logger.error(f"Connection error: {e}")
        except requests.Timeout as e:
            logger.error(f"Request timeout: {e}")
        except requests.RequestException as e:
            logger.error(f"Failed to query LLM: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        return None
