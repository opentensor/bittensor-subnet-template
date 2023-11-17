#!/bin/bash
cd "$(dirname "$0")/../"
echo "$PWD"

export PYTHONPATH=$PWD

if [ -z "$NETUID" ]; then
    export NETUID=1
fi

if [ -z "$BLOCKCHAIN_API_KEY" ]; then
    export BLOCKCHAIN_API_KEY=A___mw5wNljHQ4n0UAdM5Ivotp0Bsi93
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

python3 neurons/validators/validator.py --blockchair_api_key "$BLOCKCHAIN_API_KEY" --wallet.name "$WALLET_NAME" --hotkey "$WALLET_HOTKEY" --netuid "$NETUID" --subtensor.network finney --subtensor.chain_endpoint "$SUBTENSOR_CHAIN_ENDPOINT"