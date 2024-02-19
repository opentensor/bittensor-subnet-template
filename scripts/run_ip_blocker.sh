#!/bin/bash
cd "$(dirname "$0")/../"
export PYTHONPATH=$PWD
python3 neurons/miners/ip_blocker.py --wallet.name "$WALLET_NAME" --wallet.hotkey "$WALLET_HOTKEY" --netuid 15 --logging.debug --logging.trace