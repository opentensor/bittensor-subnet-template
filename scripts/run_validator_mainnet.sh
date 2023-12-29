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

if [ -z "$BITCOIN_NODE_RPC_URL" ]; then
    export BITCOIN_NODE_RPC_URL="http://bitcoinrpc:rpcpassword@127.0.0.1:8332"
fi

python3 neurons/validators/validator.py --wallet.name "$WALLET_NAME" --wallet.hotkey "$WALLET_HOTKEY" --netuid 15 --subtensor.network finney --logging.debug --logging.trace
