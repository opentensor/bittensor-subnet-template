import argparse
import json
import os
import re
import time
import traceback
import typing
import bittensor as bt
import yaml
from protocols.blockchain import NETWORK_BITCOIN, NETWORK_ETHEREUM
from protocols.llm_engine import LlmMessage, QueryOutput, LLM_ERROR_TYPE_NOT_SUPPORTED, LLM_ERROR_MESSAGES, \
    LLM_ERROR_GENERAL_RESPONSE_FAILED, LLM_CLIENT_ERROR

from insights import protocol
from neurons import logger
from neurons.miners import blacklist
from neurons.miners.llm_client import LLMClient
from neurons.remote_config import MinerConfig
from neurons.storage import store_miner_metadata
from template.base.miner import BaseMinerNeuron


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
        parser.add_argument("--netuid", type=int, default=15, help="The chain subnet uid.")
        parser.add_argument("--dev", action=argparse.BooleanOptionalAction)
        parser.add_argument(
            "--llm_engine_url",
            type=str,
            default="http://localhost:8912",
            help="LLM engine host",
        )

        bt.subtensor.add_args(parser)
        bt.logging.add_args(parser)
        bt.wallet.add_args(parser)
        bt.axon.add_args(parser)

        config = bt.config(parser)
        config.blacklist = dict(force_validator_permit=True, allow_non_registered=False)
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
                logger.info(f"config updated with {dev_config_path}")

            else:
                with open(dev_config_path, 'w') as f:
                    yaml.safe_dump(config, f)
                logger.info(f"config stored in {dev_config_path}")

        def _copy(newconfig, config, allow):
            if(isinstance(allow, str)):
                newconfig[allow] = config[allow]
            elif(isinstance(allow, tuple)):
                if(len(allow) == 1):
                    newconfig[allow[0]] = config[allow[0]]
                else:
                    if(newconfig.get(allow[0]) == None): newconfig[allow[0]] = {}
                    _copy(newconfig[allow[0]], config[allow[0]], allow[1:])

        def filter(config, allowlist):
            newconfig = {}
            for item in allowlist:
                _copy(newconfig, config, item)
            return newconfig

        whitelist_config_keys = {('axon', 'port'), 'graph_db_url', 'graph_db_user', 'llm_engine_url', ('logging', 'logging_dir'), ('logging', 'record_log'), 'netuid',
                                'network', ('subtensor', 'chain_endpoint'), ('subtensor', 'network'), 'wallet'}

        json_config = json.loads(json.dumps(config, indent=2))
        config_out = filter(json_config, whitelist_config_keys)
        logger.info('config', config = config_out)

        return config
    
    def __init__(self, config=None):
        config = Miner.get_config()

        super(Miner, self).__init__(config=config)
        
        self.request_timestamps: dict = {}
        
        self.axon = bt.axon(wallet=self.wallet, port=self.config.axon.port)        
        logger.info(f"Attaching forwards functions to miner axon.")
        (self.axon.attach(
            forward_fn=self.health_check,
            blacklist_fn=self.health_check_blacklist,
            priority_fn=self.health_check_priority)
        .attach(
            forward_fn=self.discovery,
            blacklist_fn=self.discovery_blacklist,
            priority_fn=self.discovery_priority,
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
        ))

        logger.info(f"Axon created: {self.axon}")

        self.miner_config = MinerConfig().load_and_get_config_values()
        self.llm = LLMClient(config.llm_engine_url)
        self.miner_config = MinerConfig().load_and_get_config_values()

    async def health_check(self, synapse: protocol.HealthCheck) -> protocol.HealthCheck:
        logger.info("Health check received")
        synapse.output = [{
            "network": self.config.network,
            "hotkey": self.wallet.hotkey.ss58_address,
            "uid": self.uid,
        }]
        return synapse

    async def discovery(self, synapse: protocol.Discovery) -> protocol.Discovery:
        try:
            discovery = self.llm.discovery_v1(network=self.config.network)
            if discovery is None:
                logger.error("Failed to query for discovery")
                synapse.output = None
                return synapse

            synapse.output = protocol.DiscoveryOutput(
                metadata=protocol.DiscoveryMetadata(
                    network=self.config.network,
                ),
                start_block_height=discovery['funds_flow_model_start_block'],
                block_height=discovery['funds_flow_model_ast_block'],
                balance_model_last_block=discovery['balance_model_last_block'],
            )
            logger.info("Serving miner discovery output",
                        output={
                            'metadata': {
                                'network': synapse.output.metadata.network,
                            },
                            'start_block_height': synapse.output.start_block_height,
                            'block_height': synapse.output.block_height,
                            'balance_model_last_block': synapse.output.balance_model_last_block,
                            'version': synapse.output.version})

        except Exception as e:
            logger.error('error', error=traceback.format_exc())
            synapse.output = None

        return synapse

    async def challenge(self, synapse: protocol.Challenge) -> protocol.Challenge:
        try:
            logger.info("challenge received", synapse={'version': synapse.version,
                                                       'in_total_amount': synapse.in_total_amount,
                                                       'out_total_amount': synapse.out_total_amount,
                                                       'tx_id_last_4_chars': synapse.tx_id_last_4_chars,
                                                       'checksum': synapse.checksum,
                                                       'output': synapse.output})

            if self.config.network == NETWORK_BITCOIN:
                challenge_output = self.llm.challenge_utxo_v1(network=self.config.network,
                                                              in_total_amount=synapse.in_total_amount,
                                                              out_total_amount=synapse.out_total_amount,
                                                              tx_id_last_4_chars=synapse.tx_id_last_4_chars)
                if challenge_output is None:
                    logger.error("Failed to query for challenge")
                    synapse.output = None
                else:
                    synapse.output = challenge_output['output']

            if self.config.network == NETWORK_ETHEREUM:
                challenge_output = self.llm.challenge_evm_v1(network=self.config.network, checksum=synapse.checksum)
                if challenge_output is None:
                    synapse.output = None
                else:
                    synapse.output = challenge_output['output']

            logger.info(f"Serving miner challenge", output = f"{synapse.output}")

        except Exception as e:
            logger.error('error', error=traceback.format_exc())
            synapse.output = None
        return synapse

    async def benchmark(self, synapse: protocol.Benchmark) -> protocol.Benchmark:
        try:
            logger.info(f"Executing benchmark query", query = synapse.query)
            pattern = self.miner_config.get_benchmark_query_regex(self.config.network)
            regex = re.compile(pattern)
            match = regex.fullmatch(synapse.query)
            if match is None:
                logger.error("Invalid benchmark query", query = synapse.query)
                synapse.output = None
            else:
                result = self.llm.benchmark_v1(network=self.config.network, query=synapse.query)
                if result is None:
                    synapse.output = None
                    logger.error("Failed to query for benchmark")
                else:
                    synapse.output = result['output']

            logger.info(f"Serving miner benchmark output", output = f"{synapse.output}")
        except Exception as e:
            logger.error('error', error = traceback.format_exc())
        return synapse

    async def llm_query(self, synapse: protocol.LlmQuery) -> protocol.LlmQuery:
        logger.info(f"llm query received: {synapse}")
        query_output = self.llm.llm_query_v1(synapse.messages)
        if query_output is None:
            logger.error("Failed to query for llm query")
            synapse.output = [QueryOutput(type="text", error=LLM_ERROR_GENERAL_RESPONSE_FAILED, interpreted_result=LLM_ERROR_MESSAGES[LLM_CLIENT_ERROR])]
        else:
            for query_output_item in query_output:
                query_output_item['miner_hotkey'] = self.wallet.hotkey.ss58_address

            synapse.output = query_output
            logger.info(f"Serving miner llm query output: {synapse.output}")

        return synapse

    async def health_check_blacklist(self, synapse: protocol.HealthCheck) -> typing.Tuple[bool, str]:
        return blacklist.base_blacklist(self, synapse=synapse)

    async def discovery_blacklist(self, synapse: protocol.Discovery) -> typing.Tuple[bool, str]:
        return blacklist.discovery_blacklist(self, synapse=synapse)

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
        priority = float(
            self.metagraph.S[caller_uid]
        )
        logger.trace("Prioritizing hotkey", hotkey=synapse.dendrite.hotkey, priority=priority)
        return priority

    async def health_check_priority(self, synapse: protocol.HealthCheck) -> float:
        return self.base_priority(synapse=synapse)

    async def discovery_priority(self, synapse: protocol.Discovery) -> float:
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


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    with Miner() as miner:
        while True:
            logger.info(f"Miner running")
            time.sleep(bt.__blocktime__*10)

