#!/bin/bash
cd "$(dirname "$0")/../"
export PYTHONPATH=$PWD
python3 neurons/miners/miner.py --network bitcoin --wallet.name "$WALLET_NAME" --wallet.hotkey "$WALLET_HOTKEY" --netuid "$NETUID" --subtensor.network "$SUBTENSOR_NETWORK" --miner_set_weights "$MINER_SET_WEIGHTS" --subtensor.chain_endpoint "$SUBTENSOR_URL" --llm_engine_url "$LLM_ENGINE_URL" --logging.trace