#!/bin/bash
cd "$(dirname "$0")/../"
echo "$PWD"

export PYTHONPATH=$PWD

if [ -z "$WALLET_NAME" ]; then
    export WALLET_NAME=miner
fi

if [ -z "$WALLET_HOTKEY" ]; then
    export WALLET_HOTKEY=default
fi

python3 neurons/miners/ip_blocker.py --wallet.name "$WALLET_NAME" --wallet.hotkey "$WALLET_HOTKEY" --netuid 15 --logging.debug --logging.trace