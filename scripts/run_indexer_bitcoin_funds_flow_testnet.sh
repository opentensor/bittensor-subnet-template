#!/bin/bash
cd "$(dirname "$0")/../"
echo $(pwd)
export PYTHONPATH=$(pwd)

if [ -z "$NODE_RPC_URL" ]; then
    export NODE_RPC_URL="http://bitcoinrpc:rpcpassword@127.0.0.1:18332"
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

source venv/Scripts/activate
python3 neurons/miners/bitcoin/funds_flow/indexer.py
source venv/Scripts/deactivate