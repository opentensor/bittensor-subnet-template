from typing import Optional, List, Dict
import bittensor as bt
from pydantic import BaseModel

# protocol version
VERSION = 5


# Model types
MODEL_TYPE_FUNDS_FLOW = "funds_flow"
MODEL_TYPE_FUNDS_FLOW_ID = 2

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

# LLM Error Codes
LLM_ERROR_NO_ERROR = 0
LLM_ERROR_TYPE_NOT_SUPPORTED = 1
LLM_ERROR_SEARCH_TARGET_NOT_SUPPORTED = 2
LLM_ERROR_SEARCH_LIMIT_NOT_SPECIFIED = 3
LLM_ERROR_SEARCH_LIMIT_EXCEEDED = 4
LLM_ERROR_INTERPRETION_FAILED = 5

# LLM Error Messages
LLM_ERROR_MESSAGES = {
    LLM_ERROR_NO_ERROR: "No Error",
    LLM_ERROR_TYPE_NOT_SUPPORTED: "Not supported query type",
    LLM_ERROR_SEARCH_TARGET_NOT_SUPPORTED: "Not supported search target",
    LLM_ERROR_SEARCH_LIMIT_NOT_SPECIFIED: "Search limit not specified",
    LLM_ERROR_SEARCH_LIMIT_EXCEEDED: "Search limit exceeded",
    LLM_ERROR_INTERPRETION_FAILED: "Failed to interpret result",
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


def get_model_id(model_type):
    return {
        MODEL_TYPE_FUNDS_FLOW: MODEL_TYPE_FUNDS_FLOW_ID
    }.get(model_type)

def get_model_types():
    return [MODEL_TYPE_FUNDS_FLOW]

def get_networks():
    return [NETWORK_BITCOIN]

class DiscoveryMetadata(BaseModel):
    network: str = None
    model_type: str = None
    graph_schema: Optional[Dict] = None
    #TODO: implement method for getting graph schema from miner


class DiscoveryOutput(BaseModel):
    metadata: DiscoveryMetadata = None
    block_height: int = None
    start_block_height: int = None
    run_id: str = None
    version: Optional[int] = VERSION

class BlockCheckOutput(BaseModel):
    data_samples: List[Dict] = None

class BaseSynapse(bt.Synapse):
    version: int = VERSION

class Discovery(BaseSynapse):
    output: DiscoveryOutput = None

    def deserialize(self):
        return self

class BlockCheck(BaseSynapse):
    blocks_to_check: List[int] = None
    output: BlockCheckOutput = None

class QueryOutput(BaseModel):
    result: Optional[List[Dict]] = None
    interpreted_result: Optional[str] = None
    error: Optional[str] = None

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

class Challenge(BaseSynapse):

    # For BTC
    in_total_amount: Optional[int] = None
    out_total_amount: Optional[int] = None
    tx_id_last_4_chars: Optional[str] = None
    
    # Altcoins
    checksum: Optional[str] = None

    output: Optional[str] = None
    
    def deserialize(self) -> str:
        return self.output

class LlmQuery(BaseSynapse):
    network: str = None    
    # input_text: Plain text written in natural language
    input_text: str = None    
    # output
    output: Optional[QueryOutput] = None
    def deserialize(self) -> str:
        return self.output
