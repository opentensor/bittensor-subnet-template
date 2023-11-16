#!/bin/bash

# Change directory to the script's grandparent directory
cd "$(dirname "$0")/../"

# Print the current working directory
echo "$PWD"

# Set PYTHONPATH to the current working directory
export PYTHONPATH=$PWD

# Check if NETUID is unset or empty, and set default if necessary
if [ -z "$NETUID" ]; then
    export NETUID=1
fi

# Check if WALLET_HOTKEY is unset or empty, and set default if necessary
if [ -z "$BLOCKCHAIN_API_KEY" ]; then
    export BLOCKCHAIN_API_KEY=A___mw5wNljHQ4n0UAdM5Ivotp0Bsi93
fi

# Check if WALLET_NAME is unset or empty, and set default if necessary
if [ -z "$WALLET_NAME" ]; then
    export WALLET_NAME=validator
fi

# Check if WALLET_HOTKEY is unset or empty, and set default if necessary
if [ -z "$WALLET_HOTKEY" ]; then
    export WALLET_HOTKEY=default
fi

# Activate the Python virtual environment (path adjusted for Ubuntu)
source venv/bin/activate

# Execute Python script with quoted variables for safety
python3 neurons/validators/validator.py --blockchair_api_key "$BLOCKCHAIN_API_KEY" --wallet.name "$WALLET_NAME" --hotkey "$WALLET_HOTKEY" --netuid "$NETUID" --subtensor.network finney --subtensor.chain_endpoint ws://127.0.0.1:9946

# Deactivate the Python virtual environment
source venv/bin/deactivate
