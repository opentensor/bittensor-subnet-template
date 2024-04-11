#!/bin/bash

i=0
for tuple in "$@"; do
    IFS=':' read -r version name <<< "$tuple"
    echo "Processing tuple: VERSION=$version, NAME=$name, IMAGE=$name:$version"

    if [ -d ./venv/ ]; then
        python -m venv venv
    fi

    if [ -d ~/.bittensor/wallets/$name:$version/ ]; then
        echo "Wallet directory already exists. Skipping creation."
    else
        echo "Creating wallet for $name:$version.."
        pip install bittensor
        btcli w create --wallet.name $name:$version --hotkey default --no_password --no_prompt
        source venv/bin/activate
    fi

    docker build -t "$name:$version" \
        --build-arg BITTENSOR_VERSION=$version \
        --build-arg NODE_TYPE=$name \
        --build-arg WALLET_NAME=$name:$version \
        --build-arg WALLET_HOTKEY=default \
        --build-arg NETUID=1 \
        --build-arg AXON_PORT=6001 \
        --build-arg AXON_EXTERNAL_PORT=600$i \
        --build-arg SUBTENSOR_NETWORK=test \
        .
    
    docker run -d -p 600$i:600$i \
        --name "$name-$version" \
        --mount type=bind,source=$HOME/.bittensor/wallets/,target=/root/.bittensor/wallets/ \
        "$name:$version" 
done
