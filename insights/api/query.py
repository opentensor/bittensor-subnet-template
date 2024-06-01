# The MIT License (MIT)
# Copyright © 2021 Yuma Rao
# Copyright © 2023 Opentensor Foundation
# Copyright © 2023 Opentensor Technologies Inc

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import bittensor as bt
from typing import List, Optional, Union, Any, Dict

from protocols.llm_engine import LLM_MESSAGE_TYPE_USER

from insights import protocol
from insights.protocol import LlmQuery, LlmMessage
from insights.api import SubnetsAPI


class TextQueryAPI(SubnetsAPI):
    def __init__(self, wallet: "bt.wallet"):
        super().__init__(wallet)
        self.netuid = 15
        self.name = "LlmQuery"

    def prepare_synapse(self, network:str, text: str) -> LlmQuery:
        synapse = LlmQuery(
            network=network,
            messages=[
                LlmMessage(
                    type=LLM_MESSAGE_TYPE_USER,
                    content=text
                ),
            ],
        )
        return synapse

    def process_responses(
        self, responses: List[Union["bt.Synapse", Any]]
    ) -> List[int]:        
        outputs = []
        blacklist_axon_list = []
        for id, response in enumerate(responses):
            print(response)
            if response.dendrite.status_code != 200:
                blacklist_axon_list.append(id)
                continue
            outputs.append(response.output)
        return outputs, blacklist_axon_list