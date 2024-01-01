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

if [ -z "$SUBTENSOR_URL" ]; then
    export SUBTENSOR_URL=ws://51.158.60.18:9944
fi

if [ -z "$SUBTENSOR_NETWORK" ]; then
    export SUBTENSOR_NETWORK=local
fi

python3 neurons/validators/validator.py --bitcoin_cheat_factor_sample_size "$BITCOIN_CHEAT_FACTOR_SAMPLE_SIZE" --wallet.name "$WALLET_NAME" --wallet.hotkey "$WALLET_HOTKEY" --netuid 15 --subtensor.network "$SUBTENSOR_NETWORK" --subtensor.chain_endpoint "$SUBTENSOR_URL" --logging.trace