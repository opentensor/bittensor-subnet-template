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

# Bittensor Validator Template:
# TODO(developer): Rewrite based on protocol defintion.

# Step 1: Import necessary libraries and modules
import copy
import torch
import asyncio
import bittensor as bt
from abc import ABC, abstractmethod
from traceback import print_exception

from template.utils.config import check_config, add_args, config
from template.utils.misc import ttl_get_block

# Sync calls set weights and also resyncs the metagraph.
from template.utils.sync import sync


class BaseValidatorNeuron(ABC):

    @classmethod
    def check_config(cls, config: "bt.Config"):
        check_config(cls, config)

    @classmethod
    def add_args(cls, parser):
        add_args(cls, parser)

    @classmethod
    def config(cls):
        return config(cls)

    subtensor: "bt.subtensor"
    wallet: "bt.wallet"
    metagraph: "bt.metagraph"


    def __init__(self, config=None):

        base_config = copy.deepcopy(config or BaseValidatorNeuron.config())
        self.config = self.config()
        self.config.merge(base_config)

        # Set up logging with the provided configuration and directory.
        bt.logging(config=config, logging_dir=config.full_path)
        bt.logging.info(
            f"Running validator for subnet: {config.netuid} on network: {config.subtensor.chain_endpoint} with config:"
        )
        # Log the configuration for reference.
        bt.logging.info(config)

        # Step 4: Build Bittensor validator objects
        # These are core Bittensor classes to interact with the network.
        bt.logging.info("Setting up bittensor objects.")

        # The wallet holds the cryptographic key pairs for the validator.
        self.wallet = bt.wallet(config=config)
        bt.logging.info(f"Wallet: {self.wallet}")

        # The subtensor is our connection to the Bittensor blockchain.
        self.subtensor = bt.subtensor(config=config)
        bt.logging.info(f"Subtensor: {self.subtensor}")

        # Dendrite is the RPC client; it lets us send messages to other nodes (axons) in the network.
        self.dendrite = bt.dendrite(wallet=self.wallet)
        bt.logging.info(f"Dendrite: {self.dendrite}")

        # The metagraph holds the state of the network, letting us know about other validators and miners.
        self.metagraph = self.subtensor.metagraph(config.netuid)
        bt.logging.info(f"Metagraph: {self.metagraph}")

        sync( self )

        self.uid = self.metagraph.hotkeys.index(self.wallet.hotkey.ss58_address)
        bt.logging.info(f"Running validator on uid: {self.uid}")

        # Step 6: Set up initial scoring weights for validation
        bt.logging.info("Building validation weights.")
        self.scores = torch.ones_like(self.metagraph.S, dtype=torch.float32)
        bt.logging.info(f"Weights: {self.scores}")

        # Create asyncio event loop to manage async tasks.
        self.loop = asyncio.get_event_loop()
        self.step = 0

    @property
    def block(self):
        return ttl_get_block( self )

    @abstractmethod
    async def forward(self):
        # This method is responsible for the actual validation logic.
        ...

    # Run multiple forwards.
    async def run_forward(self):
        coroutines = [
            self.forward()
            for _ in range(self.config.neuron.num_concurrent_forwards)
        ]
        await asyncio.gather(*coroutines)

    def run(self):
        bt.logging.info("Starting validator loop.")

        try:
            while True:

                bt.logging.info(f"step({self.step}) block({self.block})")

                self.loop.run_until_complete( self.run_forward() )

                sync( self )

                self.step += 1

        # If someone intentionally stops the validator, it'll safely terminate operations.
        except KeyboardInterrupt:
            self.axon.stop()
            bt.logging.success("Miner killed by keyboard interrupt.")
            exit()

        # In case of unforeseen errors, the validator will log the error and continue operations.
        except Exception as err:
            bt.logging.error("Error during validation", str(err))
            bt.logging.debug(print_exception(type(err), err, err.__traceback__))


    def __enter__(self):
        """
        Starts the miner's operations in a background thread upon entering the context.
        This method facilitates the use of the miner in a 'with' statement.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Stops the miner's background operations upon exiting the context.
        This method facilitates the use of the miner in a 'with' statement.

        Args:
            exc_type: The type of the exception that caused the context to be exited.
                      None if the context was exited without an exception.
            exc_value: The instance of the exception that caused the context to be exited.
                       None if the context was exited without an exception.
            traceback: A traceback object encoding the stack trace.
                       None if the context was exited without an exception.
        """
        return self
