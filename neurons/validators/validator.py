# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2023 aph5nt


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
import traceback
import torch
import bittensor as bt
import os
import yaml

from insights.protocol import Discovery, DiscoveryOutput, MAX_MINER_INSTANCE

from neurons.remote_config import ValidatorConfig
from neurons.nodes.factory import NodeFactory
from neurons.storage import store_validator_metadata
from neurons.validators.scoring import Scorer
from neurons.validators.uptime import UptimeManager
from neurons.validators.utils.metadata import Metadata
from neurons.validators.utils.synapse import is_discovery_response_valid

from neurons.validators.utils.uids import get_uids_batch

from template.base.validator import BaseValidatorNeuron
class Validator(BaseValidatorNeuron):

    @staticmethod
    def get_config():

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--alpha", default=0.9, type=float, help="The weight moving average scoring.py."
        )

        parser.add_argument("--netuid", type=int, default=15, help="The chain subnet uid.")
        parser.add_argument("--dev", action=argparse.BooleanOptionalAction)

        bt.subtensor.add_args(parser)
        bt.logging.add_args(parser)
        bt.wallet.add_args(parser)

        config = bt.config(parser)
        
        dev = config.dev
        if dev:
            dev_config_path = "validator.yml"
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
        config=Validator.get_config()
        self.validator_config = ValidatorConfig().load_and_get_config_values()
        networks = self.validator_config.get_networks()
        self.nodes = {network : NodeFactory.create_node(network) for network in networks}
        self.block_height_cache = {network: self.nodes[network].get_current_block_height() for network in networks}
        super(Validator, self).__init__(config)

        self.sync_validator()
        self.uid_batch_generator = get_uids_batch(self, self.config.neuron.sample_size)
        self.uptime_manager = UptimeManager(self, db_url='sqlite:///data/miners_uptime.db')

        
    def cross_validate(self, axon, node, start_block_height, last_block_height):
        try:
            challenge, expected_response = node.create_challenge(start_block_height, last_block_height)
            
            response = self.dendrite.query(
                axon,
                challenge,
                deserialize=False,
                timeout = self.validator_config.challenge_timeout,
            )
            
            if response is None or response.output is None:
                bt.logging.debug("Cross validation failed")
                return False, 128
            
            response_time = response.dendrite.process_time
            
            # if the miner's response is different from the expected response and validation failed
            if not response.output == expected_response and not node.validate_challenge_response_output(challenge, response.output):
                return False, response_time
            
            return True, response_time
        except Exception as e:
            bt.logging.error(f"Cross validation error occurred: {e}")
            return None, None

    def is_miner_metadata_valid(self, response: Discovery):
        hotkey = response.axon.hotkey
        ip = response.axon.ip
        run_id = response.output.run_id
        
        hotkey_meta = self.metadata.get_metadata_for_hotkey(hotkey)

        if not (hotkey_meta and hotkey_meta['run_id'] and hotkey_meta['network']):
            bt.logging.info(f'Validation Failed: hotkey={hotkey} unable to retrieve miner metadata')
            return False

        ip_count = self.metadata.ip_distribution.get(ip, 0)
        run_id_count = self.metadata.run_id_distribution.get(run_id, 0)
        coldkey_count = self.metadata.coldkey_distribution.get(hotkey, 0)

        bt.logging.info(f"🔄 Processing response for {hotkey}@{ip}")
        if ip_count > MAX_MINER_INSTANCE:
            bt.logging.info(f'Validation Failed: hotkey={hotkey} has {ip_count} ip')
            return False
        if run_id_count > MAX_MINER_INSTANCE:
            bt.logging.info(f'Validation Failed: hotkey={hotkey} has {run_id} run_id')
            return False
        if coldkey_count > MAX_MINER_INSTANCE:
            bt.logging.info(f'Validation Failed: Coldkey of hotkey={hotkey} has {coldkey_count} hotkeys')
            return False
        
        bt.logging.info(f'hotkey={hotkey} has {ip_count} ip, {run_id_count} run_id, {coldkey_count} hotkeys for its coldkey')

        return True
    
    def is_response_status_code_valid(self, response):
            status_code = response.axon.status_code
            status_message = response.axon.status_message
            if response.is_failure:
                bt.logging.info(f"Discovery response: Failure, miner {response.axon.hotkey} returned {status_code=}: {status_message=}")
            elif response.is_blacklist:
                bt.logging.info(f"Discovery response: Blacklist, miner {response.axon.hotkey} returned {status_code=}: {status_message=}")
            elif response.is_timeout:
                bt.logging.info(f"Discovery response: Timeout, miner {response.axon.hotkey}")
            return status_code == 200

    def get_reward(self, response: Discovery, uid: int):
        try:
            self.uptime_manager.try_update_miner(uid, response.axon.hotkey)

            if not self.is_response_status_code_valid(response):
                score = self.metagraph.T[uid]/2
                self.uptime_manager.down(uid, response.axon.hotkey)
                bt.logging.debug(f'Discovery Response error: hotkey={response.axon.hotkey}, setting score to {score}')
                return score
            if not is_discovery_response_valid(response):
                self.uptime_manager.down(uid, response.axon.hotkey)
                bt.logging.debug(f'Discovery Response invalid {response}')
                return 0
            if not self.is_miner_metadata_valid(response):
                self.uptime_manager.down(uid, response.axon.hotkey)
                return 0
            
            output: DiscoveryOutput = response.output
            network = output.metadata.network
            start_block_height = output.start_block_height
            last_block_height = output.block_height
            hotkey = response.axon.hotkey

            cross_validation_result, response_time = self.cross_validate(response.axon, self.nodes[network], start_block_height, last_block_height)

            if cross_validation_result is None:
                self.uptime_manager.down(uid, response.axon.hotkey)
                bt.logging.debug(f"Cross-Validation: {hotkey=} Timeout skipping response")
                return None
            if not cross_validation_result:
                self.uptime_manager.down(uid, response.axon.hotkey)
                bt.logging.info(f"Cross-Validation: {hotkey=} Test failed")
                return 0
            bt.logging.info(f"Cross-Validation: {hotkey=} Test passed")

            self.uptime_manager.up(uid, response.axon.hotkey)
            uptime_score = self.uptime_manager.get_uptime_scores(uid, response.axon.hotkey)

            score = self.scorer.calculate_score(
                network,
                response_time,
                start_block_height,
                last_block_height,
                self.block_height_cache[network],
                self.metadata.network_distribution
            )

            return score
        except Exception as e:
            bt.logging.error(f"Error occurred during cross-validation: {traceback.format_exc()}")
            return None

    async def forward(self):
        uids = next(self.uid_batch_generator, None)
        if uids is None:
            self.uid_batch_generator = get_uids_batch(self, self.config.neuron.sample_size)
            uids = next(self.uid_batch_generator, None)

        axons = [self.metagraph.axons[uid] for uid in uids]
        
        responses = self.dendrite.query(
            axons,
            Discovery(),
            deserialize=True,
            timeout = self.validator_config.discovery_timeout,
        )

        rewards = [
            self.get_reward(response, uid) for response, uid in zip(responses, uids)
        ]
        # Remove None reward as they represent timeout cross validation
        filtered_data = [(reward, uid) for reward, uid in zip(rewards, uids) if reward is not None]

        if filtered_data:
            rewards, uids = zip(*filtered_data)

            rewards = torch.FloatTensor(rewards)
            self.update_scores(rewards, uids)
        else: 
            bt.logging.info('Skipping update_scores() as no responses were valid')

    def sync_validator(self):
        self.metadata = Metadata.build(self.metagraph, self.config)
        self.validator_config = ValidatorConfig().load_and_get_config_values()
        self.scorer = Scorer(self.validator_config)

        self.networks = self.validator_config.get_networks()
        self.block_height_cache = {network: self.nodes[network].get_current_block_height() for network in self.networks}


    def resync_metagraph(self):
        super(Validator, self).resync_metagraph()
        self.sync_validator()

    def send_metadata(self):
        store_validator_metadata(self.config, self.wallet, self.uid)


if __name__ == "__main__":
    from dotenv import load_dotenv
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    load_dotenv()

    with Validator() as validator:
        while True:
            bt.logging.info("Validator running")
            time.sleep(bt.__blocktime__*10)


