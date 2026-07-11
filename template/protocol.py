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

import typing

import bittensor as bt

# TODO(developer): Rewrite with your protocol definition.

# This is the protocol for an inference-focused subnet.
# Validators send a prompt and miners return a response string.

# ---- miner ----
# Example usage:
#   def generate( synapse: Inference ) -> Inference:
#       synapse.response = run_model(synapse.prompt)
#       return synapse
#   axon = bt.axon().attach( generate ).serve(netuid=...).start()

# ---- validator ---
# Example usage:
#   dendrite = bt.dendrite()
#   response = dendrite.query( Inference( prompt="hello" ) )
#   assert response == "bonjour"


class Inference(bt.Synapse):
    """
    A protocol representation for inference request/response.

    Attributes:
    - prompt: The input prompt or task request sent by the validator.
    - task_id: Optional task identifier for tracking.
    - response: Optional model response text filled by the miner.
    - model_name: Optional model identifier reported by the miner.
    """

    # Required request input, filled by sending dendrite caller.
    prompt: str

    # Optional task identifier set by the validator.
    task_id: typing.Optional[str] = None

    # Optional response output, filled by receiving axon.
    response: typing.Optional[str] = None

    # Optional model name reported by the miner.
    model_name: typing.Optional[str] = None

    def deserialize(self) -> typing.Dict[str, str]:
        """
        Deserialize the response text. This method retrieves the response from
        the miner and returns a structured payload from the dendrite.query()
        call.

        Returns:
        - Dict[str, str]: A dictionary with the response text and model name.
        """
        return {
            "response": self.response or "",
            "model_name": self.model_name or "",
        }
