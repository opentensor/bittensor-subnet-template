# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2023 aph5nt
import concurrent
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
import torch
import argparse
import traceback
import bittensor as bt
from random import sample
from insights import protocol
from insights.protocol import MinerDiscoveryOutput, NETWORK_BITCOIN, MinerRandomBlockCheckOutput
from neurons import VERSION
from neurons.nodes.nodes import get_node
from neurons.remote_config import ValidatorConfig
from neurons.validators.miner_registry import MinerRegistryManager
from neurons.validators.scoring import Scorer

def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--alpha", default=0.9, type=float, help="The weight moving average scoring.py."
    )

    parser.add_argument("--netuid", type=int, default=15, help="The chain subnet uid.")

    bt.subtensor.add_args(parser)
    bt.logging.add_args(parser)
    bt.wallet.add_args(parser)

    config = bt.config(parser)
    config.full_path = os.path.expanduser(
        "{}/{}/{}/netuid{}/{}".format(
            config.logging.logging_dir,
            config.wallet.name,
            config.wallet.hotkey,
            config.netuid,
            "validator",
        )
    )

    if not os.path.exists(config.full_path):
        os.makedirs(config.full_path, exist_ok=True)
    return config


def main(config):
    bt.logging.info(f"Running validator with config: {config}")
    bt.logging.info("Setting up bittensor objects.")

    bt.logging(config=config, logging_dir=config.full_path)
    wallet = bt.wallet(config=config)
    subtensor = bt.subtensor(config=config)
    dendrite = bt.dendrite(wallet=wallet)
    metagraph = subtensor.metagraph(config.netuid)
    metagraph.sync(subtensor = subtensor)

    bt.logging.info(f"Wallet: {wallet}")
    bt.logging.info(f"Subtensor: {subtensor}")
    bt.logging.info(f"Dendrite: {dendrite}")
    bt.logging.info(f"Metagraph: {metagraph}")

    if wallet.hotkey.ss58_address not in metagraph.hotkeys:
        bt.logging.error(
            f"\nYour validator: {wallet} if not registered to chain connection: {subtensor} \nRun btcli register and try again."
        )
        exit()

    my_subnet_uid = metagraph.hotkeys.index(wallet.hotkey.ss58_address)
    bt.logging.info(f"Running validator on uid: {my_subnet_uid}")
    bt.logging.info("Building validation weights.")

    # Restore weights, or initialize weights for each miner to 0.
    scores_file = "scores.pt"
    try:
        scores = torch.load(scores_file)
        bt.logging.info(f"Loaded scores from save file: {scores}")
    except:
        scores = torch.zeros_like(metagraph.S, dtype=torch.float32)
        bt.logging.info(f"Initialized all scores to 0")


    scores = scores * (metagraph.total_stake < 1.024e3) # all nodes with more than 1e3 total stake are set to 0 (sets validators weights to 0)
    scores = scores * torch.Tensor([metagraph.neurons[uid].axon_info.ip != '0.0.0.0' for uid in metagraph.uids]) # set all nodes without ips set to 0
    bt.logging.info(f"Initial scores: {scores}")

    total_dendrites_per_query = 25
    minimum_dendrites_per_query = 3
    curr_block = subtensor.block
    last_updated_block = curr_block - (curr_block % 100)
    last_reset_weights_block = curr_block

    bt.logging.debug(f"curr_block: {curr_block}, last_updated_block: {last_updated_block}, last_reset_weights_block: {last_reset_weights_block}")

    """ Building dependencies. """
    validator_config = ValidatorConfig()
    validator_config.load_and_get_config_values()
    miner_registry_manager = MinerRegistryManager()
    scorer = Scorer(validator_config)

    bt.logging.info("Starting validator loop.")
    step = 0

    # Main loop
    while True:
        # Per 10 blocks, sync the subtensor state with the blockchain.
        if step % 5 == 0:
            bt.logging.info(f"🔄 Syncing metagraph with subtensor.")
            metagraph.sync(subtensor = subtensor)

        # If there are more uids than scores, add more weights.
        # Get the uids of all miners in the network.
        uids = metagraph.uids.tolist()
        if len(uids) > len(scores):
            bt.logging.trace("Adding more weights")
            size_difference = len(uids) - len(scores)
            new_scores = torch.zeros(size_difference, dtype=torch.float32)
            scores = torch.cat((scores, new_scores))
            del new_scores

        # If there are less uids than scores, remove some weights.
        queryable_uids = (metagraph.total_stake < 1.024e3)
        # Remove the weights of miners that are not queryable.
        queryable_uids = queryable_uids * torch.Tensor([metagraph.neurons[uid].axon_info.ip != '0.0.0.0' for uid in uids])
        active_miners = torch.sum(queryable_uids)

        # if there are no active miners, set active_miners to 1
        if active_miners == 0:
            active_miners = 1
        # if there are less than dendrites_per_query * 3 active miners, set dendrites_per_query to active_miners / 3
        if active_miners < total_dendrites_per_query * 3:
            dendrites_per_query = int(active_miners / 3)
        else:
            dendrites_per_query = total_dendrites_per_query

        # less than 3 set to 3
        if dendrites_per_query < minimum_dendrites_per_query:
            dendrites_per_query = minimum_dendrites_per_query

        # zip uids and queryable_uids, filter only the uids that are queryable, unzip, and get the uids
        zipped_uids = list(zip(uids, queryable_uids))
        filtered_uids = list(zip(*filter(lambda x: x[1], zipped_uids)))[0]
        dendrites_to_query = sample( filtered_uids, min( dendrites_per_query, len(filtered_uids) ) )

        try:
            # Filter metagraph.axons by indices saved in dendrites_to_query list
            filtered_axons = [metagraph.axons[i] for i in dendrites_to_query]
            bt.logging.info(f"filtered axons: {filtered_axons}")

            responses = dendrite.query(
                filtered_axons,
                protocol.MinerDiscovery(),
                deserialize=True,
                timeout = validator_config.discovery_timeout,
            )

            # Cache dictionary
            block_height_cache = {}

            for index, response in enumerate(responses):
                if response.output is None:
                    bt.logging.debug(f"Skipping response {response}")
                    continue

                try:
                    # Vars
                    output: MinerDiscoveryOutput = response.output
                    network = output.metadata.network
                    model_type = output.metadata.model_type
                    start_block_height = output.start_block_height
                    last_block_height = output.block_height
                    data_samples = output.data_samples
                    axon_ip = response.axon.ip
                    hot_key = response.axon.hotkey
                    run_id = response.output.run_id
                    response_time = response.dendrite.process_time

                    if response.output.version < VERSION and validator_config.grace_period:
                        score = 0.1
                        scores[dendrites_to_query[index]] = config.alpha * scores[dendrites_to_query[index]] + (1 - config.alpha) * score
                        bt.logging.info(f"Miner is running an old version. Grace period is enabled. Score set to {score}.")
                        continue

                    elif response.output.version != VERSION:
                        score = 0
                        scores[dendrites_to_query[index]] = config.alpha * scores[dendrites_to_query[index]] + (1 - config.alpha) * score
                        bt.logging.info(f"Miner is running an old version. Grace period is disabled. Score set to {score}")
                        continue

                    bt.logging.info(f"🔄 Processing response for {hot_key}@ {axon_ip}")

                    node = get_node(network)
                    data_samples_are_valid = validate_all_data_samples(node, network, data_samples)

                    if len(data_samples) < 10:
                        data_samples_are_valid = False

                    if network not in block_height_cache:
                        block_height_cache[network] = node.get_current_block_height()

                    miner_distribution = miner_registry_manager.get_miner_distribution(validator_config.get_network_importance_keys())
                    multiple_ips = miner_registry_manager.detect_multiple_ip_usage(hot_key)
                    multiple_run_ids = miner_registry_manager.detect_multiple_run_id(run_id)

                    score = scorer.calculate_score(
                        network,
                        response_time,
                        start_block_height,
                        last_block_height,
                        block_height_cache[network],
                        data_samples_are_valid,
                        miner_distribution,
                        multiple_ips,
                        multiple_run_ids
                    )

                    blocks_to_check = sample(range(start_block_height, last_block_height + 1), 10)
                    random_block_response = dendrite.query(
                        [response.axon],
                        protocol.MinerRandomBlockCheck(blocks_to_check=blocks_to_check),
                        deserialize=True,
                        timeout = validator_config.discovery_timeout,
                    )

                    # take the first response
                    random_block_response = random_block_response[0]
                    if response.output is None:
                        bt.logging.debug(f"Skipping response {response}")
                        continue

                    bt.logging.info(f"🔄 Processing random cross-check response for {hot_key}")
                    blocks_to_check_output: MinerRandomBlockCheckOutput = random_block_response.output
                    if blocks_to_check_output is None:
                        bt.logging.debug(f"Timeout for {hot_key}, skipping response")
                        continue

                    blocks_to_check_data_samples_are_valid = validate_all_data_samples(node, network, blocks_to_check_output.data_samples)
                    if not blocks_to_check_data_samples_are_valid:
                        score = 0
                        bt.logging.info(f"🔄 Punishing {hot_key} for invalid data samples.")
                    else:
                        bt.logging.info(f"🔄 Rewarding {hot_key} for valid data samples.")

                    scores[dendrites_to_query[index]] = config.alpha * scores[dendrites_to_query[index]] + (1 - config.alpha) * score

                    miner_registry_manager.store_miner_metadata(
                        ip_address=axon_ip,
                        hot_key=hot_key,
                        network=network,
                        model_type=model_type,
                        response_time=response_time,
                        score=scores[dendrites_to_query[index]],
                        run_id=run_id
                    )
                except Exception as e:
                    bt.logging.error(e)
                    traceback.print_exc()

            current_block = subtensor.block

            if current_block - last_updated_block > 100:
                weights = scores / torch.sum(scores)
                bt.logging.info(f"Setting weights: {weights}")
                # Miners with higher scores (or weights) receive a larger share of TAO rewards on this subnet.
                (processed_uids,  processed_weights) = bt.utils.weight_utils.process_weights_for_netuid(
                    uids=metagraph.uids,
                    weights=weights,
                    netuid=config.netuid,
                    subtensor=subtensor
                )
                bt.logging.info(f"Processed weights: {processed_weights}")
                bt.logging.info(f"Processed uids: {processed_uids}")
                result = subtensor.set_weights(
                    netuid = config.netuid, # Subnet to set weights on.
                    wallet = wallet, # Wallet to sign set weights using hotkey.
                    uids = processed_uids, # Uids of the miners to set weights for.
                    weights = processed_weights, # Weights to set for the miners.
                )
                last_updated_block = current_block
                if result: bt.logging.success('✅ Successfully set weights.')
                else: bt.logging.error('Failed to set weights.')

            bt.logging.info(f"Scoring response: {scores}")

            step += 1

            # Resync our local state with the latest state from the blockchain.
            metagraph = subtensor.metagraph(config.netuid)
            torch.save(scores, scores_file)
            validator_config.load_and_get_config_values()
            time.sleep(bt.__blocktime__ * 10)

        except RuntimeError as e:
            bt.logging.error(e)
            traceback.print_exc()

        except KeyboardInterrupt:
            bt.logging.success("Keyboard interrupt detected. Exiting validator.")
            exit()

        except Exception as e:
            bt.logging.error(e)
            traceback.print_exc()

