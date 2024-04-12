#!/bin/bash

i=0
for tuple in "$@"; do
    IFS=':' read -r name version <<< "$tuple"
    echo "Processing tuple: VERSION=$version, NAME=$name, IMAGE=$name:$version"

    if [ -d ./venv/ ]; then
        python -m venv venv
    fi

    if [ -d ~/.bittensor/wallets/$name:$version/ ]; then
        echo "Wallet directory already exists. Skipping creation."
    else
        echo "Creating wallet for $name:$version.."
        source venv/bin/activate
        pip install bittensor
        if [ "$name" == "miner" ]; then
            for ((j=1; j<=3; j++)); do
                btcli w create --wallet.name $name:$version$j --hotkey default --no_password --no_prompt
            done
        elif [ "$name" == "validator" ]; then
            for ((j=1; j<=2; j++)); do
                btcli w create --wallet.name $name:$version$j --hotkey default --no_password --no_prompt
            done
        fi
    fi

    echo "Building and running $name:$version.."

    docker build -t "$name:$version" \
        --build-arg BITTENSOR_VERSION=$version \
        --build-arg NODE_TYPE=$name \
        --build-arg WALLET_NAME=$name:$version \
        --build-arg WALLET_HOTKEY=default \
        --build-arg NETUID=1 \
        --build-arg AXON_PORT=6001 \
        --build-arg AXON_EXTERNAL_PORT=600$i \
        --build-arg SUBTENSOR_NETWORK=test \
        -f ./node.Dockerfile \
        .
    
    docker run -d -p 6001:600$i \
        --name "$name-$version" \
        --mount type=bind,source=$HOME/.bittensor/wallets/,target=/root/.bittensor/wallets/ \
        "$name:$version" 
done


# create owner wallet to fund all miners and validators
btcli w create --wallet.name owner --hotkey default --no_password --no_prompt

# create chain container
docker build -t chain \
    --build-arg BT_DEFAULT_TOKEN_WALLET=owner \
    -f chain.Dockerfile \
    .

docker run -d \
    --name chain \
    -v $HOME/.bittensor/wallets/:/root/.bittensor/wallets/ \
    chain