#!/bin/bash
cd "$(dirname "$0")/../"
echo $(pwd)
export PYTHONPATH=$(pwd)

export NODE_RPC_URL="http://bitcoinrpc:rpcpassword@127.0.0.1:8332"

source venv/Scripts/activate
python3 neurons/miners/bitcoin/funds_flow/indexer.py