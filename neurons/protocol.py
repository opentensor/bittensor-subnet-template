from typing import Optional, List, Dict

import bittensor as bt


class GetBlockchainData(bt.Synapse):
    network: str = "BITCOIN"
    cypher_query: Optional[int] = None
    output: Optional[List[Dict]] = None

    def deserialize(self) -> List[Dict]:
        """
        Deserialize the scrap_output into a list of dictionaries.
        """
        # TODO: Add error handling for when scrap_output is None
        return self.output

