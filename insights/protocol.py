from typing import Optional, List, Dict
import bittensor as bt
from pydantic import BaseModel

# protocol version
VERSION = 4


# Model types
MODEL_TYPE_FUNDS_FLOW = "funds_flow"
MODEL_TYPE_FUNDS_FLOW_ID = 1

# Networks
NETWORK_BITCOIN = "bitcoin"
NETWORK_BITCOIN_ID = 1
NETWORK_DOGE = "doge"
NETWORK_DOGE_ID = 2
NETWORK_ETHEREUM = "ethereum"
NETWORK_ETHEREUM_ID = 3

# Default settings for miners
MAX_MULTIPLE_RUN_ID = 9
MAX_MULTIPLE_IPS = 9

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

class Query(BaseSynapse):
    network: str = None
    model_type: str = None
    query: str = None
    output: Optional[List[Dict]] = None

    def deserialize(self) -> List[Dict]:
        return self.output