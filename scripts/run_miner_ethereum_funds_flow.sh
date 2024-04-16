#!/bin/bash
cd "$(dirname "$0")/../"
export PYTHONPATH=$PWD
python3 neurons/miners/miner.py --network ethereum --wallet.name "$WALLET_NAME" --wallet.hotkey "$WALLET_HOTKEY" --netuid 15 --subtensor.network "$SUBTENSOR_NETWORK" --miner_set_weights "$MINER_SET_WEIGHTS" --subtensor.chain_endpoint "$SUBTENSOR_URL" --logging.trace