#!/bin/bash

# Change directory to the script's grandparent directory
cd "$(dirname "$0")/../"

# Print the current working directory
echo "$PWD"

# Set PYTHONPATH to the current working directory
export PYTHONPATH=$PWD

# Check if WALLET_NAME is unset or empty, and set default if necessary
if [ -z "$WALLET_NAME" ]; then
    export WALLET_NAME=miner
fi

# Check if WALLET_HOTKEY is unset or empty, and set default if necessary
if [ -z "$WALLET_HOTKEY" ]; then
    export WALLET_HOTKEY=default
fi

# Activate the Python virtual environment (path adjusted for Ubuntu)
source venv/bin/activate

# Execute Python script with quoted variables for safety
python3 neurons/miners/miner.py --network bitcoin --model_type funds_flow --wallet.name "$WALLET_NAME" --hotkey "$WALLET_HOTKEY" --netuid 15 --subtensor.network finney

# Deactivate the Python virtual environment
source venv/bin/deactivate
