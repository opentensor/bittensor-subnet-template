#!/bin/bash

i=0
for tuple in "$@"; do
    IFS=':' read -r version name <<< "$tuple"
    echo "Processing tuple: VERSION=$version, NAME=$name, IMAGE=$name:$version"
    docker build -t "$name:$version" \
        --build-arg BITTENSOR_VERSION=$version \
        --build-arg NODE_TYPE=$name \
        --build-arg WALLET_NAME=default \
        --build-arg WALLET_HOTKEY=default \
        --build-arg NETUID=1 \
        --build-arg AXON_PORT=6001 \
        --build-arg AXON_EXTERNAL_PORT=600$i \
        --build-arg SUBTENSOR_NETWORK=test \
        .
    
    docker run -d -p 600$i:600$i --name "$name-$version" "$name:$version" 
done
