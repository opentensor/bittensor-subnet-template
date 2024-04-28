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

import asyncio
import torch
import bittensor as bt
import os
import yaml

from collections import Counter
from sklearn.cluster import KMeans
import numpy as np

import insights
from insights import protocol
from insights.protocol import Discovery, DiscoveryOutput, MAX_MINER_INSTANCE, QUERY_TYPE_SEARCH

import threading
from insights.protocol import Discovery, DiscoveryOutput, MAX_MINER_INSTANCE, NETWORK_BITCOIN, MODEL_TYPE_BALANCE_TRACKING
from neurons.remote_config import ValidatorConfig
from neurons.nodes.factory import NodeFactory
from neurons.storage import store_validator_metadata
from neurons.validators.scoring import Scorer
from neurons.validators.uptime import MinerUptimeManager
from neurons.validators.challenge_factory.balance_challenge_factory import BalanceChallengeFactory
from neurons.validators.utils.metadata import Metadata
from neurons.validators.utils.ping import ping
from neurons.validators.utils.synapse import is_discovery_response_valid
from concurrent.futures import ThreadPoolExecutor
from neurons.validators.utils.uids import get_uids_batch
from template.base.validator import BaseValidatorNeuron

from insights.api.insight_api import APIServer

class Validator(BaseValidatorNeuron):

    @staticmethod
    def get_config():       
        
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--alpha", default=0.9, type=float, help="The weight moving average scoring.py."
        )

        parser.add_argument("--netuid", type=int, default=15, help="The chain subnet uid.")
        parser.add_argument("--dev", action=argparse.BooleanOptionalAction)
        # For API configuration
        # Subnet Validator and validator API        
        # You can invoke the API while instantiating the validator.
        # To run API, it's needed to set `enable_api`, `api_port`, `top_rate`, `timeout`, `user_query_moving_average_alpha` additionally.
        
        parser.add_argument("--enable_api", type=bool, default=False, help="Decide whether to launch api or not.")
        parser.add_argument("--api_port", type=int, default=8001, help="API endpoint port.")
        parser.add_argument("--timeout", type=int, default=40, help="Timeout.")
        parser.add_argument("--top_rate", type=float, default=1, help="Best selection percentage")
        parser.add_argument("--user_query_moving_average_alpha", type=float, default=0.0001, help="Moving average alpha for scoring user query miners.")

        bt.subtensor.add_args(parser)
        bt.logging.add_args(parser)
        bt.wallet.add_args(parser)

        config = bt.config(parser)
        config.db_connection_string = os.environ.get('DB_CONNECTION_STRING', '')

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
        self.challenge_factory = {
            NETWORK_BITCOIN: {
                MODEL_TYPE_BALANCE_TRACKING: BalanceChallengeFactory(self.nodes[NETWORK_BITCOIN])
            }
        }
        super(Validator, self).__init__(config)
        self.sync_validator()
        self.uid_batch_generator = get_uids_batch(self, self.config.neuron.sample_size)
        self.miner_uptime_manager = MinerUptimeManager(db_url=self.config.db_connection_string)
        if config.enable_api:
            self.api_server = APIServer(
                config=self.config,
                wallet=self.wallet,
                subtensor=self.subtensor,
                metagraph=self.metagraph,
                scores=self.scores
            )


    def cross_validate(self, axon, node, challenge_factory, start_block_height, last_block_height, balance_model_last_block):
        try:
            # first, validate funds flow model response
            challenge, expected_response = node.create_challenge(start_block_height, last_block_height)
            
            response = self.dendrite.query(
                axon,
                challenge,
                deserialize=False,
                timeout=self.validator_config.challenge_timeout,
            )

            response_time = response.dendrite.process_time
            bt.logging.info(f"Cross validation response time: {response_time}, status_code: {response.axon.status_code}")

            if response is None or response.output is None:
                bt.logging.debug("Cross validation failed")
                return False, 128

            # if the miner's response is different from the expected response and validation failed
            if not response.output == expected_response and not node.validate_challenge_response_output(challenge, response.output):
                bt.logging.debug("Cross validation failed")
                return False, response_time
            
            # second, validate balance model response
            challenge, expected_response = challenge_factory[MODEL_TYPE_BALANCE_TRACKING].get_challenge(balance_model_last_block)
            
            response = self.dendrite.query(
                axon,
                challenge,
                deserialize=False,
                timeout = self.validator_config.challenge_timeout,
            )
            
            if response is None or response.output is None:
                bt.logging.debug("Cross validation failed")
                return False, 128
            
            response_time += response.dendrite.process_time
            
            if not str(response.output) == str(expected_response):
                bt.logging.debug("Cross validation failed")
                return False, response_time
            
            return True, response_time
        except Exception as e:
            bt.logging.error(f"Cross validation error occurred: {e}")
            return None, None

    def is_miner_metadata_valid(self, response: Discovery):
        hotkey = response.axon.hotkey
        ip = response.axon.ip    
        hotkey_meta = self.metadata.get_metadata_for_hotkey(hotkey)

        if not (hotkey_meta and hotkey_meta['network']):
            bt.logging.info(f'Validation Failed: hotkey={hotkey} unable to retrieve miner metadata')
            return False

        ip_count = self.metadata.ip_distribution.get(ip, 0)
        coldkey_count = self.metadata.coldkey_distribution.get(hotkey, 0)

        bt.logging.info(f"🔄 Processing response for {hotkey}@{ip}")
        if ip_count > MAX_MINER_INSTANCE:
            bt.logging.info(f'Validation Failed: hotkey={hotkey} has {ip_count} ip')
            return False
        if coldkey_count > MAX_MINER_INSTANCE:
            bt.logging.info(f'Validation Failed: Coldkey of hotkey={hotkey} has {coldkey_count} hotkeys')
            return False
        
        bt.logging.info(f'hotkey={hotkey} has {ip_count} ip, {coldkey_count} hotkeys for its coldkey')

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

    def is_response_valid(self, response: Discovery):
        if not self.is_response_status_code_valid(response):
            return False
        if not is_discovery_response_valid(response):
            return False
        if not self.is_miner_metadata_valid(response):
            return False
        return True

    def get_reward(self, response: Discovery, uid: int, benchmarks_result):
        try:
            uid_value = uid.item() if uid.numel() == 1 else int(uid.numpy())
            self.miner_uptime_manager.try_update_miner(uid_value, response.axon.hotkey)

            if not self.is_response_status_code_valid(response):
                score = self.metagraph.T[uid]/2
                self.miner_uptime_manager.down(uid_value, response.axon.hotkey)
                bt.logging.debug(f'Discovery Response error: hotkey={response.axon.hotkey}, setting score to {score}')
                return score
            if not is_discovery_response_valid(response):
                self.miner_uptime_manager.down(uid_value, response.axon.hotkey)
                bt.logging.debug(f'Discovery Response invalid {response}')
                return 0
            if not self.is_miner_metadata_valid(response):
                self.miner_uptime_manager.down(uid_value, response.axon.hotkey)
                return 0

            output: DiscoveryOutput = response.output
            network = output.metadata.network
            start_block_height = output.start_block_height
            last_block_height = output.block_height
            balance_model_last_block = output.balance_model_last_block
            hotkey = response.axon.hotkey

            if self.block_height_cache[network] - last_block_height < 6:
                bt.logging.debug(f"Indexed block cannot be higher than current_block - 6")
                return 0

            result, average_ping_time = ping(response.axon.ip, response.axon.port, attempts=10)
            if not result:
                bt.logging.info(f"Ping: {hotkey=} Test failed, setting score to avg_ping_time=0, continuing..")
            else:
                bt.logging.info(f"Ping: {hotkey=} average ping time: {average_ping_time} seconds")

            cross_validation_result = self.cross_validate(response.axon, self.nodes[network], self.challenge_factory[network], start_block_height, last_block_height, balance_model_last_block)

            if cross_validation_result is None:
                self.miner_uptime_manager.down(uid_value, response.axon.hotkey)
                bt.logging.debug(f"Cross-Validation: {hotkey=} Timeout skipping response")
                return None
            if not cross_validation_result:
                self.miner_uptime_manager.down(uid_value, response.axon.hotkey)
                bt.logging.info(f"Cross-Validation: {hotkey=} Test failed")
                return 0

            cross_validation_result_is_valid, _ = cross_validation_result
            if cross_validation_result_is_valid is False:
                self.miner_uptime_manager.down(uid_value, response.axon.hotkey)
                bt.logging.info(f"Cross-Validation: {hotkey=} Test failed")
                return 0

            bt.logging.info(f"Cross-Validation: {hotkey=} Test passed")

            benchmark_result = benchmarks_result.get(uid_value)
            if benchmark_result is None:
                self.miner_uptime_manager.down(uid_value, response.axon.hotkey)
                bt.logging.info(f"Benchmark-Validation: {hotkey=} Timeout skipping response")
                return

            response_time, benchmark_is_valid = benchmark_result
            if not benchmark_is_valid:
                self.miner_uptime_manager.down(uid_value, response.axon.hotkey)
                bt.logging.info(f"Benchmark-Validation: {hotkey=} Test failed")
                return 0

            bt.logging.info(f"Benchmark-Validation: {hotkey=} Test passed")

            response_time = response_time - average_ping_time

            self.miner_uptime_manager.up(uid_value, response.axon.hotkey)
            uptime_score = self.miner_uptime_manager.get_uptime_scores(uid_value, response.axon.hotkey)

            score = self.scorer.calculate_score(
                network,
                response_time,
                start_block_height,
                last_block_height,
                self.block_height_cache[network],
                self.metadata.network_distribution,
                uptime_score['average']
            )

            return score
        except Exception as e:
            bt.logging.error(f"Error occurred during cross-validation: {traceback.format_exc()}")
            return None

    async def forward(self):
        self.block_height_cache = {network: self.nodes[network].get_current_block_height() for network in self.networks}
        # Update the subtensor, metagraph, scores of api_server as the one of validator is updated.
        self.api_server.subtensor = self.subtensor
        self.api_server.metagraph = self.metagraph
        self.api_server.scores = self.scores
        uids = next(self.uid_batch_generator, None)
        if uids is None:
            self.uid_batch_generator = get_uids_batch(self, self.config.neuron.sample_size)
            uids = next(self.uid_batch_generator, None)

        axons = [self.metagraph.axons[uid] for uid in uids]

        responses = self.dendrite.query(
            axons,
            Discovery(),
            deserialize=True,
            timeout=self.validator_config.discovery_timeout,
        )

        responses_to_benchmark = [(response, uid) for response, uid in zip(responses, uids) if self.is_response_valid(response)]
        benchmarks_result = self.run_benchmarks(responses_to_benchmark)

        rewards = [
            self.get_reward(response, uid, benchmarks_result) for response, uid in zip(responses, uids)
        ]

        filtered_data = [(reward, uid) for reward, uid in zip(rewards, uids) if reward is not None]

        if filtered_data:
            rewards, uids = zip(*filtered_data)

            rewards = torch.FloatTensor(rewards)
            self.update_scores(rewards, uids)
        else:  
            bt.logging.info('Skipping update_scores() as no responses were valid')

    def run_benchmarks(self, filtered_responses):
        grouped_responses = self.group_responses(filtered_responses)

        results = {}
        for network, main_group in grouped_responses.items():
            for label, group in main_group.items():
                import textwrap
                benchmark_query_script = textwrap.dedent(self.validator_config.get_benchmark_query_script(network))
                benchmark_query_script_vars = {
                    'network': network,
                    'start_block': group['common_start'],
                    'end_block': group['common_end']
                }

                exec(benchmark_query_script, benchmark_query_script_vars)
                benchmark_query = benchmark_query_script_vars['query']

                benchmark_results = self.execute_benchmarks(group, benchmark_query)

                if len(benchmark_results) > 0:
                    try:
                        filtered_result = [response_output for uid_value, response_time, response_output in benchmark_results]
                        most_common_result, _ = Counter(filtered_result).most_common(1)[0]
                        for uid_value, response_time, result in benchmark_results:
                            results[uid_value] = (response_time, result == most_common_result)
                    except Exception as e:
                        bt.logging.error(f"Error occurred during benchmarking: {traceback.format_exc()}")

            return results

    def run_benchmark(self, response: Discovery, uid, benchmark_query: str = "RETURN 1"):
        try:
            uid_value = uid.item() if uid.numel() == 1 else int(uid.numpy())
            output: DiscoveryOutput = response.output

            benchmark_response = self.dendrite.query(
                response.axon,
                protocol.Benchmark(
                    network=output.metadata.network,
                    query=benchmark_query
                ),
                deserialize=False,
                timeout=self.validator_config.benchmark_timeout,
            )

            if benchmark_response is None or benchmark_response.output is None:
                bt.logging.debug(f"Benchmark validation failed for {response.axon.hotkey}")
                return None, None, None

            response_time = benchmark_response.dendrite.process_time

            bt.logging.info(f"Benchmark validation passed for {response.axon.hotkey} with response time {response_time}, output: {benchmark_response.output}, uid: {uid_value}")
            return uid_value, response_time, benchmark_response.output
        except Exception as e:
            bt.logging.error(f"Error occurred during benchmarking {response.axon.hotkey}: {traceback.format_exc()}")
            return None, None, None

    def execute_benchmarks(self, group, benchmark_query):

        results = []
        for response, uid in group['responses']:
            bt.logging.info(f"Running benchmark for {response.axon.hotkey}")
            result = self.run_benchmark(response, uid, benchmark_query)
            results.append(result)

        filtered_run_results = []
        for uid_value, response_time, response_output in results:
            if response_output is not None:
                filtered_run_results.append((uid_value, response_time, response_output))

        return filtered_run_results

    def group_responses(self, responses) -> dict:
        network_grouped_responses = {}

        for resp, uid in responses:
            net = resp.output.metadata.network
            if net not in network_grouped_responses:
                network_grouped_responses[net] = []
            network_grouped_responses[net].append((resp, uid))

        new_groups = {}
        for network in network_grouped_responses:
            data = np.array([(resp.output.start_block_height, resp.output.block_height) for (resp, uid) in network_grouped_responses[network]])
            k = self.validator_config.benchmark_cluster_size

            kmeans = KMeans(n_clusters=k, random_state=0).fit(data)
            labels = kmeans.labels_

            grouped_responses = {}
            for label, response in zip(labels, network_grouped_responses[network]):
                if label not in grouped_responses:
                    grouped_responses[label] = []
                grouped_responses[label].append(response)

            # we find here common starting and ending block height for each group
            for label, group in grouped_responses.items():
                min_start = min(resp.output.start_block_height for (resp, uid) in group)
                min_end = min(resp.output.block_height for (resp, uid) in group)
                if network not in new_groups:
                    new_groups[network] = {}
                new_groups[network][label] = {
                    'common_start': min_start,
                    'common_end': min_end,
                    'responses': group,
                }

        return new_groups

    def sync_validator(self):
        self.metadata = Metadata.build(self.metagraph, self.config)
        self.validator_config = ValidatorConfig().load_and_get_config_values()
        self.scorer = Scorer(self.validator_config)

        self.networks = self.validator_config.get_networks()

        if self.validator_config.version_update is True and self.validator_config.version != insights.__version__:
            exit(3)

    def resync_metagraph(self):
        super(Validator, self).resync_metagraph()
        self.sync_validator()

    def send_metadata(self):
        store_validator_metadata(self)

def run_api_server(api_server):
    api_server.start()

if __name__ == "__main__":
    from dotenv import load_dotenv
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    load_dotenv()

    with Validator() as validator:
        if validator.config.enable_api:
            if not validator.api_server:
                validator.api_server = APIServer(
                    config=validator.config,
                    wallet=validator.wallet,
                    subtensor=validator.subtensor,
                    metagraph=validator.metagraph,
                    scores=validator.scores
                )
            api_server_thread = threading.Thread(target=run_api_server, args=(validator.api_server,))
            api_server_thread.start()

        while True:
            bt.logging.info("Validator running")
            time.sleep(bt.__blocktime__*10)


