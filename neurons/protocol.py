from typing import Optional, List, Dict
import bittensor as bt

# Model types
MODEL_TYPE_FUNDS_FLOW = "funds_flow"
MODEL_TYPE_FUNDS_FLOW = "funds_flow-v1.0"

# Networks
NETWORK_BITCOIN = "bitcoin"


class DiscoveryMetadata:
    network: str = None
    assets: List[str] = None
    model_type: str = None


class DiscoveryOutput:
    metadata: DiscoveryMetadata = None
    data: Optional[List[Dict]] = None


class MinerDiscovery(bt.Synapse):
    output: DiscoveryOutput = None

    def deserialize(self) -> DiscoveryOutput:
        return self.output