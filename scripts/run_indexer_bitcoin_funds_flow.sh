#!/bin/bash
cd "$(dirname "$0")/../"
export PYTHONPATH=$(pwd)
python3 neurons/miners/bitcoin/funds_flow/indexer.py