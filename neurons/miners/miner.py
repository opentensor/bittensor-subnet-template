# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2023 aphex5
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
import argparse
import traceback
import typing
import torch
import bittensor as bt
from random import sample
from insights import protocol
from neurons.miners import blacklists
from neurons.nodes.nodes import get_node
from neurons.miners.bitcoin.funds_flow.graph_indexer import GraphIndexer
from neurons.miners.query import (
    execute_query_proxy,
    get_graph_search, is_query_only,
)
from insights.protocol import (
    MODEL_TYPE_FUNDS_FLOW,
    NETWORK_BITCOIN,
    MinerDiscoveryMetadata,
)
from neurons.remote_config import MinerConfig
from neurons.miners.custom_miner_config import CustomMinerConfig


def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--network",
        default=NETWORK_BITCOIN,
        help="Set miner's supported blockchain network.",
    )
    parser.add_argument(
        "--model_type",
        type=str,
        default=MODEL_TYPE_FUNDS_FLOW,
        help="Set miner's supported model type.",
    )

    parser.add_argument("--netuid", type=int, default=15, help="The chain subnet uid.")

    bt.subtensor.add_args(parser)
    bt.logging.add_args(parser)
    bt.wallet.add_args(parser)
    bt.axon.add_args(parser)

    config = bt.config(parser)
    config.full_path = os.path.expanduser(
        "{}/{}/{}/netuid{}/{}".format(
            config.logging.logging_dir,
            config.wallet.name,
            config.wallet.hotkey,
            config.netuid,
            "miner",
        )
    )
    if not os.path.exists(config.full_path):
        os.makedirs(config.full_path, exist_ok=True)
    return config


