#!/bin/bash
cd "$(dirname "$0")/../"
echo "$PWD"

export PYTHONPATH=$PWD

if [ -z "$BLOCKCHAIN_API_KEY" ]; then
    export BLOCKCHAIN_API_KEY=A___mw5wNljHQ4n0UAdM5Ivotp0Bsi93
fi

if [ -z "$WALLET_NAME" ]; then
    export WALLET_NAME=validator
fi

if [ -z "$WALLET_HOTKEY" ]; then
    export WALLET_HOTKEY=default
fi

if [ -z "$BITCOIN_START_BLOCK_HEIGHT" ]; then
    export BITCOIN_START_BLOCK_HEIGHT=1
fi

python3 neurons/validators/validator.py --blockchair_api_key "$BLOCKCHAIN_API_KEY" --bitcoin_start_block_height "$BITCOIN_START_BLOCK_HEIGHT" --wallet.name "$WALLET_NAME" --hotkey "$WALLET_HOTKEY" --netuid 15 --subtensor.network finney
