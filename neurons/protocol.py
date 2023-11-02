from typing import Optional, List, Dict

import bittensor as bt


class GetBlockchainData(bt.Synapse):
    benchmark: bool = False
    network: str = None
    cypher_query: str = None
    output: Optional[List[Dict]] = None

    def deserialize(self) -> List[Dict]:
        return self.output
