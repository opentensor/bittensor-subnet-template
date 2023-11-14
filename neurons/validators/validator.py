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
import torch
import argparse
import traceback
import bittensor as bt
from insights import protocol
from insights.protocol import MinerDiscovery
from neurons.validators.blockchair_api import BlockchairAPI
from neurons.validators.miner_data_sample import MinerDataSample
from neurons.validators.miner_registry import MinerRegistry


def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--alpha", default=0.9, type=float, help="The weight moving average scoring."
    )
    parser.add_argument(
        "--blockchain",
        default="BITCOIN",
        help="Set miner's supported blockchain network.",
    )

    parser.add_argument(
        "--blockchair_api_key",
        default="BITCOIN",
        help="Blockchair api key.",
    )

    parser.add_argument("--netuid", type=int, default=1, help="The chain subnet uid.")

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
    bt.logging(config=config, logging_dir=config.full_path)
    bt.logging.info(config)
    bt.logging.info("Setting up bittensor objects.")

    wallet = bt.wallet(config=config)
    bt.logging.info(f"Wallet: {wallet}")

    subtensor = bt.subtensor(config=config)
    bt.logging.info(f"Subtensor: {subtensor}")

    dendrite = bt.dendrite(wallet=wallet)
    bt.logging.info(f"Dendrite: {dendrite}")

    metagraph = subtensor.metagraph(config.netuid)
    bt.logging.info(f"Metagraph: {metagraph}")

    if wallet.hotkey.ss58_address not in metagraph.hotkeys:
        bt.logging.error(
            f"\nYour validator: {wallet} if not registered to chain connection: {subtensor} \nRun btcli register and try again."
        )
        exit()

    my_subnet_uid = metagraph.hotkeys.index(wallet.hotkey.ss58_address)
    bt.logging.info(f"Running validator on uid: {my_subnet_uid}")
    bt.logging.info("Building validation weights.")
    scores = torch.ones_like(metagraph.S, dtype=torch.float32)
    bt.logging.info(f"Weights: {scores}")

    bt.logging.info("Starting validator loop.")
    step = 0

    blochair_api = BlockchairAPI(config.blockchain, config.blockchair_api_key)

    while True:
        try:
            responses = dendrite.query(
                metagraph.axons,
                protocol.MinerDiscovery(),
                deserialize=True,
            )

            bt.logging.info(f"Received responses: {responses}")
            for index, response in enumerate(responses):
                synapse: MinerDiscovery = response

                MinerRegistry().store_miner_metadata(
                    ip_address=synapse.axon.ip,
                    hot_key=synapse.dendrite.hotkey,
                    network=synapse.output.metadata.network,
                    assets=synapse.output.metadata.assets,
                    model_type=synapse.output.metadata.model_type,
                )

                MinerDataSample().store_miner_data_sample(
                    hot_key=synapse.dendrite.hotkey,
                    network=synapse.output.metadata.network,
                    model_type=synapse.output.metadata.model_type,
                    data_sample=synapse.output.data_sample.block_height,
                )

                last_block_height = blochair_api.get_latest_block_height(
                    network=synapse.output.metadata.network
                )

                miner_block_height = synapse.output.block_height

                data_sample_is_valid = blochair_api.verify_data_sample(
                    network=synapse.output.metadata.network,
                    input_result=synapse.output.data_sample,
                )

                is_block_heights_random = MinerDataSample().is_block_heights_random(
                    synapse.dendrite.hotkey,
                    synapse.output.metadata.network,
                    synapse.output.metadata.model_type,
                )

                bt.logging.info(f"Last block height: {last_block_height}")
                bt.logging.info(f"Miner block height: {miner_block_height}")
                bt.logging.info(f"Data sample is valid: {data_sample_is_valid}")
                bt.logging.info(f"Block heights are random: {is_block_heights_random}")

                score = 0

                if data_sample_is_valid and is_block_heights_random:
                    score = 1
                    proportion = MinerRegistry().get_miner_proportion(
                        synapse.output.metadata.network,
                        synapse.output.metadata.model_type,
                    )

                    bt.logging.info(f"Miner proportion: {proportion}")

                    score *= proportion

                    block_height_diff = abs(last_block_height - miner_block_height)
                    bt.logging.info(f"Block height diff: {block_height_diff}")

                    if block_height_diff == 100:
                        score *= 0.5

                scores[index] = (
                    config.alpha * scores[index] + (1 - config.alpha) * score
                )

            bt.logging.info(f"Scoring response: {scores}")

            if (step + 1) % 10 == 0:
                weights = torch.nn.functional.normalize(scores, p=1.0, dim=0)
                bt.logging.info(f"Setting weights: {weights}")
                result = subtensor.set_weights(
                    netuid=config.netuid,  # Subnet to set weights on.
                    wallet=wallet,  # Wallet to sign set weights using hotkey.
                    uids=metagraph.uids,  # Uids of the miners to set weights for.
                    weights=weights,  # Weights to set for the miners.
                    wait_for_inclusion=True,
                )
                if result:
                    bt.logging.success("Successfully set weights.")
                else:
                    bt.logging.error("Failed to set weights.")

            step += 1
            metagraph = subtensor.metagraph(config.netuid)
            time.sleep(bt.__blocktime__)

        except RuntimeError as e:
            bt.logging.error(e)
            traceback.print_exc()

        except KeyboardInterrupt:
            bt.logging.success("Keyboard interrupt detected. Exiting validator.")
            exit()


if __name__ == "__main__":
    config = get_config()
    main(config)
