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
from insights.protocol import MinerDiscoveryOutput
from neurons.nodes.nodes import get_node
from neurons.validators.miner_registry import MinerRegistryManager
from neurons.validators.scoring import calculate_score, verify_data_sample, \
    BLOCKCHAIN_IMPORTANCE


def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--alpha", default=0.9, type=float, help="The weight moving average scoring.py."
    )

    parser.add_argument(
        "--bitcoin_cheat_factor_sample_size",
        default=256,
        help="Bitcoin sample size used for calculating cheat factor.",
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
                timeout = 60,
            )

            miner_distribution = MinerRegistryManager().get_miner_distribution(BLOCKCHAIN_IMPORTANCE.keys())

            # Cache dictionary
            block_height_cache = {}

            for index, response in enumerate(responses):
                if response.output is None:
                    bt.logging.debug(f"Skipping response")
                    continue

                # Vars
                output: MinerDiscoveryOutput = response.output
                network = output.metadata.network
                model_type = output.metadata.model_type

                start_block_height = output.start_block_height
                last_block_height = output.block_height

                data_samples = output.data_samples
                axon_ip = response.axon.ip
                hot_key = response.axon.hotkey
                response_time = response.axon.process_time

                bt.logging.info(f"🔄 Processing response from {axon_ip} / {hot_key}")

                node = get_node(network)
                data_samples_are_valid = validate_all_data_samples(node, network, data_samples)

                if len(data_samples) < 10:
                    data_samples_are_valid = False

                bitcoin_cheat_factor_sample_size = int(config.bitcoin_cheat_factor_sample_size)
                cheat_factor = MinerRegistryManager().calculate_cheat_factor(hot_key=hot_key, network=network, model_type=model_type, sample_size=bitcoin_cheat_factor_sample_size)

                if network not in block_height_cache:
                    block_height_cache[network] = node.get_current_block_height()


                score = calculate_score(
                    network,
                    response_time,
                    start_block_height,
                    last_block_height,
                    block_height_cache[network],
                    miner_distribution,
                    data_samples_are_valid,
                    cheat_factor
                )

                scores[dendrites_to_query[index]] = config.alpha * scores[dendrites_to_query[index]] + (1 - config.alpha) * score

                MinerRegistryManager().store_miner_metadata(
                    ip_address=axon_ip,
                    hot_key=hot_key,
                    network=network,
                    model_type=model_type,
                    response_time=response_time,
                    score=scores[dendrites_to_query[index]],
                )

                MinerRegistryManager().store_miner_block_height(
                    hot_key=hot_key,
                    network=network,
                    model_type=model_type,
                    block_height=last_block_height,
                )

            current_block = subtensor.block
            bt.logging.info(f"Block difference is {current_block - last_updated_block}.")
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
            bt.logging.info(f"Saved weights to \"{scores_file}\"")
            time.sleep(bt.__blocktime__ * 10)

        except RuntimeError as e:
            bt.logging.error(e)
            traceback.print_exc()

        except KeyboardInterrupt:
            bt.logging.success("Keyboard interrupt detected. Exiting validator.")
            exit()

def validate_data_sample(node, network, data_sample):
    block_data = node.get_block_by_height(data_sample['block_height'])
    return verify_data_sample(
        network=network,
        input_result=data_sample,
        block_data=block_data
    )

def validate_all_data_samples(node, network, data_samples):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Creating a future for each data sample validation
        futures = [executor.submit(validate_data_sample, node, network, sample) for sample in data_samples]

        for future in concurrent.futures.as_completed(futures):
            if not future.result():
                return False  # If any data sample is invalid, return False immediately
    return True  # All data samples are valid


if __name__ == "__main__":
    config = get_config()

    main(config)