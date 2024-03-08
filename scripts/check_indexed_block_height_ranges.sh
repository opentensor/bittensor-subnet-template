#!/bin/bash
cd "$(dirname "$0")/../"
export PYTHONPATH=$(pwd)
python3 neurons/miners/bitcoin/funds_flow/utils/find_indexed_block_height_ranges.py