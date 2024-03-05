from typing import Optional, List, Dict
import bittensor as bt
from pydantic import BaseModel

# protocol version
VERSION = 4


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
    version: Optional[int] = None

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
    result: Optional[Dict] = None
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
