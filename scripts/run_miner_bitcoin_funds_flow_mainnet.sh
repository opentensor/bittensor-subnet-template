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

if [ -z "$GRAPH_DB_URL" ]; then
    export GRAPH_DB_URL="bolt://localhost:7687"
fi

if [ -z "$GRAPH_DB_USER" ]; then
    export GRAPH_DB_USER=""
fi

if [ -z "$GRAPH_DB_PASSWORD" ]; then
    export GRAPH_DB_PASSWORD=""
fi

if [ -z "$WAIT_FOR_SYNC" ]; then
    export WAIT_FOR_SYNC="True"
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

if [ -z "$MINER_SET_WEIGHTS" ]; then
    export MINER_SET_WEIGHTS="True"
fi


python3 neurons/miners/miner.py --network bitcoin --model_type funds_flow --wallet.name "$WALLET_NAME" --wallet.hotkey "$WALLET_HOTKEY" --netuid 15 --subtensor.network "$SUBTENSOR_NETWORK" --subtensor.chain_endpoint "$SUBTENSOR_URL" --logging.trace --miner_set_weights "$MINER_SET_WEIGHTS"