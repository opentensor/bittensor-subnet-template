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
from insights.protocol import MinerDiscoveryOutput
from neurons.external_api.blockchair_api import BlockchairAPIError
from neurons.validators.discovery import BlockVerification
from neurons.validators.miner_registry import MinerRegistryManager


def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--alpha", default=0.9, type=float, help="The weight moving average scoring."
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

    while True:
        try:
            block_verification = BlockVerification(config.blockchair_api_key)
            verification_data = block_verification.get_verification_data()

            responses = dendrite.query(
                metagraph.axons,
                protocol.MinerDiscovery(random_block_height=verification_data),
                deserialize=True,
            )

            if responses is None or responses == [None, None]:
                bt.logging.info(f"No valid responses received. {bt.__blocktime__} seconds until next query.")
                time.sleep(bt.__blocktime__)
                continue

            bt.logging.info(f"Received responses: {responses}")
            for index, response in enumerate(responses):
                if response is None:
                    continue

                output: MinerDiscoveryOutput = response
                network = output.metadata.network
                model_type = output.metadata.model_type
                data_sample_block_height = output.block_height
                data_sample = output.data_sample
                axon_ip = metagraph.axons[index].ip
                hot_key = metagraph.axons[index].hotkey

                MinerRegistryManager().store_miner_metadata(
                    ip_address=axon_ip,
                    hot_key=hot_key,
                    network=network,
                    model_type=model_type,
                )

                last_block_height = verification_data[network]['last_block_height']
                data_sample_is_valid = block_verification.verify_data_sample(
                    network=network,
                    block_height=data_sample_block_height,
                    input_result=data_sample,
                )

                bt.logging.info(f"Last block height: {last_block_height}")
                bt.logging.info(f"Data sample block height: {data_sample_block_height}")
                bt.logging.info(f"Data sample is valid: {data_sample_is_valid}")

                score = 0
                if data_sample_is_valid:
                    score = 1
                    proportion = MinerRegistryManager().get_miner_proportion(
                        network,
                        model_type,
                    )

                    bt.logging.info(f"Miner proportion: {proportion}")

                    score *= proportion

                    block_height_diff = abs(last_block_height - data_sample_block_height)
                    bt.logging.info(f"Block height diff: {block_height_diff}")

                    if block_height_diff == 100:
                        score *= 0.1

                scores[index] = (
                    config.alpha * scores[index] + (1 - config.alpha) * score
                )

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
    """

    main(config)
