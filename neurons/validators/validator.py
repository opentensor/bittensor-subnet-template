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

import os
import time
from random import sample

import torch
import argparse
import traceback
import bittensor as bt
from insights import protocol
from insights.protocol import MinerDiscoveryOutput
from neurons.external_api.blockchair_api import BlockchairAPIError
from neurons.validators.discovery import BlockchainAPIFacade
from neurons.validators.miner_registry import MinerRegistryManager
from neurons.validators.scoring import build_miner_distribution, calculate_score

SCORES_FILE = "scores.pt"


def get_scores_from_file(metagraph):
    try:
        scores = torch.load(SCORES_FILE)
        bt.logging.info(f"Loaded scores from save file: {scores}")
    except Exception as e:
        scores = torch.zeros_like(metagraph.S, dtype=torch.float32)
        bt.logging.info(f"Initialized all scores to 0")
    return scores


def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--alpha", default=0.9, type=float, help="The weight moving average scoring.py."
    )
    parser.add_argument(
        "--blockchair_api_key",
        default="BITCOIN",
        help="Blockchair api key.",
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
    scores = get_scores_from_file(metagraph)
    scores = scores * (metagraph.total_stake < 1.024e3) # all nodes with more than 1e3 total stake are set to 0 (sets validators weights to 0)
    scores = scores * torch.Tensor([metagraph.neurons[uid].axon_info.ip != '0.0.0.0' for uid in metagraph.uids]) # set all nodes without ips set to 0
    bt.logging.info(f"Initial scores: {scores}")

    bt.logging.info("Starting validator loop.")
    step = 0
    total_dendrites_per_query = 25
    minimum_dendrites_per_query = 3

    blockchain_api_facade = BlockchainAPIFacade(config.blockchair_api_key)

    while True:
        # Per 10 blocks, sync the subtensor state with the blockchain.
        if step % 5 == 0:
            metagraph.sync(subtensor = subtensor)
            bt.logging.info(f"🔄 Syncing metagraph with subtensor.")

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
        bt.logging.info(f"queryable_uids:{queryable_uids}")

        # Remove the weights of miners that are not queryable.
        queryable_uids = queryable_uids * torch.Tensor([metagraph.neurons[uid].axon_info.ip != '0.0.0.0' for uid in uids])
        active_miners = torch.sum(queryable_uids)
        dendrites_per_query = total_dendrites_per_query

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
        bt.logging.info(f"filtered_uids:{filtered_uids}")
        dendrites_to_query = sample( filtered_uids, min( dendrites_per_query, len(filtered_uids) ) )
        bt.logging.info(f"dendrites_to_query:{dendrites_to_query}")


        try:
            # Filter metagraph.axons by indices saved in dendrites_to_query list
            filtered_axons = [metagraph.axons[i] for i in dendrites_to_query]
            bt.logging.info(f"filtered_axons: {filtered_axons}")

            verification_data = blockchain_api_facade.get_verification_data()
            responses = dendrite.query(
                filtered_axons,
                protocol.MinerDiscovery(random_block_height=verification_data),
                deserialize=True,
                timeout = 60,
            )

            bt.logging.info(f"Received responses: {responses}")

            # filter out None responses
            responses = list(filter(lambda x: x is not None, responses))

            # Get miner distribution
            miner_distribution = build_miner_distribution(responses)

            for index, response in enumerate(responses):
                # Vars
                output: MinerDiscoveryOutput = response
                network = output.metadata.network
                model_type = output.metadata.model_type
                data_sample_block_height = output.block_height
                data_sample = output.data_sample
                axon_ip = metagraph.axons[index].ip
                hot_key = metagraph.axons[index].hotkey
                response_time = response.dendrite.process_time

                last_block_height = verification_data[network]['last_block_height']

                data_sample_is_valid = blockchain_api_facade.verify_data_sample(
                    network=network,
                    block_height=data_sample_block_height,
                    input_result=data_sample,
                )

                score = calculate_score(
                    response,
                    verification_data[network]['last_block_height'],
                    network,
                    miner_distribution,
                    data_sample_is_valid,
                )

                bt.logging.info(f"Last block height: {last_block_height}")
                bt.logging.info(f"Data sample block height: {data_sample_block_height}")
                bt.logging.info(f"Data sample is valid: {data_sample_is_valid}")

                scores[index] = (
                    config.alpha * scores[index] + (1 - config.alpha) * score
                )

                MinerRegistryManager().store_miner_metadata(
                    ip_address=axon_ip,
                    hot_key=hot_key,
                    network=network,
                    model_type=model_type,
                    response_time=response_time,
                    score=scores[index],
                )

            ## While loop end
            bt.logging.info(f"Scoring response: {scores}")

            if (step + 1) % 10 == 0:
                weights = torch.nn.functional.normalize(scores, p=1.0, dim=0)
                bt.logging.info(f"Setting weights: {weights}")
                result = subtensor.set_weights(
                    netuid=config.netuid,
                    wallet=wallet,
                    uids=metagraph.uids,
                    weights=weights,
                    wait_for_inclusion=True,
                )
                if result:
                    bt.logging.success("Successfully set weights.")
                    time.sleep(bt.__blocktime__ * 101)
                else:
                    bt.logging.error("Failed to set weights.")

            step += 1
            metagraph = subtensor.metagraph(config.netuid)

            # storing scores to file
            torch.save(scores, SCORES_FILE)
            bt.logging.info(f"Saved weights to \"{SCORES_FILE}\"")
            time.sleep(bt.__blocktime__)

        except BlockchairAPIError as e:
            bt.logging.error(e)
            traceback.print_exc()
            time.sleep(bt.__blocktime__ * 12)

        except RuntimeError as e:
            bt.logging.error(e)
            traceback.print_exc()

        except KeyboardInterrupt:
            bt.logging.success("Keyboard interrupt detected. Exiting validator.")
            exit()


if __name__ == "__main__":
    config = get_config()
    """
    python miner.py 
    --netuid 1  # The subnet id you want to connect to
    --subtensor.network finney  # blockchain endpoint you want to connect
    --wallet.name <your miner wallet> # name of your wallet
    --wallet.hotkey <your miner hotkey> # hotkey name of your wallet
    
    config.subtensor.chain_endpoint = "ws://127.0.0.1:9946"
    config.subtensor.network = "finney"
    config.wallet.hotkey = 'default'
    config.wallet.name = 'validator'
    config.netuid = 1
    config.blockchair_api_key = "A___mw5wNljHQ4n0UAdM5Ivotp0Bsi93"
      
    config.subtensor.chain_endpoint = "ws://127.0.0.1:9946"
    
    
    """

    config.subtensor.network = "finney"
    config.wallet.hotkey = 'default'
    config.wallet.name = 'validator'
    config.netuid = 15
    config.blockchair_api_key = "A___mw5wNljHQ4n0UAdM5Ivotp0Bsi93"

    main(config)
