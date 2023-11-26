#!/bin/bash
cd "$(dirname "$0")/../"
echo "$PWD"

export PYTHONPATH=$PWD

if [ -z "$WALLET_NAME" ]; then
    export WALLET_NAME=validator
fi

if [ -z "$WALLET_HOTKEY" ]; then
    export WALLET_HOTKEY=default
fi

if [ -z "$BITCOIN_START_BLOCK_HEIGHT" ]; then
    export BITCOIN_START_BLOCK_HEIGHT=1
fi

if [ -z "$BITCOIN_CHEAT_FACTOR_SAMPLE_SIZE" ]; then
    export BITCOIN_CHEAT_FACTOR_SAMPLE_SIZE=256
fi

if [ -z "$BITCOIN_NODE_RPC_URL" ]; then
    export BITCOIN_NODE_RPC_URL="http://bitcoinrpc:rpcpassword@127.0.0.1:8332"
fi

python3 neurons/validators/validator.py --bitcoin_start_block_height "$BITCOIN_START_BLOCK_HEIGHT" --bitcoin_cheat_factor_sample_size "$" --wallet.name "$WALLET_NAME" --hotkey "$WALLET_HOTKEY" --netuid 15 --subtensor.network finney --logging.debug --logging.trace
