from typing import Optional, List, Dict
import bittensor as bt
from pydantic import BaseModel

# Model types
MODEL_TYPE_FUNDS_FLOW = "funds_flow"
MODEL_TYPE_FUNDS_FLOW_V1 = "funds_flow-v1.0"

# Networks
NETWORK_BITCOIN = "bitcoin"
NETWORK_LITECOIN = "litecoin"
NETWORK_DOGE = "doge"
NETWORK_DASH = "dash"
NETWORK_ZCASH = "zcash"
NETWORK_BITCOIN_CASH = "bitcoin_cash"


class MinerDiscoveryMetadata(BaseModel):
    network: str = None
    model_type: str = None
    graph_schema: Optional[Dict] = None
    #TODO: implement method for getting graph schema from miner


class MinerDiscoveryOutput(BaseModel):
    metadata: MinerDiscoveryMetadata = None
    data_samples: List[Dict] = None
    block_height: int = None
    start_block_height: int = None
    run_id: str = None
    version: Optional[int] = None

class MinerDiscovery(bt.Synapse):
    output: MinerDiscoveryOutput = None

    def deserialize(self):
        return self

class MinerRandomBlockCheckOutput(BaseModel):
    data_samples: List[Dict] = None

class MinerRandomBlockCheck(bt.Synapse):
    blocks_to_check: List[int] = None
    output: MinerRandomBlockCheckOutput = None

class MinerQuery(bt.Synapse):
    network: str = None
    model_type: str = None
    query: str = None
    output: Optional[List[Dict]] = None

    def deserialize(self) -> List[Dict]:
        return self.output