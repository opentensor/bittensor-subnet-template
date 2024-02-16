import bittensor as bt
from typing import List, Optional, Union, Any, Dict
from template.protocol import Dummy
from bittensor.subnets import SubnetsAPI


class DummyAPI(SubnetsAPI):
    def __init__(self, wallet: "bt.wallet"):
        super().__init__(wallet)
        self.netuid = 33
        self.name = "dummy"

    def prepare_synapse(
        self, dummy_input: int
    ) -> Dummy:
        synapse.dummy_input = dummy_input
        return synapse

    def process_responses(self, responses: List[Union["bt.Synapse", Any]]) -> List[int]:
        outputs = []
        for response in responses:
            if response.dendrite.status_code != 200:
                continue
            return outputs.append(response.dummy_output)
        return outputs
