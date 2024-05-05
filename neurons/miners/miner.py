import argparse
import os
import time
import typing
import traceback
import yaml
import bittensor as bt
from insights import protocol

# import base miner class which takes care of most of the boilerplate
from template.base.miner import BaseMinerNeuron
from neurons.miners import blacklist
from insights.protocol import MODEL_TYPE_FUNDS_FLOW, MODEL_TYPE_BALANCE_TRACKING, NETWORK_BITCOIN, NETWORK_ETHEREUM, LLM_TYPE_CUSTOM, LLM_TYPE_OPENAI, \
    QueryOutput

from neurons.storage import store_miner_metadata
from neurons.remote_config import MinerConfig
from neurons.nodes.factory import NodeFactory
from neurons.miners.query import get_graph_search, get_graph_indexer, get_balance_search, get_balance_indexer
from insights.llm import LLMFactory


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
            "--llm_type",
            type=str,
            default=LLM_TYPE_OPENAI,
            help="Set miner's supported LLM type.",
        )

        parser.add_argument("--netuid", type=int, default=15, help="The chain subnet uid.")
        parser.add_argument("--dev", action=argparse.BooleanOptionalAction)

        bt.subtensor.add_args(parser)
        bt.logging.add_args(parser)
        bt.wallet.add_args(parser)
        bt.axon.add_args(parser)

        config = bt.config(parser)
        config.blacklist  = dict(force_validator_permit=True, allow_non_registered=False)
        config.wait_for_sync = os.environ.get('WAIT_FOR_SYNC', 'False')=='True'
        config.graph_db_url = os.environ.get('GRAPH_DB_URL', 'bolt://localhost:7687')
        config.graph_db_user = os.environ.get('GRAPH_DB_USER', 'user')
        config.graph_db_password = os.environ.get('GRAPH_DB_PASSWORD', 'pwd')

        config.db_connection_string = os.environ.get('DB_CONNECTION_STRING', '')
        
        dev = config.dev
        if dev:
            dev_config_path = "miner.yml"
            if os.path.exists(dev_config_path):
                with open(dev_config_path, 'r') as f:
                    dev_config = yaml.safe_load(f.read())
                config.update(dev_config)
                bt.logging.info(f"config updated with {dev_config_path}")

            else:
                with open(dev_config_path, 'w') as f:
                    yaml.safe_dump(config, f)
                bt.logging.info(f"config stored in {dev_config_path}")

        return config
    
    def __init__(self, config=None):
        config = Miner.get_config()
        
        super(Miner, self).__init__(config=config)
        
        self.request_timestamps: dict = {}
        
        self.axon = bt.axon(wallet=self.wallet, port=self.config.axon.port)        
        # Attach determiners which functions are called when servicing a request.
        bt.logging.info(f"Attaching forwards functions to miner axon.")
        self.axon.attach(
            forward_fn=self.discovery,
            blacklist_fn=self.discovery_blacklist,
            priority_fn=self.discovery_priority,
        ).attach(
            forward_fn=self.query,
            blacklist_fn=self.query_blacklist,
            priority_fn=self.query_priority,
        ).attach(
            forward_fn=self.challenge,
            blacklist_fn=self.challenge_blacklist,
            priority_fn=self.challenge_priority,
        ).attach(
            forward_fn=self.benchmark,
            blacklist_fn=self.benchmark_blacklist,
            priority_fn=self.benchmark_priority
        ).attach(
            forward_fn=self.llm_query,
            blacklist_fn=self.llm_query_blacklist,
            priority_fn=self.llm_query_priority
        )

        bt.logging.info(f"Axon created: {self.axon}")

        self.graph_search = get_graph_search(config)
        self.balance_search = get_balance_search(config)
        self.miner_config = MinerConfig().load_and_get_config_values()
        self.llm = LLMFactory.create_llm(config.llm_type)
        self.graph_search = get_graph_search(config)

        self.miner_config = MinerConfig().load_and_get_config_values()

    async def discovery(self, synapse: protocol.Discovery ) -> protocol.Discovery:
        try:
            start_block, last_block = self.graph_search.get_min_max_block_height_cache()
            balance_model_last_block = self.balance_search.get_latest_block_number()
            synapse.output = protocol.DiscoveryOutput(
                metadata=protocol.DiscoveryMetadata(
                    network=self.config.network,
                ),
                start_block_height=start_block,
                block_height=last_block,
                balance_model_last_block=balance_model_last_block,
            )
            bt.logging.info(f"Serving miner discovery output: {synapse.output}")
        except Exception as e:
            bt.logging.error(traceback.format_exc())
            synapse.output = None
        return synapse

    async def query(self, synapse: protocol.Query ) -> protocol.Query:
        try:
            synapse.output = QueryOutput(result=self.graph_search.execute_query(query=synapse))
        except Exception as e:
            bt.logging.error(traceback.format_exc())
            synapse.output = QueryOutput(error=e)
        return synapse

    async def challenge(self, synapse: protocol.Challenge ) -> protocol.Challenge:
        try:
            bt.logging.info(f"challenge received: {synapse}")

            if self.config.network == NETWORK_BITCOIN:
                synapse.output = self.graph_search.solve_challenge(
                    in_total_amount=synapse.in_total_amount,
                    out_total_amount=synapse.out_total_amount,
                    tx_id_last_4_chars=synapse.tx_id_last_4_chars
                )
            if self.config.network == NETWORK_ETHEREUM:
                synapse.output = self.graph_search.solve_challenge(
                    checksum=synapse.checksum,
                )

            bt.logging.info(f"Serving miner challenge output: {synapse.output}")

        except Exception as e:
            bt.logging.error(traceback.format_exc())
            synapse.output = None
        return synapse

    async def benchmark(self, synapse: protocol.Benchmark) -> protocol.Benchmark:
        try:
            bt.logging.info(f"Executing benchmark query: {synapse.query}")

            result = self.graph_search.execute_benchmark_query(cypher_query=synapse.query)
            synapse.output = result[0]

            bt.logging.info(f"Serving miner benchmark output: {synapse.output}")
        except Exception as e:
            bt.logging.error(traceback.format_exc())
        return synapse

    async def llm_query(self, synapse: protocol.LlmQuery ) -> protocol.LlmQuery:
        bt.logging.info(f"llm query received: {synapse}")
        synapse.output = {}

        try:
            # TODO: handle llm query
            query = self.llm.build_query_from_messages(synapse.messages)
            bt.logging.info(f"extracted query: {query}")
            
            result = self.graph_search.execute_query(query=query)
            interpreted_result = self.llm.interpret_result(llm_messages=synapse.messages, result=result)

            synapse.output = QueryOutput(result=result, interpreted_result=interpreted_result)

        except Exception as e:
            bt.logging.error(traceback.format_exc())
            error_code = e.args[0]
            if error_code == protocol.LLM_ERROR_TYPE_NOT_SUPPORTED:
                # handle unsupported query templates
                try:
                    interpreted_result = self.llm.generate_general_response(llm_messages=synapse.messages)
                    synapse.output = QueryOutput(error=error_code, interpreted_result=interpreted_result)
                except Exception as e:
                    error_code = e.args[0]
                    synapse.output = QueryOutput(error=error_code, interpreted_result=protocol.LLM_ERROR_MESSAGES[error_code])
            else:
                synapse.output = QueryOutput(error=error_code, interpreted_result=protocol.LLM_ERROR_MESSAGES[error_code])

        bt.logging.info(f"Serving miner llm query output: {synapse.output}")
        return synapse

    async def discovery_blacklist(self, synapse: protocol.Discovery) -> typing.Tuple[bool, str]:
        return blacklist.discovery_blacklist(self, synapse=synapse)

    async def query_blacklist(self, synapse: protocol.Query) -> typing.Tuple[bool, str]:
        return blacklist.query_blacklist(self, synapse=synapse)

    async def challenge_blacklist(self, synapse: protocol.Challenge) -> typing.Tuple[bool, str]:
        return blacklist.base_blacklist(self, synapse=synapse)

    async def benchmark_blacklist(self, synapse: protocol.Benchmark) -> typing.Tuple[bool, str]:
        return blacklist.base_blacklist(self, synapse=synapse)
 
    async def llm_query_blacklist(self, synapse: protocol.LlmQuery) -> typing.Tuple[bool, str]:
        return blacklist.base_blacklist(self, synapse=synapse)
    
    def base_priority(self, synapse: bt.Synapse) -> float:
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
    
    async def discovery_priority(self, synapse: protocol.Discovery) -> float:
        return self.base_priority(synapse=synapse)

    async def query_priority(self, synapse: protocol.Query) -> float:
        return self.base_priority(synapse=synapse)

    async def challenge_priority(self, synapse: protocol.Challenge) -> float:
        return self.base_priority(synapse=synapse)

    async def llm_query_priority(self, synapse: protocol.LlmQuery) -> float:
        return self.base_priority(synapse=synapse)

    async def benchmark_priority(self, synapse: protocol.Benchmark) -> float:
        return self.base_priority(synapse=synapse)

    def resync_metagraph(self):
        self.miner_config = MinerConfig().load_and_get_config_values()       
        super(Miner, self).resync_metagraph()

    def should_send_metadata(self):        
        return (
            self.block - self.last_message_send
        ) > self.miner_config.store_metadata_frequency
    
    def send_metadata(self):
        store_miner_metadata(self)


