#!/bin/bash
cd "$(dirname "$0")/../"
export PYTHONPATH=$PWD

if [ "$NEW" = "true" ]; then
    python3 neurons/nodes/bitcoin/btc-vout-hashtable-builder/indexer.py --csvfile "$CSV_FILE" --targetpath "$TARGET_PATH" --new
else
    python3 neurons/nodes/bitcoin/btc-vout-hashtable-builder/indexer.py --csvfile "$CSV_FILE" --targetpath "$TARGET_PATH"
fi