def validate_data_sample(node, network, data_sample):
    block_data = node.get_block_by_height(data_sample['block_height'])
    return verify_data_sample(
        network=network,
        input_result=data_sample,
        block_data=block_data
    )

def verify_data_sample(network, input_result, block_data):
   if network == NETWORK_BITCOIN:
        block_height = int(input_result['block_height'])
        transactions = block_data["tx"]
        num_transactions = len(transactions)
        result = {
            "block_height": block_height,
            "transaction_count": num_transactions,
        }
        is_valid = result["transaction_count"] == input_result["transaction_count"]
        return is_valid
   else:
        return False

def validate_all_data_samples(node, network, data_samples):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Creating a future for each data sample validation
        futures = [executor.submit(validate_data_sample, node, network, sample) for sample in data_samples]

        for future in concurrent.futures.as_completed(futures):
            if not future.result():
                return False  # If any data sample is invalid, return False immediately
    return True  # All data samples are valid


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    config = get_config()

    # Check for an environment variable to enable local development
    if os.getenv("VALIDATOR_TEST_MODE") == "True":
        # Local development settings
        config.subtensor.network = 'test'
        config.wallet.hotkey = 'default'
        config.wallet.name = 'validator'
        config.netuid = 59

        # set environment variables
        os.environ['GRAPH_DB_URL'] = 'bolt://localhost:7687'
        os.environ['GRAPH_DB_USER'] = 'user'
        os.environ['GRAPH_DB_PASSWORD'] = 'pwd'

    main(config)