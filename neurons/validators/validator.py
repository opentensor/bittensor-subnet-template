# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2023 aph5nt
import concurrent
import json
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

import time
import argparse
import random
import torch
import bittensor as bt

from insights import protocol
from insights.protocol import DiscoveryOutput, BlockCheckOutput, MAX_MULTIPLE_IPS, \
    MAX_MULTIPLE_RUN_ID

from neurons import VERSION
from neurons.remote_config import ValidatorConfig
from neurons.nodes.factory import NodeFactory
from neurons.storage import store_validator_metadata, get_miners_metadata
from neurons.validators.scoring import Scorer

from neurons.validators.utils.utils import get_miner_distributions, count_hotkeys_per_ip, count_run_id_per_hotkey
from neurons.validators.utils.uids import get_random_uids

from template.base.validator import BaseValidatorNeuron
class Validator(BaseValidatorNeuron):

    @staticmethod
    def get_config():

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--alpha", default=0.9, type=float, help="The weight moving average scoring.py."
        )

        parser.add_argument("--netuid", type=int, default=15, help="The chain subnet uid.")
        parser.add_argument("--mode", type=str, default="prod", help="(staging|testnet|prod)")

        bt.subtensor.add_args(parser)
        bt.logging.add_args(parser)
        bt.wallet.add_args(parser)

        config = bt.config(parser)

        bt.logging.info(f"running in {config.mode} mode")
        if config.mode == "staging":
            # Local development settings
            config.subtensor.chain_endpoint = "ws://163.172.164.213:9944"
            config.wallet.hotkey = 'default'
            config.wallet.name = 'validator'
            config.netuid = 1
            config.logging.debug = True
            config.logging.trace = True
            config.miner_set_weights = True
            config.neuron={'vpermit_tao_limit' : 0}
        elif config.mode == 'testnet':
            config.subtensor.network = 'test'
            config.subtensor.chain_endpoint = None
            config.wallet.hotkey = 'default'
            config.wallet.name = 'validator'
            config.netuid = 59
            config.logging.debug = True
            config.logging.trace = True
            config.miner_set_weights = True
            config.neuron={'vpermit_tao_limit' : 0}

        return config

    def __init__(self, config=None):
        config=Validator.get_config()
        super(Validator, self).__init__(config)
        
        bt.logging.info("load_state()")
        self.load_state()
        
        self.validator_uid = self.metagraph.hotkeys.index(self.wallet.hotkey.ss58_address)
        bt.logging.info(f"Running validator on uid: {self.validator_uid}")
        store_validator_metadata(self.config, self.wallet, self.validator_uid)

    def should_set_weights(self) -> bool:
        if self.step == 0:
            return False

        if self.config.neuron.disable_set_weights:
            return False

        return (
            self.block - self.metagraph.last_update[self.uid]
        ) > 100

    def should_sync_metagraph(self):
        """
        Check if enough epoch blocks have elapsed since the last checkpoint to sync.
        """
        return (
            self.block - self.metagraph.last_update[self.uid]
        ) > 5

    def cross_validate(self, axon, node, start_block_height, last_block_height, k=10):
        blocks_to_check = random.sample(range(start_block_height, last_block_height + 1), k=k)
        random_block_response = self.dendrite.query(
            [axon],
            protocol.BlockCheck(blocks_to_check=blocks_to_check),
            deserialize=True,
            timeout = self.validator_config.discovery_timeout,
        )

        random_block_response = random_block_response[0]
        if random_block_response.output is None or random_block_response.output:
            bt.logging.debug(f"Skipping response {random_block_response}")
            return None
        
        blocks_to_check_output: BlockCheckOutput = random_block_response.output
        return node.validate_all_data_samples(blocks_to_check_output.data_samples)


    def get_reward(self, response: DiscoveryOutput, ip_per_hotkey=None, run_id_per_hotkey=None, miner_distribution=None):
        if response.output.version < VERSION and self.validator_config.grace_period:
            score = 0.15
            bt.logging.info(f"Miner is running an old version. Grace period is enabled. Score set to {score}.")
            return score
        if response.output.version != VERSION and not self.validator_config.grace_period:            
            score = 0
            bt.logging.info(f"Miner is running an old version. Grace period is disabled. Score set to {score}")
            return score

        output: DiscoveryOutput = response.output
        network = output.metadata.network
        start_block_height = output.start_block_height
        last_block_height = output.block_height
        data_samples = output.data_samples
        axon_ip = response.axon.ip
        hot_key = response.axon.hotkey
        response_time = response.dendrite.process_time
        bt.logging.info(f"🔄 Processing response for {hot_key}@{axon_ip}")

        data_samples_are_valid = self.nodes[network].validate_all_data_samples(data_samples)

        multiple_ips = ip_per_hotkey[axon_ip] > MAX_MULTIPLE_IPS
        multiple_run_ids = run_id_per_hotkey[hot_key] > MAX_MULTIPLE_RUN_ID

        score = self.scorer.calculate_score(
            network,
            response_time,
            start_block_height,
            last_block_height,
            self.block_height_cache[network],
            data_samples_are_valid,
            miner_distribution,
            multiple_ips,
            multiple_run_ids
        )
        cross_validation_result = self.cross_validate(response.axon, self.nodes[network], start_block_height, last_block_height)

        if cross_validation_result is None:
            bt.logging.debug(f"Cross-Validation: {hot_key=} Timeout skipping response")
            return None
        if not cross_validation_result:
            bt.logging.info(f"Cross-Validation: {hot_key=} Test failed")
            return 0
        bt.logging.info(f"Cross-Validation: {hot_key=} Test passed")
        return score

    async def forward(self):
        available_uids = get_random_uids(self, self.config.neuron.sample_size)

        filtered_axons = [self.metagraph.axons[uid] for uid in available_uids]
        
        ip_per_hotkey = count_hotkeys_per_ip(filtered_axons)
        run_id_per_hotkey = count_run_id_per_hotkey(self.miners_metadata)
        miner_distribution = get_miner_distributions(self.miners_metadata, self.validator_config.get_networks())
        
        bt.logging.info(f"filtered axons: {filtered_axons}")
        responses = self.dendrite.query(
            filtered_axons,
            protocol.Discovery(),
            deserialize=True,
            timeout = self.validator_config.discovery_timeout,
        )

        valid_uids = []
        valid_responses = []
        for uid, response in zip(available_uids, responses):
            if response and response.output and self.miners_metadata.get(response.axon.hotkey):
                valid_uids.append(uid)
                valid_responses.append(response)
            else:
                bt.logging.info(f"skipping {response=} do not meet requirement")
        
        if valid_responses:
            rewards = [
                self.get_reward(response, 
                                ip_per_hotkey=ip_per_hotkey,
                                run_id_per_hotkey=run_id_per_hotkey,
                                miner_distribution=miner_distribution) for response in valid_responses
            ]
            
            # Remove None reward as they represent timeout cross validation
            filtered_data = [(reward, uid) for reward, uid in zip(rewards, valid_uids) if reward is not None]
            rewards, valid_uids = zip(*filtered_data)

            rewards = torch.FloatTensor(rewards)
            self.update_scores(rewards, valid_uids)

    def resync_metagraph(self):
        super(Validator, self).resync_metagraph()

        #reload our config
        self.miners_metadata = get_miners_metadata(self.config, self.metagraph)
        self.validator_config = ValidatorConfig().load_and_get_config_values()
        self.scorer = Scorer(self.validator_config)

        networks = self.validator_config.get_networks()
        self.nodes = {network : NodeFactory.create_node(network) for network in networks}
        self.block_height_cache = {network: self.nodes[network].get_current_block_height() for network in networks}



if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    with Validator() as validator:
        while True:
            bt.logging.info("Validator running...", time.time())
            time.sleep(10)
