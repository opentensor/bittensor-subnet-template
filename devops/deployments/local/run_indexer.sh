#!/bin/bash
cd "$(dirname "$0")/../../../"
echo $(pwd)
export PYTHONPATH=$(pwd)
source venv/Scripts/activate
python3 neurons/miners/bitcoin/indexer.py