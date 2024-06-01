from typing import List, Optional, Dict
from pydantic import BaseModel
from neurons import logger
import requests

class LlmMessage(BaseModel):
    type: int
    content: str


class QueryOutput(BaseModel):
    result: Optional[List[Dict]] = None
    interpreted_result: Optional[str] = None
    error: Optional[int] = None


class GenericOutput(BaseModel):
    result: Optional[Dict] = None


class LLMClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def discovery_v1(self, network: str) -> GenericOutput | None:
        try:
            url = f"{self.base_url}/v1/discovery/{network}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.ConnectionError as e:
            logger.error(f"Connection error: {e}")
        except requests.Timeout as e:
            logger.error(f"Request timeout: {e}")
        except requests.RequestException as e:
            logger.error(f"Failed to query: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        return None

    def challenge_utxo_v1(self, network: str, in_total_amount: int, out_total_amount: int, tx_id_last_4_chars: str) -> GenericOutput | None:
        try:
            url = f"{self.base_url}/v1/challenge/{network}"
            params = {'in_total_amount': in_total_amount, 'out_total_amount': out_total_amount, 'tx_id_last_4_chars': tx_id_last_4_chars}
            response = requests.get(url, params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.ConnectionError as e:
            logger.error(f"Connection error: {e}")
        except requests.Timeout as e:
            logger.error(f"Request timeout: {e}")
        except requests.RequestException as e:
            logger.error(f"Failed to query: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        return None

    def challenge_evm_v1(self, network: str, checksum: str) -> GenericOutput | None:
        try:
            url = f"{self.base_url}/v1/challenge/{network}"
            params = {'checksum': checksum}
            response = requests.get(url, params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.ConnectionError as e:
            logger.error(f"Connection error: {e}")
        except requests.Timeout as e:
            logger.error(f"Request timeout: {e}")
        except requests.RequestException as e:
            logger.error(f"Failed to query: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        return None

    def benchmark_v1(self, network: str, query: str) -> GenericOutput | None:
        try:
            url = f"{self.base_url}/v1/benchmark/{network}"
            params = {'query': query}
            response = requests.get(url,params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.ConnectionError as e:
            logger.error(f"Connection error: {e}")
        except requests.Timeout as e:
            logger.error(f"Request timeout: {e}")
        except requests.RequestException as e:
            logger.error(f"Failed to query: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        return None

    def llm_query_v1(self, messages: List[LlmMessage], llm_type: str = "openai", network: str = "bitcoin") -> QueryOutput | None:
        try:
            url = f"{self.base_url}/v1/process_prompt"
            payload = {
                "llm_type": llm_type,
                "network": network,
                "messages": [message.dict() for message in messages]
            }
            logger.debug(f"Querying LLM with payload: {payload}")
            response = requests.post(url, json=payload, timeout=5*60)
            response.raise_for_status()
            return response.json()
        except requests.ConnectionError as e:
            logger.error(f"Connection error: {e}")
        except requests.Timeout as e:
            logger.error(f"Request timeout: {e}")
        except requests.RequestException as e:
            logger.error(f"Failed to query: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        return None