def main(config):
    print("Current Working Directory:", os.getcwd())
    bt.logging(config=config, logging_dir=config.full_path)
    bt.logging.info(
        f"Running miner for subnet: {config.netuid} on network: {config.subtensor.chain_endpoint} with config:"
    )
    bt.logging.info("Setting up bittensor objects.")
    wallet = bt.wallet(config=config)
    bt.logging.info(f"Wallet: {wallet}")
    subtensor = bt.subtensor(config=config)
    bt.logging.info(f"Subtensor: {subtensor}")
    metagraph = subtensor.metagraph(config.netuid)
    bt.logging.info(f"Metagraph: {metagraph}")

    last_updated_block = subtensor.block - 100

    if wallet.hotkey.ss58_address not in metagraph.hotkeys:
        bt.logging.error(
            f"\nYour miner: {wallet} is not registered to chain connection: {subtensor} \nRun btcli register and try again. "
        )
        exit()

    """ Building dependencies. """
    miner_config = MinerConfig()
    config_miner_config = CustomMinerConfig()
    miner_config.load_and_get_config_values()
    blacklist_registry_manager = blacklists.BlacklistRegistryManager()
    _blacklist_discovery = blacklists.BlacklistDiscovery(miner_config, config_miner_config, blacklist_registry_manager)


    bt.logging.info(f"Waiting for graph model to sync with blockchain.")
    is_synced=False
    while not is_synced:
        wait_for_sync = os.getenv('WAIT_FOR_SYNC', 'True')
        if wait_for_sync == 'False':
            bt.logging.info(f"Skipping graph sync.")
            break

        try:
            graph_indexer = GraphIndexer(config.graph_db_url)
            if config.network == 'bitcoin':
                node = get_node(config.network)
                latest_block_height =  node.get_current_block_height()
                current_block_height = graph_indexer.get_latest_block_number()
                if latest_block_height - current_block_height < 100:
                    is_synced = True
                    bt.logging.info(f"Graph model is synced with blockchain.")
                else:
                    bt.logging.info(f"Graph Sync: {current_block_height}/{latest_block_height}")
                    time.sleep(bt.__blocktime__ * 12)
            else:
                raise Exception("Unsupported blockchain network")
        except Exception as e:
            bt.logging.error(traceback.format_exc())
            time.sleep(bt.__blocktime__ * 12)
            bt.logging.info(f"Failed to connect with graph database. Retrying...")
            continue

    my_subnet_uid = metagraph.hotkeys.index(wallet.hotkey.ss58_address)
    bt.logging.info(f"Running miner on uid: {my_subnet_uid}")

    def miner_discovery(synapse: protocol.MinerDiscovery) -> protocol.MinerDiscovery:
        try:
            graph_search = get_graph_search(config.network, config.model_type)

            block_range = graph_search.get_block_range()
            _latest_block_height = block_range['latest_block_height']
            start_block_height = block_range['start_block_height']

            block_heights = sample(range(start_block_height, _latest_block_height + 1), 10)
            data_samples = graph_search.get_block_transactions(block_heights)
            run_id = graph_search.get_run_id()

            synapse.output = protocol.MinerDiscoveryOutput(
                metadata=MinerDiscoveryMetadata(
                    network=config.network,
                    model_type=config.model_type,
                ),
                start_block_height=start_block_height,
                block_height=_latest_block_height,
                data_samples=data_samples,
                run_id=run_id
            )
            bt.logging.info(f"Serving miner discovery output: {synapse.output}")

            return synapse
        except Exception as e:
            bt.logging.error(traceback.format_exc())
            synapse.output = None
            return synapse

    def execute_query(synapse: protocol.MinerQuery) -> protocol.MinerQuery:
        try:
            synapse.output = execute_query_proxy(
                network=synapse.network,
                model_type=synapse.model_type,
                query=synapse.query,
            )
        except Exception as e:
            bt.logging.error(traceback.format_exc())
            synapse.output = None

        return synapse

    def priority_discovery(synapse: protocol.MinerDiscovery) -> float:
        caller_uid = metagraph.hotkeys.index(synapse.dendrite.hotkey)
        prirority = float(metagraph.S[caller_uid])
        bt.logging.trace(
            f"Prioritizing {synapse.dendrite.hotkey} with value: ", prirority
        )
        return prirority

    def blacklist_discovery(synapse: protocol.MinerDiscovery) -> typing.Tuple[bool, str]:
        return  _blacklist_discovery.blacklist_discovery(metagraph, synapse)

    def priority_execute_query(synapse: protocol.MinerQuery) -> float:
        caller_uid = metagraph.hotkeys.index(synapse.dendrite.hotkey)
        prirority = float(metagraph.S[caller_uid])
        bt.logging.trace(
            f"Prioritizing {synapse.dendrite.hotkey} with value: ", prirority
        )
        return prirority

    def blacklist_execute_query(synapse: protocol.MinerQuery) -> typing.Tuple[bool, str]:

        if synapse.dendrite.hotkey not in metagraph.hotkeys:
            bt.logging.trace(
                f"Blacklisting unrecognized hotkey {synapse.dendrite.hotkey}"
            )
            return True, "Unrecognized hotkey"

        if synapse.network != config.blockchain:
            bt.logging.trace(
                f"Blacklisting hot key {synapse.dendrite.hotkey} because of wrong blockchain"
            )
            return True, "Blockchain not supported."

        elif synapse.model_type != config.model_type:
            bt.logging.trace(
                f"Blacklisting hot key {synapse.dendrite.hotkey} because of wrong model type"
            )
            return True, "Model type not supported."

        elif not is_query_only(synapse.query):
            bt.logging.trace(
                f"Blacklisting hot key {synapse.dendrite.hotkey} because of illegal cypher keywords"
            )
            return True, "Illegal cypher keywords."

        else:
            return False, "All ok"

    axon = bt.axon(wallet=wallet, config=config)
    bt.logging.info(f"Attaching forward function to axon.")

    axon.attach(forward_fn=miner_discovery,  blacklist_fn=blacklist_discovery, priority_fn=priority_discovery).attach(
        forward_fn=execute_query, blacklist_fn=blacklist_execute_query, priority_fn=priority_execute_query)

    bt.logging.info(
        f"Serving axon {axon} on network: {config.subtensor.chain_endpoint} with netuid: {config.netuid}"
    )

    axon.serve(netuid=config.netuid, subtensor=subtensor)
    bt.logging.info(f"Starting axon server on port: {config.axon.port}")

    axon.start()
    # Keep the miner alive
    # This loop maintains the miner's operations until intentionally stopped.
    bt.logging.info(f"Starting main loop")
    step = 0
    while True:
        try:
            if subtensor.block - last_updated_block >= 100:
                bt.logging.trace(f"Setting miner weight")
                # find the uid that matches config.wallet.hotkey [meta.axons[N].hotkey == config.wallet.hotkey]
                # set the weight of that uid to 1.0
                uid = None
                try:
                    for _uid, axon in enumerate(metagraph.axons):
                        if axon.hotkey == wallet.hotkey.ss58_address:
                            # uid = axon.uid
                            # uid doesnt exist ona xon
                            uid = _uid
                            break
                    if uid is not None:
                        # 0 weights for all uids
                        weights = torch.Tensor([0.0] * len(metagraph.uids))
                        # 1 weight for uid
                        weights[uid] = 1.0
                        (uids, processed_weights) = bt.utils.weight_utils.process_weights_for_netuid( uids = metagraph.uids, weights = weights, netuid=config.netuid, subtensor = subtensor)
                        subtensor.set_weights(wallet = wallet, netuid = config.netuid, weights = processed_weights, uids = uids)
                        last_updated_block = subtensor.block
                        bt.logging.trace("🔄 Miner weight set!")
                    else:
                        bt.logging.warning(f"Could not find uid with hotkey {config.wallet.hotkey} to set weight")
                except Exception as e:
                    bt.logging.warning(f"Could not set miner weight: {e}")
                    raise e
            # Below: Periodically update our knowledge of the network graph.
            if step % 60 == 0:
                metagraph = subtensor.metagraph(config.netuid)
                log =  (f'Step:{step} | ' \
                        f'Block:{metagraph.block.item()} | ' \
                        f'Stake:{metagraph.S[my_subnet_uid]} | ' \
                        f'Rank:{metagraph.R[my_subnet_uid]} | ' \
                        f'Trust:{metagraph.T[my_subnet_uid]} | ' \
                        f'Consensus:{metagraph.C[my_subnet_uid] } | ' \
                        f'Incentive:{metagraph.I[my_subnet_uid]} | ' \
                        f'Emission:{metagraph.E[my_subnet_uid]}')
                bt.logging.info(log)
            step += 1
            time.sleep(1)

        except KeyboardInterrupt:
            axon.stop()
            bt.logging.success("Miner killed by keyboard interrupt.")
            break
        except Exception as e:
            bt.logging.error(traceback.format_exc())
            continue


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    config = get_config()

    # Check for an environment variable to enable local development
    if os.getenv("MINER_LOCAL_MODE") == "True":
        # Local development settings
        config.subtensor.chain_endpoint = "ws://127.0.0.1:9946"
        config.subtensor.network = "local"
        config.wallet.hotkey = 'default'
        config.wallet.name = 'miner'
        config.netuid = 1

        # set environment variables
        os.environ['WAIT_FOR_SYNC'] = 'False'
        os.environ['GRAPH_DB_URL'] = 'bolt://localhost:7687'
        os.environ['GRAPH_DB_USER'] = 'user'
        os.environ['GRAPH_DB_PASSWORD'] = 'pwd'

    main(config)
