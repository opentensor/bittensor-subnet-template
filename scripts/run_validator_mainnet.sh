#!/bin/bash
cd "$(dirname "$0")/../"
export PYTHONPATH=$PWD
python3 neurons/validators/validator.py --wallet.name "$WALLET_NAME" --wallet.hotkey "$WALLET_HOTKEY" --netuid "$NETUID" --subtensor.network "$SUBTENSOR_NETWORK" --subtensor.chain_endpoint "$SUBTENSOR_URL" --enable_api "$ENABLE_API" --logging.trace
