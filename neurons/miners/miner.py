import argparse
import os
import time
import typing
import traceback
import random

import bittensor as bt

from insights import protocol

from neurons.miners.query import (
    execute_query_proxy,
    get_graph_search,
)

# import base miner class which takes care of most of the boilerplate
from template.base.miner import BaseMinerNeuron

from neurons.miners import blacklist
from insights.protocol import MODEL_TYPE_FUNDS_FLOW, NETWORK_BITCOIN
from neurons import VERSION

from neurons.storage import store_miner_metadata
from neurons.remote_config import MinerConfig
from neurons.miners.bitcoin.funds_flow.graph_indexer import GraphIndexer
from neurons.nodes.factory import NodeFactory

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
        config = Miner.get_config()
        self.wait_for_blocks_sync()
        
        super(Miner, self).__init__(config=config)

        self.request_timestamps: dict = {}
        
        self.axon = bt.axon(wallet=self.wallet, port=self.config.axon.port)        
        # Attach determiners which functions are called when servicing a request.
        bt.logging.info(f"Attaching forwards functions to miner axon.")
        self.axon.attach(
            forward_fn=self.block_check,
            blacklist_fn=self.base_blacklist,
            priority_fn=self.base_priority,
        ).attach(
            forward_fn=self.discovery,
            blacklist_fn=self.discovery_blacklist,
            priority_fn=self.base_priority,
        ).attach(
            forward_fn=self.query,
            blacklist_fn=self.query_blacklist,
            priority_fn=self.base_priority,
        )
        bt.logging.info(f"Axon created: {self.axon}")

        self.graph_search = get_graph_search(config.network, config.model_type)

    def wait_for_blocks_sync(self):
        bt.logging.info(f"Waiting for graph model to sync with blockchain.")
        is_synced=False
        while not is_synced:
            wait_for_sync = os.getenv('WAIT_FOR_SYNC', 'True')
            if wait_for_sync == 'False':
                bt.logging.info(f"Skipping graph sync.")
                break

            try:
                graph_indexer = GraphIndexer(self.config.graph_db_url)
                node = NodeFactory.create_node(self.config.network)
                latest_block_height =  node.get_current_block_height()
                current_block_height = graph_indexer.get_latest_block_number()
                if latest_block_height - current_block_height < 100:
                    is_synced = True
                    bt.logging.info(f"Graph model is synced with blockchain.")
                else:
                    bt.logging.info(f"Graph Sync: {current_block_height}/{latest_block_height}")
                    time.sleep(bt.__blocktime__ * 12)
            except Exception as e:
                bt.logging.error(traceback.format_exc())
                time.sleep(bt.__blocktime__ * 12)
                bt.logging.info(f"Failed to connect with graph database. Retrying...")
                continue
    
    async def block_check(self, synapse: protocol.BlockCheck) -> protocol.BlockCheck:
        try:
            block_heights = synapse.blocks_to_check
            data_samples = self.graph_search.get_block_transactions(block_heights)
            synapse.output = protocol.BlockCheckOutput(
                data_samples=data_samples,
            )
            bt.logging.info(f"Serving miner random block check output: {synapse.output}")
        except Exception as e:
            bt.logging.error(traceback.format_exc())
            synapse.output = None
        return synapse
            
    async def discovery(self, synapse: protocol.Discovery ) -> protocol.Discovery:
        try:
            block_range = self.graph_search.get_block_range()
            start_block = block_range['start_block_height']
            last_block = block_range['latest_block_height']

            block_heights = random.sample(range(start_block, last_block + 1), 10)
            data_samples = self.graph_search.get_block_transactions(block_heights)
            run_id = self.graph_search.get_run_id()

            synapse.output = protocol.DiscoveryOutput(
                metadata=protocol.DiscoveryMetadata(
                    network=self.config.network,
                    model_type=self.model_type,
                ),
                start_block_height=start_block,
                block_height=last_block,
                data_samples=data_samples,
                run_id=run_id,
                version=VERSION,
            )
            bt.logging.info(f"Serving miner discovery output: {synapse.output}")
        except Exception as e:
            bt.logging.error(traceback.format_exc())
            synapse.output = None
        return synapse

    async def query(self, synapse: protocol.Query ) -> protocol.Query:
        try:
            synapse.output = self.graph_search.execute_query(
                network=synapse.network, query=synapse.query)
        except Exception as e:
            bt.logging.error(traceback.format_exc())
            synapse.output = None
        return synapse

    async def base_blacklist(self, synapse: bt.Synapse) -> typing.Tuple[bool, str]:
        return blacklist.base_blacklist(self, synapse=synapse)

    async def discovery_blacklist(self, synapse: protocol.Discovery) -> typing.Tuple[bool, str]:
        return blacklist.discovery_blacklist(self, synapse=synapse)

    async def query_blacklist(self, synapse: protocol.Query) -> typing.Tuple[bool, str]:
        return blacklist.query_blacklist(self, synapse=synapse)


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
        super(Miner, self).resync_metagraph()

        #reload our config
        self.miner_config = MinerConfig().load_and_get_config_values()
        store_miner_metadata(self.config, self.graph_search, self.wallet)


# This is the main function, which runs the miner.
if __name__ == "__main__":
    with Miner() as miner:
        while True:
            bt.logging.info("Miner running...", time.time())
            time.sleep(5)
