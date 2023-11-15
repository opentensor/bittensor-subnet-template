#!/bin/bash
cd "$(dirname "$0")/../"
echo $(pwd)
export PYTHONPATH=$(pwd)

if [ -z "$NODE_RPC_URL" ]; then
    export NODE_RPC_URL="http://bitcoinrpc:rpcpassword@127.0.0.1:8332"
fi

source venv/Scripts/activate
python3 neurons/miners/bitcoin/funds_flow/indexer.py
source venv/Scripts/deactivate