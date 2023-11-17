# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# TODO(developer): Set your name
# Copyright © 2023 <your name>

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

# Bittensor Miner Template:
# TODO(developer): Rewrite based on protocol and validator defintion.

# Step 1: Import necessary libraries and modules
import os
import time
import argparse
import typing
import traceback
import bittensor as bt

# import this repo
import template
from template.base import BaseMinerNeuron


class Neuron(BaseMinerNeuron):
    def __init__(self, config=None):

        # Takes care of routine tasks such as setting up wallet, subtensor, metagraph, logging directory, parsing config, etc.
        # init parent class
        super(Neuron, self).__init__(config=config)

        # Anything else specific to your use case you can do here

    async def forward(self, synapse: template.protocol.Dummy) -> template.protocol.Dummy:
        # You should replace the template forward with your own implementation
        synapse.dummy_output = synapse.dummy_input * 2
        return synapse

    # Step 5: Set up miner functionalities
    # The following functions control the miner's response to incoming requests.
    # The blacklist function decides if a request should be ignored.
    async def blacklist(self, synapse: template.protocol.Dummy) -> typing.Tuple[bool, str]:
        # TODO(developer): Define how miners should blacklist requests. This Function
        # Runs before the synapse data has been deserialized (i.e. before synapse.data is available).
        # The synapse is instead contructed via the headers of the request. It is important to blacklist
        # requests before they are deserialized to avoid wasting resources on requests that will be ignored.
        # Below: Check that the hotkey is a registered entity in the metagraph.
        if synapse.dendrite.hotkey not in metagraph.hotkeys:
            # Ignore requests from unrecognized entities.
            bt.logging.trace(
                f"Blacklisting unrecognized hotkey {synapse.dendrite.hotkey}"
            )
            return True, "Unrecognized hotkey"
        # TODO(developer): In practice it would be wise to blacklist requests from entities that
        # are not validators, or do not have enough stake. This can be checked via metagraph.S
        # and metagraph.validator_permit. You can always attain the uid of the sender via a
        # metagraph.hotkeys.index( synapse.dendrite.hotkey ) call.
        # Otherwise, allow the request to be processed further.
        bt.logging.trace(
            f"Not Blacklisting recognized hotkey {synapse.dendrite.hotkey}"
        )
        return False, "Hotkey recognized!"

    # The priority function determines the order in which requests are handled.
    # More valuable or higher-priority requests are processed before others.
    async def priority(self, synapse: template.protocol.Dummy) -> float:
        # TODO(developer): Define how miners should prioritize requests.
        # Miners may recieve messages from multiple entities at once. This function
        # determines which request should be processed first. Higher values indicate
        # that the request should be processed first. Lower values indicate that the
        # request should be processed later.
        # Below: simple logic, prioritize requests from entities with more stake.
        caller_uid = metagraph.hotkeys.index(
            synapse.dendrite.hotkey
        )  # Get the caller index.
        prirority = float(metagraph.S[caller_uid])  # Return the stake as the priority.
        bt.logging.trace(
            f"Prioritizing {synapse.dendrite.hotkey} with value: ", prirority
        )
        return prirority


# This is the main function, which runs the miner.
if __name__ == "__main__":
    with Neuron() as miner:
        while True:
            bt.logging.info("running...", time.time())
            time.sleep(5)