def wait_for_blocks_sync():
        is_synced=False

        config = Miner.get_config()
        if not config.wait_for_sync:
            bt.logging.info(f"Skipping graph sync.")
            return is_synced
        
        miner_config = MinerConfig().load_and_get_config_values()
        
        delta = miner_config.get_blockchain_sync_delta(config.network)
        bt.logging.info(f"Waiting for graph model to sync with blockchain.")
        while not is_synced:
            try:
                graph_indexer = get_graph_indexer(config)
                node = NodeFactory.create_node(config.network)

                latest_block_height = node.get_current_block_height()
                current_block_height = graph_indexer.get_latest_block_number()
                delta = latest_block_height - current_block_height
                if delta < 100:
                    is_synced = True
                    bt.logging.success(f"Graph model is synced with blockchain.")
                else:
                    bt.logging.info(f"Graph Sync: {current_block_height}/{latest_block_height}")
                    time.sleep(bt.__blocktime__ * 12)
            except Exception as e:
                bt.logging.error(traceback.format_exc())
                time.sleep(bt.__blocktime__ * 12)
                bt.logging.info(f"Failed to connect with graph database. Retrying...")
                continue
        return is_synced


# This is the main function, which runs the miner.
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    wait_for_blocks_sync()
    with Miner() as miner:
        while True:
            bt.logging.info(f"Miner running")
            time.sleep(bt.__blocktime__*2)

