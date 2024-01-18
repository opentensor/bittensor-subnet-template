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

import os
import time
import typing
import bittensor as bt

from insights import protocol
# Bittensor Miner Template:
import template

# import base miner class which takes care of most of the boilerplate
from template.base.miner import BaseMinerNeuron
import argparse

from insights.protocol import (
    MODEL_TYPE_FUNDS_FLOW,
    NETWORK_BITCOIN,
    MinerDiscoveryMetadata, get_network_id, get_model_id,
)
from neurons.remote_config import MinerConfig
from neurons.miners.query import is_query_only

class Miner(BaseMinerNeuron):
    """
    Your miner neuron class. You should use this class to define your miner's behavior. In particular, you should replace the forward function with your own logic. You may also want to override the blacklist and priority functions according to your needs.

    This class inherits from the BaseMinerNeuron class, which in turn inherits from BaseNeuron. The BaseNeuron class takes care of routine tasks such as setting up wallet, subtensor, metagraph, logging directory, parsing config, etc. You can override any of the methods in BaseNeuron if you need to customize the behavior.

    This class provides reasonable default behavior for a miner such as blacklisting unrecognized hotkeys, prioritizing requests based on stake, and forwarding requests to the forward function. If you need to define custom
    """
    @staticmethod
    def get_config():

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--network",
            default=NETWORK_BITCOIN,
            help="Set miner's supported blockchain network.",
        )
        parser.add_argument(
            "--model_type",
            type=str,
            default=MODEL_TYPE_FUNDS_FLOW,
            help="Set miner's supported model type.",
        )

        parser.add_argument("--netuid", type=int, default=15, help="The chain subnet uid.")

        
        bt.subtensor.add_args(parser)
        bt.logging.add_args(parser)
        bt.wallet.add_args(parser)
        bt.axon.add_args(parser)

        config = bt.config(parser)

        bt.logging.info(f"running in {config.mode} mode")
        common_settings = {
                'wallet.hotkey': 'default',
                'wallet.name': 'miner',
                'logging.debug': True,
                'logging.trace': True,
                'miner_set_weights': True,
                'WAIT_FOR_SYNC': 'False',
                'GRAPH_DB_URL': 'bolt://localhost:7687',
                'GRAPH_DB_USER': 'user',
                'GRAPH_DB_PASSWORD': 'pwd',
                'BT_AXON_PORT': '8191'
            }

        if config.mode == 'staging':
            staging_settings = {
                'subtensor.chain_endpoint': 'ws://163.172.164.213:9944',
                'netuid': 1
            }
            config.update(common_settings)
            config.update(staging_settings)

        elif config.mode == 'testnet':
            testnet_settings = {
                'subtensor.network': 'test',
                'subtensor.chain_endpoint': None,
                'netuid': 59
            }
            config.update(common_settings)
            config.update(testnet_settings)
        return config
    
    def __init__(self, config=None):
        super(Miner, self).__init__(config=config)

        self.miner_config = MinerConfig().load_and_get_config_values()
        self.axon = bt.axon(wallet=self.wallet, port=self.config.axon.port)

        # Attach determiners which functions are called when servicing a request.
        bt.logging.info(f"Attaching forward function to miner axon.")
        self.axon.attach(
            forward_fn=self.block_check,
            blacklist_fn=self.base_blacklist,
            priority_fn=self.base_priority,
        ).attach(
            forward_fn=self.discovery,
            blacklist_fn=self.base_blacklist,
            priority_fn=self.base_priority,
        )
        bt.logging.info(f"Axon created: {self.axon}")

    
    async def block_check(self, synapse: protocol.BlockCheck) -> protocol.BlockCheck:
            try:
                graph_search = get_graph_search(config.network, config.model_type)
                block_heights = synapse.blocks_to_check
                data_samples = graph_search.get_block_transactions(block_heights)
                synapse.output = protocol.MinerRandomBlockCheckOutput(
                    data_samples=data_samples,
                )
                bt.logging.info(f"Serving miner random block check output: {synapse.output}")

                return synapse
            except Exception as e:
                bt.logging.error(traceback.format_exc())
                synapse.output = None
                return synapse
    async def discovery(self, synapse: protocol.Discovery ) -> protocol.Discovery:
        pass
            
    async def base_blacklist(self, synapse: bt.Synapse) -> typing.Tuple[bool, str]:
        if synapse.dendrite.hotkey not in self.metagraph.hotkeys:
            bt.logging.trace(
                f"Blacklisting unrecognized hotkey {synapse.dendrite.hotkey}"
            )
            return True, "Unrecognized hotkey"
        
        if synapse.network != self.config.blockchain:
            bt.logging.trace(
                f"Blacklisting hot key {synapse.dendrite.hotkey} because of wrong blockchain"
            )
            return True, "Blockchain not supported."
        if synapse.model_type != self.config.model_type:
            bt.logging.trace(
                f"Blacklisting hot key {synapse.dendrite.hotkey} because of wrong model type"
            )
            return True, "Model type not supported."
        if not is_query_only(synapse.query):
            bt.logging.trace(
                f"Blacklisting hot key {synapse.dendrite.hotkey} because of illegal cypher keywords"
            )
            return True, "Illegal cypher keywords."
        
        bt.logging.trace(
            f"Not Blacklisting recognized hotkey {synapse.dendrite.hotkey}"
        )
        return False, "Hotkey recognized!"

    async def base_priority(self, synapse: bt.Synapse) -> float:
        caller_uid = self.metagraph.hotkeys.index(
            synapse.dendrite.hotkey
        ) 
        prirority = float(
            self.metagraph.S[caller_uid]
        )
        bt.logging.trace(
            f"Prioritizing {synapse.dendrite.hotkey} with value: ", prirority
        )
        return prirority
    
    def resync_metagraph(self):
        """Resyncs the metagraph and updates the hotkeys and moving averages based on the new metagraph."""
        bt.logging.info("resync_metagraph()")

        # Sync the metagraph.
        self.metagraph.sync(subtensor=self.subtensor)

# This is the main function, which runs the miner.
if __name__ == "__main__":
    with Miner() as miner:
        while True:
            bt.logging.info("Miner running...", time.time())
            time.sleep(5)
