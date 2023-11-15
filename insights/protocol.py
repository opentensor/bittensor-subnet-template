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
    data_sample: Optional[List[Dict]] = None
    block_height: Optional[int] = None


class MinerDiscovery(bt.Synapse):
    random_block_height: dict[str, dict] = None
    output: MinerDiscoveryOutput = None

    def deserialize(self) -> MinerDiscoveryOutput:
        return self.output


class MinerQuery(bt.Synapse):
    network: str = None
    model_type: str = None
    query: str = None
    output: Optional[List[Dict]] = None

    def deserialize(self) -> List[Dict]:
        return self.output