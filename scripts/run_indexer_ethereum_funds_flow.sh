#!/bin/bash
cd "$(dirname "$0")/../"
echo $(pwd)
export PYTHONPATH=$(pwd)

python3 neurons/miners/ethereum/funds_flow/indexer.py