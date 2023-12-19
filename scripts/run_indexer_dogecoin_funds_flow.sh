#!/bin/bash
cd "$(dirname "$0")/../"
echo $(pwd)
export PYTHONPATH=$(pwd)

if [ -z "$DOGE_NODE_RPC_URL" ]; then
    export DOGE_NODE_RPC_URL="http://doge:doge@127.0.0.1:44555"
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

python3 neurons/miners/dogecoin/funds_flow/indexer.py