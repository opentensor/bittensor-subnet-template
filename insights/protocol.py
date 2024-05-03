from typing import Optional, List, Dict
import bittensor as bt
from pydantic import BaseModel

# protocol version
VERSION = 5
ERROR_TYPE = int

# Model types
MODEL_TYPE_FUNDS_FLOW = "funds_flow"
MODEL_TYPE_BALANCE_TRACKING = "balance_tracking"

# Networks
NETWORK_BITCOIN = "bitcoin"
NETWORK_BITCOIN_ID = 1
NETWORK_DOGE = "doge"
NETWORK_DOGE_ID = 2
NETWORK_ETHEREUM = "ethereum"
NETWORK_ETHEREUM_ID = 3

# Query Types
QUERY_TYPE_SEARCH = "search"
QUERY_TYPE_FLOW = "flow"
QUERY_TYPE_AGGREGATION = "aggregation"

# Default settings for miners
MAX_MINER_INSTANCE = 9

# LLM Type
LLM_TYPE_OPENAI = "openai"
LLM_TYPE_CUSTOM = "custom"

# LLM MESSAGE TYEP
LLM_MESSAGE_TYPE_USER = 1
LLM_MESSAGE_TYPE_AGENT = 2

# LLM Error Codes
LLM_ERROR_NO_ERROR = 0
LLM_ERROR_TYPE_NOT_SUPPORTED = 1
LLM_ERROR_SEARCH_TARGET_NOT_SUPPORTED = 2
LLM_ERROR_SEARCH_LIMIT_NOT_SPECIFIED = 3
LLM_ERROR_SEARCH_LIMIT_EXCEEDED = 4
LLM_ERROR_INTERPRETION_FAILED = 5
LLM_ERROR_EXECUTION_FAILED = 6
LLM_ERROR_QUERY_BUILD_FAILED = 7
LLM_ERROR_GENERAL_RESPONSE_FAILED = 8
LLM_ERROR_NOT_APPLICAPLE_QUESTIONS = 9

# LLM Error Messages
LLM_ERROR_MESSAGES = {
    LLM_ERROR_NO_ERROR: "No Error",
    LLM_ERROR_TYPE_NOT_SUPPORTED: "Not supported query type",
    LLM_ERROR_SEARCH_TARGET_NOT_SUPPORTED: "Please let us know what you want to search.",
    LLM_ERROR_SEARCH_LIMIT_NOT_SPECIFIED: "Because there are too many results, you need to let us know how many results you want to get.",
    LLM_ERROR_SEARCH_LIMIT_EXCEEDED: "We cannot provide that many results.",
    LLM_ERROR_INTERPRETION_FAILED: "Unexpected error occurs while interpreting results.",
    LLM_ERROR_EXECUTION_FAILED: "Unexpected error occurs during database interaction.",
    LLM_ERROR_QUERY_BUILD_FAILED: "Unexpected error occurs while inferencing AI models.",
    LLM_ERROR_GENERAL_RESPONSE_FAILED: "Unexpected error occurs while answering general questions.",
    LLM_ERROR_NOT_APPLICAPLE_QUESTIONS: "Your question is not applicable to our subnet. We only answer questions related blockchain or cryptocurrency."
}

def get_network_by_id(id):
    return {
        NETWORK_BITCOIN_ID: NETWORK_BITCOIN,
        NETWORK_DOGE_ID: NETWORK_DOGE,
        NETWORK_ETHEREUM_ID: NETWORK_ETHEREUM
    }.get(id)

def get_network_id(network):
    return {
        NETWORK_BITCOIN : NETWORK_BITCOIN_ID,
        NETWORK_DOGE : NETWORK_DOGE_ID,
        NETWORK_ETHEREUM: NETWORK_ETHEREUM_ID
    }.get(network)

def get_model_types():
    return [MODEL_TYPE_FUNDS_FLOW, MODEL_TYPE_BALANCE_TRACKING]

def get_networks():
    return [NETWORK_BITCOIN]

class DiscoveryMetadata(BaseModel):
    network: str = None
    #TODO: implement method for getting graph schema from miner

class DiscoveryOutput(BaseModel):
    metadata: DiscoveryMetadata = None
    block_height: int = None
    start_block_height: int = None
    balance_model_last_block: int = None
    run_id: str = None
    version: Optional[int] = VERSION

class BaseSynapse(bt.Synapse):
    version: int = VERSION

class Discovery(BaseSynapse):
    output: DiscoveryOutput = None
                        
    def deserialize(self):
        return self

class QueryOutput(BaseModel):
    result: Optional[List[Dict]] = None
    interpreted_result: Optional[str] = None
    error: Optional[ERROR_TYPE] = None

class GenericQueryOutput(BaseModel):
    result: Optional[List[Dict]] = None    
    error: Optional[ERROR_TYPE] = None

class Query(BaseSynapse):
    network: str = None
    type: str = None

    # search query
    target: str = None
    where: Optional[Dict] = None
    limit: Optional[int] = None
    skip: Optional[int] = 0

    # output
    output: Optional[QueryOutput] = None

    def deserialize(self) -> Dict:
        return self.output

class Benchmark(BaseSynapse):
    network: str = None
    query: str = None

    # output
    output: Optional[float] = None

    def deserialize(self) -> Dict:
        return self.output

class Challenge(BaseSynapse):
    model_type: str # model type

    # For BTC funds flow model
    in_total_amount: Optional[int] = None
    out_total_amount: Optional[int] = None
    tx_id_last_4_chars: Optional[str] = None
    
    # For BTC balance tracking model
    block_height: Optional[int] = None
    
    # Altcoins
    checksum: Optional[str] = None

    output: Optional[str] = None
    
    def deserialize(self) -> str:
        return self.output

class LlmMessage(BaseModel):
    type: int = None
    content: str = None

class LlmQuery(BaseSynapse):
    network: str = None    
    # decide whether to invoke a generic llm endpoint or not
    # is_generic_llm: bool = False  
    # messages: conversation history for llm agent to use as context
    messages: List[LlmMessage] = None

    # output
    output: Optional[QueryOutput] = None
    def deserialize(self) -> str:
        return self.output

class GenericLlmQuery(BaseSynapse):
    is_generic_llm: bool = True
    messages: List[LlmMessage] = None

    # output
    output: Optional[GenericQueryOutput] = None
    def deserialize(self) -> str:
        return self.output
