#!/bin/bash
cd "$(dirname "$0")/../"
echo "$PWD"

export PYTHONPATH=$PWD

if [ -z "$NETUID" ]; then
    export NETUID=1
fi

if [ -z "$WALLET_NAME" ]; then
    export WALLET_NAME=validator
fi

if [ -z "$WALLET_HOTKEY" ]; then
    export WALLET_HOTKEY=default
fi

if [ -z "$SUBTENSOR_CHAIN_ENDPOINT" ]; then
    export SUBTENSOR_CHAIN_ENDPOINT="ws://127.0.0.1:9946"
fi

if [ -z "$BITCOIN_START_BLOCK_HEIGHT" ]; then
    export BITCOIN_START_BLOCK_HEIGHT=1
fi

if [ -z "$BITCOIN_NODE_RPC_URL" ]; then
    export BITCOIN_NODE_RPC_URL="http://bitcoinrpc:rpcpassword@127.0.0.1:8332"
fi

python3 neurons/validators/validator.py --bitcoin_start_block_height "$BITCOIN_START_BLOCK_HEIGHT" --wallet.name "$WALLET_NAME" --hotkey "$WALLET_HOTKEY" --netuid "$NETUID" --subtensor.network finney --subtensor.chain_endpoint "$SUBTENSOR_CHAIN_ENDPOINT" --logging.debug