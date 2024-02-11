#!/bin/bash
cd "$(dirname "$0")/../"
export PYTHONPATH=$PWD

if [ "$NEW" = "true" ]; then
    python3 neurons/nodes/bitcoin/btc-vout-hashtable-builder/indexer.py --csvfile "$CSV_FILE" --targetpath "$BITCOIN_TX_OUT_HASHMAP_PICKLES" --new
else
    python3 neurons/nodes/bitcoin/btc-vout-hashtable-builder/indexer.py --csvfile "$CSV_FILE" --targetpath "$BITCOIN_TX_OUT_HASHMAP_PICKLES"
fi

